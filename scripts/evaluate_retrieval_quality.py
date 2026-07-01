from __future__ import annotations

import argparse
import json
import random
import sys
import time
from collections import Counter, defaultdict
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
SEED_MODE_CHOICES = ("triple", "node", "hybrid")
DEFAULT_REEXTRACT_TICKERS = ("AMD", "NVDA", "AVGO", "RMBS")


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


def _get_existing_entities(cfg, names: list[str]) -> set[str]:
    from semigraph.connections import get_neo4j_driver

    unique_names = sorted({name for name in names if name})
    if not unique_names:
        return set()

    driver = get_neo4j_driver(cfg)
    try:
        with driver.session() as session:
            rows = list(session.run(
                """
                UNWIND $names AS name
                MATCH (e:Entity {name: name})
                RETURN DISTINCT e.name AS name
                """,
                names=unique_names,
            ))
            return {str(row["name"]) for row in rows}
    finally:
        driver.close()


def _get_tool(
    tool_name: str,
    use_graph_expansion: bool = True,
    graph_seed_mode: str = "triple",
):
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
                seed_mode=graph_seed_mode,
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
                graph_seed_mode=graph_seed_mode,
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


def _normalize_entity(name: str) -> str:
    return " ".join(str(name).strip().lower().split())


def _gold_entities(item: dict) -> list[str]:
    return [
        _normalize_entity(name)
        for name in item.get("gold_entities", [])
        if _normalize_entity(name)
    ]


def _gold_chunk_tickers(item: dict) -> set[str]:
    tickers: set[str] = set()
    for chunk_id in item.get("gold_chunks", []) or []:
        prefix = str(chunk_id).split("_", 1)[0].upper()
        if prefix:
            tickers.add(prefix)
    return tickers


def _mentioned_tickers(item: dict, known_tickers: set[str]) -> set[str]:
    haystack = " ".join(
        [
            str(item.get("query", "")),
            " ".join(str(e) for e in item.get("gold_entities", []) or []),
        ]
    ).upper()
    terms = set(haystack.replace("-", " ").replace("/", " ").split())
    return {ticker for ticker in known_tickers if ticker in terms}


def _classify_subset(
    item: dict,
    reextract_tickers: set[str],
    known_tickers: set[str],
) -> str:
    involved = _gold_chunk_tickers(item) | _mentioned_tickers(item, known_tickers)
    if involved & reextract_tickers:
        if involved - reextract_tickers:
            return "mixed_subset"
        return "reextract_subset"
    return "legacy_subset"


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


def _hit_from_names(names: set[str], gold_entities: list[str]) -> int | None:
    if not gold_entities:
        return None
    return 1 if names & set(gold_entities) else 0


def _graph_stage_metrics(
    trace: dict | None,
    gold_entities: list[str],
    gold_chunks: list[str],
    missing_gold_entities: list[str],
    score_at_k: dict,
    score_at_oracle: dict,
    error: str | None,
) -> dict:
    if trace is None:
        return {
            "seed_hit": None,
            "ppr_hit": None,
            "chunk_map_hit": None,
            "bottleneck_label": "not_applicable",
        }

    seed_names = {
        _normalize_entity(seed.get("name", ""))
        for seed in trace.get("seeds", [])
        if seed.get("name")
    }
    ppr_names = {
        _normalize_entity(entity.get("name", ""))
        for entity in trace.get("ppr_entities", [])
        if entity.get("name")
    }
    for cluster in trace.get("cluster_entries", []):
        ppr_names.update(
            _normalize_entity(alias)
            for alias in cluster.get("aliases", [])
            if alias
        )

    candidate_ids = {
        str(chunk.get("chunk_id", ""))
        for chunk in trace.get("chunk_candidates", [])
        if chunk.get("chunk_id")
    }

    seed_hit = _hit_from_names(seed_names, gold_entities)
    ppr_hit = _hit_from_names(ppr_names, gold_entities)
    chunk_map_hit = None
    if gold_chunks:
        chunk_map_hit = 1 if candidate_ids & set(gold_chunks) else 0

    if not gold_chunks:
        bottleneck = "unscored_discovery"
    elif error:
        bottleneck = "tool_error"
    elif score_at_k["hit"] == 1:
        bottleneck = "hit_top_k"
    elif missing_gold_entities:
        bottleneck = "corpus_not_ready"
    elif seed_hit == 0:
        bottleneck = "seed_loss"
    elif ppr_hit == 0:
        bottleneck = "ppr_loss"
    elif chunk_map_hit == 0:
        bottleneck = "chunk_mapping_loss"
    elif score_at_oracle["hit"] == 1:
        bottleneck = "rerank_loss"
    else:
        bottleneck = "candidate_pool_loss"

    return {
        "seed_hit": seed_hit,
        "ppr_hit": ppr_hit,
        "chunk_map_hit": chunk_map_hit,
        "bottleneck_label": bottleneck,
        "abort_reason": trace.get("abort_reason"),
        "effective_query": trace.get("effective_query"),
        "seed_mode": trace.get("seed_mode"),
        "seed_names": sorted(seed_names),
        "ppr_entity_names": [
            str(entity.get("name", ""))
            for entity in trace.get("ppr_entities", [])[:20]
            if entity.get("name")
        ],
        "chunk_candidate_ids": _chunk_ids(
            trace.get("chunk_candidates", []),
            len(trace.get("chunk_candidates", [])),
        ),
    }


