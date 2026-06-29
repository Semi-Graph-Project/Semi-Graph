from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


DEFAULT_QUERY_FILE = ROOT / "data" / "evaluate" / "phase_t_multihop_queries.yaml"
DEFAULT_OUTPUT_DIR = ROOT / "analytics"
TOOL_CHOICES = ("vector", "graph", "hybrid")


def _get_config():
    from semigraph.config import get_config

    return get_config()


def _get_corpus_chunk_count(cfg) -> int:
    from semigraph.connections import get_neo4j_driver

    driver = get_neo4j_driver(cfg)
    try:
        with driver.session() as session:
            row = session.run("MATCH (c:Chunk) RETURN count(c) AS n").single()
            return int(row["n"] or 0) if row else 0
    finally:
        driver.close()


def _get_tool(tool_name: str, use_graph_expansion: bool = True):
    if tool_name == "vector":
        from semigraph.online.vector_search import vector_search

        return vector_search
    if tool_name == "graph":
        from semigraph.online.graph_search import graph_search

        def _graph(query: str, top_k_chunks: int, cfg):
            return graph_search(
                query,
                top_k_chunks=top_k_chunks,
                use_expansion=use_graph_expansion,
                cfg=cfg,
            )

        return _graph
    if tool_name == "hybrid":
        from semigraph.online.hybrid_search import hybrid_search

        def _hybrid(query: str, top_k_chunks: int, cfg):
            return hybrid_search(
                query,
                top_k_chunks=top_k_chunks,
                graph_use_expansion=use_graph_expansion,
                cfg=cfg,
            )

        return _hybrid
    raise ValueError(f"Unknown retrieval tool: {tool_name}")


def _load_queries(path: Path) -> list[dict]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    queries = data.get("queries", []) if isinstance(data, dict) else []
    if not isinstance(queries, list):
        raise ValueError(f"{path} must contain a top-level 'queries' list")
    return queries


def _chunk_ids(chunks: list[dict], k: int) -> list[str]:
    return [
        str(chunk.get("chunk_id", ""))
        for chunk in chunks[:k]
        if chunk.get("chunk_id")
    ]


def _score_result(returned_ids: list[str], gold_ids: list[str]) -> dict:
    if not gold_ids:
        return {
            "scored": False,
            "hit": None,
            "recall": None,
            "mrr": None,
            "hits": [],
        }

    gold = set(gold_ids)
    hits = [cid for cid in returned_ids if cid in gold]
    first_hit_rank = next(
        (idx for idx, cid in enumerate(returned_ids, start=1) if cid in gold),
        None,
    )
    return {
        "scored": True,
        "hit": 1 if hits else 0,
        "recall": len(set(hits)) / len(gold),
        "mrr": 1 / first_hit_rank if first_hit_rank else 0.0,
        "hits": hits,
    }


def _random_hit_probability(corpus_size: int, gold_count: int, k: int) -> float | None:
    """Probability that random top-k retrieval hits at least one gold chunk.

    This is the benchmark's "chance baseline": if we randomly sampled `k`
    chunks without replacement from the whole corpus, how often would at least
    one of them be a gold chunk?
    """
    if corpus_size <= 0 or gold_count <= 0 or k <= 0:
        return None

    k = min(k, corpus_size)
    gold_count = min(gold_count, corpus_size)
    non_gold_count = corpus_size - gold_count
    if non_gold_count <= 0:
        return 1.0

    no_hit = 1.0
    for i in range(k):
        denominator = corpus_size - i
        if denominator <= 0:
            break
        no_hit *= max(non_gold_count - i, 0) / denominator
    return 1.0 - no_hit


def _unscored_result() -> dict:
    return {
        "scored": False,
        "hit": None,
        "recall": None,
        "mrr": None,
        "hits": [],
    }


def _run_tool(
    tool_name: str,
    query: str,
    top_k: int,
    cfg,
    use_graph_expansion: bool,
) -> tuple[list[dict], str | None, float]:
    started = time.time()
    try:
        chunks = _get_tool(tool_name, use_graph_expansion=use_graph_expansion)(
            query,
            top_k_chunks=top_k,
            cfg=cfg,
        )
        return chunks, None, time.time() - started
    except Exception as exc:
        return [], f"{type(exc).__name__}: {exc}", time.time() - started