def _run_tool(
    tool_name: str,
    query: str,
    top_k: int,
    cfg,
    use_graph_expansion: bool,
    graph_seed_mode: str,
) -> tuple[list[dict], str | None, float, dict | None]:
    started = time.time()
    try:
        if tool_name == "graph":
            from semigraph.online.graph_search import trace_graph_search

            trace = trace_graph_search(
                query,
                top_k_chunks=top_k,
                use_expansion=use_graph_expansion,
                seed_mode=graph_seed_mode,
                cfg=cfg,
            )
            return trace["chunks"], None, time.time() - started, trace

        chunks = _get_tool(
            tool_name,
            use_graph_expansion=use_graph_expansion,
            graph_seed_mode=graph_seed_mode,
        )(query, top_k_chunks=top_k, cfg=cfg)
        return chunks, None, time.time() - started, None
    except Exception as exc:
        return [], f"{type(exc).__name__}: {exc}", time.time() - started, None


def _evaluate_query(
    item: dict,
    tools: list[str],
    top_k: int,
    oracle_k: int,
    cfg,
    dry_run: bool,
    use_graph_expansion: bool,
    graph_seed_mode: str,
    corpus_size: int,
    subset: str,
    existing_entities: set[str],
) -> dict:
    query = str(item.get("query", "")).strip()
    gold_chunks = [str(cid) for cid in item.get("gold_chunks", []) if cid]
    gold_entities = _gold_entities(item)
    missing_gold_entities = [
        entity for entity in gold_entities if entity not in existing_entities
    ]
    if not gold_chunks:
        corpus_status = "unscored_discovery"
    elif missing_gold_entities:
        corpus_status = "missing_gold_entities"
    else:
        corpus_status = "ready"

    result = {
        "id": item.get("id", ""),
        "query": query,
        "type": item.get("type", ""),
        "subset": subset,
        "gold_tools": item.get("gold_tools", []),
        "gold_entities": gold_entities,
        "missing_gold_entities": missing_gold_entities,
        "corpus_status": corpus_status,
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
            chunks, error, latency, trace = [], None, 0.0, None
        else:
            chunks, error, latency, trace = _run_tool(
                tool_name=tool_name,
                query=query,
                top_k=max(top_k, oracle_k),
                cfg=cfg,
                use_graph_expansion=use_graph_expansion,
                graph_seed_mode=graph_seed_mode,
            )

        returned_at_k = _chunk_ids(chunks, top_k)
        returned_at_oracle = _chunk_ids(chunks, oracle_k)
        if dry_run:
            score_at_k = _unscored_result()
            score_at_oracle = _unscored_result()
        else:
            score_at_k = _score_result(returned_at_k, gold_chunks)
            score_at_oracle = _score_result(returned_at_oracle, gold_chunks)

        stage = _graph_stage_metrics(
            trace=trace,
            gold_entities=gold_entities,
            gold_chunks=gold_chunks,
            missing_gold_entities=missing_gold_entities,
            score_at_k=score_at_k,
            score_at_oracle=score_at_oracle,
            error=error,
        )
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
            "stage": stage,
        }

    return result


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _metric_bucket() -> dict[str, list[float]]:
    return defaultdict(list)


def _add_tool_metrics(bucket: dict, tool_name: str, metrics: dict) -> None:
    bucket[tool_name]["hit"].append(float(metrics["hit_at_k"]))
    bucket[tool_name]["recall"].append(float(metrics["recall_at_k"]))
    bucket[tool_name]["mrr"].append(float(metrics["mrr_at_k"]))
    bucket[tool_name]["oracle_hit"].append(float(metrics["oracle_hit"]))


def _summarize_grouped_metrics(grouped: dict, tools: list[str], key_name: str) -> list[dict]:
    rows: list[dict] = []
    for group in sorted(grouped):
        row = {key_name: group}
        for tool_name in tools:
            row[f"{tool_name}_hit"] = _mean(grouped[group][tool_name]["hit"])
            row[f"{tool_name}_recall"] = _mean(grouped[group][tool_name]["recall"])
            row[f"{tool_name}_mrr"] = _mean(grouped[group][tool_name]["mrr"])
            row[f"{tool_name}_oracle_hit"] = _mean(
                grouped[group][tool_name]["oracle_hit"]
            )
        rows.append(row)
    return rows