def _evaluate_query(
    item: dict,
    tools: list[str],
    top_k: int,
    oracle_k: int,
    cfg,
    dry_run: bool,
    use_graph_expansion: bool,
    corpus_size: int,
) -> dict:
    query = str(item.get("query", "")).strip()
    gold_chunks = [str(cid) for cid in item.get("gold_chunks", []) if cid]
    result = {
        "id": item.get("id", ""),
        "query": query,
        "type": item.get("type", ""),
        "gold_tools": item.get("gold_tools", []),
        "gold_chunks": gold_chunks,
        "answer_points": item.get("answer_points", []),
        "tools": {},
    }
    chance_hit_at_k = _random_hit_probability(
        corpus_size=corpus_size,
        gold_count=len(gold_chunks),
        k=top_k,
    )
    chance_hit_at_oracle = _random_hit_probability(
        corpus_size=corpus_size,
        gold_count=len(gold_chunks),
        k=oracle_k,
    )

    for tool_name in tools:
        if dry_run:
            chunks, error, latency = [], None, 0.0
        else:
            chunks, error, latency = _run_tool(
                tool_name=tool_name,
                query=query,
                top_k=max(top_k, oracle_k),
                cfg=cfg,
                use_graph_expansion=use_graph_expansion,
            )

        returned_at_k = _chunk_ids(chunks, top_k)
        returned_at_oracle = _chunk_ids(chunks, oracle_k)
        if dry_run:
            score_at_k = _unscored_result()
            score_at_oracle = _unscored_result()
        else:
            score_at_k = _score_result(returned_at_k, gold_chunks)
            score_at_oracle = _score_result(returned_at_oracle, gold_chunks)
        result["tools"][tool_name] = {
            "latency_sec": round(latency, 3),
            "error": error,
            "returned_chunk_ids": returned_at_k,
            "oracle_chunk_ids": returned_at_oracle,
            "hit_at_k": score_at_k["hit"],
            "recall_at_k": score_at_k["recall"],
            "mrr_at_k": score_at_k["mrr"],
            "hits_at_k": score_at_k["hits"],
            "chance_hit_at_k": chance_hit_at_k if score_at_k["scored"] else None,
            "oracle_hit": score_at_oracle["hit"],
            "oracle_recall": score_at_oracle["recall"],
            "oracle_hits": score_at_oracle["hits"],
            "chance_oracle_hit": chance_hit_at_oracle if score_at_oracle["scored"] else None,
        }

    return result


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _aggregate(results: list[dict], tools: list[str]) -> dict:
    aggregate: dict[str, dict] = {}
    by_type: dict[str, dict[str, dict[str, list[float]]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(list))
    )

    for tool_name in tools:
        hits: list[float] = []
        recalls: list[float] = []
        mrrs: list[float] = []
        oracle_hits: list[float] = []
        chance_hits: list[float] = []
        scored_count = 0
        errors = 0

        for row in results:
            metrics = row["tools"][tool_name]
            if metrics["error"]:
                errors += 1
            if metrics["hit_at_k"] is None:
                continue

            scored_count += 1
            hits.append(float(metrics["hit_at_k"]))
            recalls.append(float(metrics["recall_at_k"]))
            mrrs.append(float(metrics["mrr_at_k"]))
            oracle_hits.append(float(metrics["oracle_hit"]))
            if metrics["chance_hit_at_k"] is not None:
                chance_hits.append(float(metrics["chance_hit_at_k"]))

            qtype = row.get("type") or "unknown"
            by_type[qtype][tool_name]["hit"].append(float(metrics["hit_at_k"]))
            by_type[qtype][tool_name]["recall"].append(float(metrics["recall_at_k"]))
            by_type[qtype][tool_name]["mrr"].append(float(metrics["mrr_at_k"]))

        random_baseline = _mean(chance_hits)
        hit_rate = _mean(hits)
        aggregate[tool_name] = {
            "scored_queries": scored_count,
            "errors": errors,
            "hit_rate": hit_rate,
            "avg_recall": _mean(recalls),
            "avg_mrr": _mean(mrrs),
            "oracle_hit_rate": _mean(oracle_hits),
            "random_hit_baseline": random_baseline,
            "hit_minus_random": hit_rate - random_baseline,
            "hit_lift_vs_random": (hit_rate / random_baseline) if random_baseline else None,
        }

    type_rows: list[dict] = []
    for qtype in sorted(by_type):
        row = {"type": qtype}
        for tool_name in tools:
            row[f"{tool_name}_hit"] = _mean(by_type[qtype][tool_name]["hit"])
            row[f"{tool_name}_recall"] = _mean(by_type[qtype][tool_name]["recall"])
            row[f"{tool_name}_mrr"] = _mean(by_type[qtype][tool_name]["mrr"])
        type_rows.append(row)

    return {"overall": aggregate, "by_type": type_rows}