def _paired_recall_test(
    results: list[dict],
    compare_tool: str,
    subset: str | None = None,
    baseline_tool: str = "vector",
    iterations: int = 10000,
) -> dict:
    diffs: list[float] = []
    for row in results:
        if subset is not None and row.get("subset") != subset:
            continue
        tools = row.get("tools", {})
        if baseline_tool not in tools or compare_tool not in tools:
            continue
        base = tools[baseline_tool].get("recall_at_k")
        comp = tools[compare_tool].get("recall_at_k")
        if base is None or comp is None:
            continue
        diffs.append(float(comp) - float(base))

    observed = _mean(diffs)
    if len(diffs) < 2:
        return {
            "n": len(diffs),
            "mean_delta_recall": observed,
            "p_value_one_sided": None,
        }

    if observed <= 0:
        return {
            "n": len(diffs),
            "mean_delta_recall": observed,
            "p_value_one_sided": 1.0,
        }

    rng = random.Random(1337)
    more_extreme = 0
    for _ in range(iterations):
        signed_mean = _mean([
            diff if rng.random() < 0.5 else -diff
            for diff in diffs
        ])
        if signed_mean >= observed:
            more_extreme += 1

    return {
        "n": len(diffs),
        "mean_delta_recall": observed,
        "p_value_one_sided": (more_extreme + 1) / (iterations + 1),
    }


def _aggregate(results: list[dict], tools: list[str]) -> dict:
    aggregate: dict[str, dict] = {}
    by_type: dict[str, dict[str, dict[str, list[float]]]] = defaultdict(
        lambda: defaultdict(_metric_bucket)
    )
    by_subset: dict[str, dict[str, dict[str, list[float]]]] = defaultdict(
        lambda: defaultdict(_metric_bucket)
    )
    graph_stage = {
        "full_mixed": {
            "seed_hit": [],
            "ppr_hit": [],
            "chunk_map_hit": [],
            "bottlenecks": Counter(),
        }
    }

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
            _add_tool_metrics(by_type[qtype], tool_name, metrics)
            subset = row.get("subset") or "unknown_subset"
            _add_tool_metrics(by_subset[subset], tool_name, metrics)

            if tool_name == "graph":
                stage = metrics.get("stage", {})
                labels = ["full_mixed", subset]
                for label in labels:
                    graph_stage.setdefault(label, {
                        "seed_hit": [],
                        "ppr_hit": [],
                        "chunk_map_hit": [],
                        "bottlenecks": Counter(),
                    })
                    for metric_name in ("seed_hit", "ppr_hit", "chunk_map_hit"):
                        value = stage.get(metric_name)
                        if value is not None:
                            graph_stage[label][metric_name].append(float(value))
                    graph_stage[label]["bottlenecks"][stage.get(
                        "bottleneck_label",
                        "unknown",
                    )] += 1

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

    stage_rows: list[dict] = []
    for subset, values in sorted(graph_stage.items()):
        stage_rows.append({
            "subset": subset,
            "seed_hit": _mean(values["seed_hit"]),
            "ppr_hit": _mean(values["ppr_hit"]),
            "chunk_map_hit": _mean(values["chunk_map_hit"]),
            "bottlenecks": dict(values["bottlenecks"]),
        })

    paired = {}
    if "vector" in tools:
        paired["full_mixed"] = {
            tool_name: _paired_recall_test(results, tool_name)
            for tool_name in tools
            if tool_name != "vector"
        }
        for subset in sorted(by_subset):
            paired[subset] = {
                tool_name: _paired_recall_test(results, tool_name, subset=subset)
                for tool_name in tools
                if tool_name != "vector"
            }

    return {
        "overall": aggregate,
        "by_type": _summarize_grouped_metrics(by_type, tools, "type"),
        "by_subset": _summarize_grouped_metrics(by_subset, tools, "subset"),
        "graph_stage": stage_rows,
        "paired_recall_vs_vector": paired,
    }


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
    use_graph_expansion: bool,
    graph_seed_mode: str,
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
    lines.append(f"graph_use_expansion: `{use_graph_expansion}`")
    lines.append(f"graph_seed_mode: `{graph_seed_mode}`")
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

    if aggregate["by_subset"]:
        lines.append("")
        lines.append("## By Subset")
        lines.append("")
        header = ["Subset"]
        for tool_name in tools:
            header.extend([f"{tool_name} Hit", f"{tool_name} Recall", f"{tool_name} Oracle"])
        lines.append("| " + " | ".join(header) + " |")
        lines.append("|" + "|".join(["---"] + ["---:"] * (len(header) - 1)) + "|")
        for row in aggregate["by_subset"]:
            cells = [row["subset"]]
            for tool_name in tools:
                cells.append(_fmt(row.get(f"{tool_name}_hit")))
                cells.append(_fmt(row.get(f"{tool_name}_recall")))
                cells.append(_fmt(row.get(f"{tool_name}_oracle_hit")))
            lines.append("| " + " | ".join(cells) + " |")

    if aggregate["graph_stage"]:
        lines.append("")
        lines.append("## Graph Stage Diagnostics")
        lines.append("")
        lines.append("| Subset | SeedHit | PPRHit | ChunkMapHit | Bottlenecks |")
        lines.append("|---|---:|---:|---:|---|")
        for row in aggregate["graph_stage"]:
            bottlenecks = ", ".join(
                f"{name}={count}"
                for name, count in sorted(row["bottlenecks"].items())
            )
            lines.append(
                "| "
                f"{row['subset']} | "
                f"{_fmt(row['seed_hit'])} | "
                f"{_fmt(row['ppr_hit'])} | "
                f"{_fmt(row['chunk_map_hit'])} | "
                f"{bottlenecks or 'n/a'} |"
            )

    if aggregate["paired_recall_vs_vector"]:
        lines.append("")
        lines.append("## Paired Recall Test vs Vector")
        lines.append("")
        lines.append("| Subset | Tool | n | Mean Delta Recall | One-sided p |")
        lines.append("|---|---|---:|---:|---:|")
        for subset, comparisons in aggregate["paired_recall_vs_vector"].items():
            for tool_name, row in comparisons.items():
                lines.append(
                    "| "
                    f"{subset} | {tool_name} | {row['n']} | "
                    f"{_fmt(row['mean_delta_recall'])} | "
                    f"{_fmt(row['p_value_one_sided'])} |"
                )

    lines.append("")
    lines.append("## Per Query")
    for row in results:
        lines.append("")
        lines.append(f"### {row['id']}: `{row['query']}`")
        lines.append("")
        lines.append(f"- type: `{row['type']}`")
        lines.append(f"- subset: `{row['subset']}`")
        lines.append(f"- corpus_status: `{row['corpus_status']}`")
        lines.append(f"- gold_tools: `{row['gold_tools']}`")
        lines.append(f"- gold_entities: `{row['gold_entities']}`")
        lines.append(f"- missing_gold_entities: `{row['missing_gold_entities']}`")
        lines.append(f"- gold_chunks: `{row['gold_chunks']}`")
        lines.append("")
        lines.append("| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |")
        lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|")
        for tool_name in tools:
            metrics = row["tools"][tool_name]
            stage = metrics.get("stage", {})
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
                f"{_fmt(stage.get('seed_hit'))} | "
                f"{_fmt(stage.get('ppr_hit'))} | "
                f"{_fmt(stage.get('chunk_map_hit'))} | "
                f"{stage.get('bottleneck_label', 'n/a')} | "
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
    parser.add_argument(
        "--graph-seed-mode",
        choices=SEED_MODE_CHOICES,
        default="triple",
        help="Seed strategy for graph retrieval diagnostics.",
    )
    parser.add_argument(
        "--reextract-tickers",
        default=",".join(DEFAULT_REEXTRACT_TICKERS),
        help="Comma-separated tickers already re-extracted for subset reporting.",
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
    known_tickers = {
        ticker.upper()
        for ticker in (getattr(cfg, "tickers", None) or DEFAULT_REEXTRACT_TICKERS)
        if ticker
    }
    reextract_tickers = {
        ticker.strip().upper()
        for ticker in args.reextract_tickers.split(",")
        if ticker.strip()
    }
    all_gold_entities = sorted({
        entity
        for item in queries
        for entity in _gold_entities(item)
    })
    existing_entities = (
        set(all_gold_entities)
        if args.dry_run
        else _get_existing_entities(cfg, all_gold_entities)
    )

    results = [
        _evaluate_query(
            item=item,
            tools=args.tools,
            top_k=args.top_k,
            oracle_k=args.oracle_k,
            cfg=cfg,
            dry_run=args.dry_run,
            use_graph_expansion=not args.no_llm_expansion,
            graph_seed_mode=args.graph_seed_mode,
            corpus_size=corpus_size,
            subset=_classify_subset(item, reextract_tickers, known_tickers),
            existing_entities=existing_entities,
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
        use_graph_expansion=not args.no_llm_expansion,
        graph_seed_mode=args.graph_seed_mode,
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