def _fmt(value) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def _write_markdown(
    path: Path,
    query_file: Path,
    results: list[dict],
    aggregate: dict,
    tools: list[str],
    top_k: int,
    oracle_k: int,
    dry_run: bool,
    corpus_size: int,
) -> None:
    lines: list[str] = []
    lines.append("# Phase T Retrieval Baseline")
    lines.append("")
    lines.append(f"Generated: {datetime.now().isoformat(timespec='seconds')}")
    lines.append(f"Query file: `{query_file}`")
    lines.append(f"Tools: `{', '.join(tools)}`")
    lines.append(f"top_k: `{top_k}`")
    lines.append(f"oracle_k: `{oracle_k}`")
    lines.append(f"dry_run: `{dry_run}`")
    lines.append(f"corpus_chunks: `{corpus_size}`")
    lines.append("")

    lines.append("## Overall")
    lines.append("")
    lines.append("| Tool | Scored Queries | Errors | Hit@k | Random Hit@k | Hit Lift | Hit-Random | Recall@k | MRR@k | Oracle Hit |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for tool_name in tools:
        row = aggregate["overall"][tool_name]
        lines.append(
            "| "
            f"{tool_name} | {row['scored_queries']} | {row['errors']} | "
            f"{row['hit_rate']:.3f} | "
            f"{_fmt(row['random_hit_baseline'])} | "
            f"{_fmt(row['hit_lift_vs_random'])} | "
            f"{_fmt(row['hit_minus_random'])} | "
            f"{row['avg_recall']:.3f} | "
            f"{row['avg_mrr']:.3f} | {row['oracle_hit_rate']:.3f} |"
        )

    if aggregate["by_type"]:
        lines.append("")
        lines.append("## By Type")
        lines.append("")
        header = ["Type"]
        for tool_name in tools:
            header.extend([f"{tool_name} Hit", f"{tool_name} Recall"])
        lines.append("| " + " | ".join(header) + " |")
        lines.append("|" + "|".join(["---"] + ["---:"] * (len(header) - 1)) + "|")
        for row in aggregate["by_type"]:
            cells = [row["type"]]
            for tool_name in tools:
                cells.append(_fmt(row.get(f"{tool_name}_hit")))
                cells.append(_fmt(row.get(f"{tool_name}_recall")))
            lines.append("| " + " | ".join(cells) + " |")

    lines.append("")
    lines.append("## Per Query")
    for row in results:
        lines.append("")
        lines.append(f"### {row['id']}: `{row['query']}`")
        lines.append("")
        lines.append(f"- type: `{row['type']}`")
        lines.append(f"- gold_tools: `{row['gold_tools']}`")
        lines.append(f"- gold_chunks: `{row['gold_chunks']}`")
        lines.append("")
        lines.append("| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |")
        lines.append("|---|---|---:|---:|---:|---:|---:|---:|---|---|")
        for tool_name in tools:
            metrics = row["tools"][tool_name]
            lines.append(
                "| "
                f"{tool_name} | "
                f"{metrics['error'] or ''} | "
                f"{metrics['latency_sec']:.3f} | "
                f"{_fmt(metrics['hit_at_k'])} | "
                f"{_fmt(metrics['chance_hit_at_k'])} | "
                f"{_fmt(metrics['recall_at_k'])} | "
                f"{_fmt(metrics['mrr_at_k'])} | "
                f"{_fmt(metrics['oracle_hit'])} | "
                f"`{metrics['hits_at_k']}` | "
                f"`{metrics['returned_chunk_ids']}` |"
            )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, results: list[dict]) -> None:
    payload = "\n".join(
        json.dumps(row, ensure_ascii=False, default=str)
        for row in results
    )
    path.write_text(payload + ("\n" if payload else ""), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate Phase T retrieval quality for vector, graph, and hybrid tools."
    )
    parser.add_argument("--queries", type=Path, default=DEFAULT_QUERY_FILE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--tools",
        nargs="+",
        choices=TOOL_CHOICES,
        default=["vector", "graph", "hybrid"],
    )
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--oracle-k", type=int, default=10)
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of queries for smoke runs.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Load queries and write reports without calling retrievers.",
    )
    parser.add_argument(
        "--no-llm-expansion",
        action="store_true",
        help="Disable graph query expansion for graph/hybrid diagnostic runs.",
    )
    args = parser.parse_args()

    queries = _load_queries(args.queries)
    if args.limit is not None:
        queries = queries[: args.limit]

    args.output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    md_path = args.output_dir / f"phase_t_retrieval_baseline_{stamp}.md"
    jsonl_path = args.output_dir / f"phase_t_retrieval_details_{stamp}.jsonl"

    cfg = None if args.dry_run else _get_config()
    corpus_size = 0 if args.dry_run else _get_corpus_chunk_count(cfg)
    results = [
        _evaluate_query(
            item=item,
            tools=args.tools,
            top_k=args.top_k,
            oracle_k=args.oracle_k,
            cfg=cfg,
            dry_run=args.dry_run,
            use_graph_expansion=not args.no_llm_expansion,
            corpus_size=corpus_size,
        )
        for item in queries
    ]
    aggregate = _aggregate(results, args.tools)

    _write_markdown(
        path=md_path,
        query_file=args.queries,
        results=results,
        aggregate=aggregate,
        tools=args.tools,
        top_k=args.top_k,
        oracle_k=args.oracle_k,
        dry_run=args.dry_run,
        corpus_size=corpus_size,
    )
    _write_jsonl(jsonl_path, results)

    print(f"Wrote report: {md_path}")
    print(f"Wrote details: {jsonl_path}")
    for tool_name in args.tools:
        row = aggregate["overall"][tool_name]
        print(
            f"{tool_name}: scored={row['scored_queries']} "
            f"errors={row['errors']} hit={row['hit_rate']:.3f} "
            f"random={row['random_hit_baseline']:.3f} "
            f"lift={_fmt(row['hit_lift_vs_random'])} "
            f"recall={row['avg_recall']:.3f} mrr={row['avg_mrr']:.3f}"
        )


if __name__ == "__main__":
    main()
