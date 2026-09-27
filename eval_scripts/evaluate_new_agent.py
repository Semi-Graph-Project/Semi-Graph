#!/usr/bin/env python3
"""Evaluate Vector, Graph, Agent+Vector, or Agent+Graph on SOX74."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json
import sys
import statistics
import time

from dotenv import load_dotenv
import yaml


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from semigraph.config import get_config  # noqa: E402
from semigraph.connections import get_llm  # noqa: E402
from semigraph.agents.graph import run_agent as run_new_agent  # noqa: E402
from semigraph.online.vector_search import vector_search as production_vector_search  # noqa: E402
from semigraph.online.graph_search import graph_search as production_graph_search  # noqa: E402
from semigraph.online.text_to_cypher import (  # noqa: E402
    text_to_cypher_search as production_text_to_cypher_search,
)
from eval_scripts.eval_agent import (
    GENERATION_ERROR_ANSWER,
    generate_final_answer,
)
from eval_scripts.token_usage import collect_token_usage, summarize_token_usage

VECTOR_INDEX = "gold_chunk_embedding"
TOP_K = 10
EVALUATION_MODES = ("retrieve_only", "full_answer")
AGENT_TOOLS = {
    "agent_vector": "vector",
    "agent_graph": "graph",
}
SOX_DATASET = ROOT / "benchmark/freezes/sox74_retrieval_ablation_v1/inputs/finreflectkg_sox_strict74.yaml"
SOX_QUERY_COUNT = 74
TRACE_OUTPUT_TEMPLATE = ROOT / (
    "benchmark/results2/controlled_{tool}_{scope}_{version_name}_{mode}.jsonl"
)
YAML_TRACE_OUTPUT_TEMPLATE = ROOT / (
    "benchmark/results2/controlled_{tool}_{scope}_{version_name}_{mode}.yaml"
)


def load_sox_queries() -> list[dict]:
    """Load the 74 SOX benchmark queries from YAML."""
    with SOX_DATASET.open(encoding="utf-8") as file:
        dataset = yaml.safe_load(file)

    queries = dataset["queries"]
    if len(queries) != SOX_QUERY_COUNT:
        raise ValueError(f"Expected {SOX_QUERY_COUNT} queries, got {len(queries)}")
    return queries


def _select_queries(
    queries: list[dict],
    limit: int | None = None,
    start: int | None = None,
    end: int | None = None,
) -> list[dict]:
    """Select the full set, first N cases, or an inclusive 1-based range."""
    if limit is not None and (start is not None or end is not None):
        raise ValueError("limit cannot be combined with start or end")

    if limit is not None:
        if isinstance(limit, bool) or limit < 1:
            raise ValueError("limit must be greater than zero")
        if limit > len(queries):
            raise ValueError(f"limit must not exceed {len(queries)}")
        return queries[:limit]

    if start is None and end is None:
        return queries

    first = 1 if start is None else start
    last = len(queries) if end is None else end
    for name, value in (("start", first), ("end", last)):
        if isinstance(value, bool) or value < 1:
            raise ValueError(f"{name} must be greater than zero")
    if first > last:
        raise ValueError("start must not exceed end")
    if last > len(queries):
        raise ValueError(f"end must not exceed {len(queries)}")
    return queries[first - 1:last]


def _requires_llm(tool: str, mode: str, cfg) -> bool:
    """Return whether this Eval configuration makes at least one LLM call."""
    graph_filter = str(
        cfg.agent_retrieval.get("graph", {}).get("triple_filter", "none")
    )
    return (
        mode == "full_answer"
        or tool in AGENT_TOOLS
        or tool == "text_to_cypher"
        or (tool == "graph" and graph_filter == "llm")
    )


def _validate_runtime(tool: str, mode: str) -> None:
    """Fail before an Eval starts when its configured LLM key is missing."""
    cfg = get_config()
    if _requires_llm(tool, mode, cfg) and not cfg.llm_api_key.strip():
        raise RuntimeError(
            f"{tool}/{mode} requires the API key for llm.provider="
            f"{cfg.llm_provider!r}; set it in .env before running Eval"
        )


def _reciprocal_rank(retrieved_ids: list[str], gold_ids: set[str]) -> float:
    """Return 1/rank for the first retrieved Gold chunk, or zero if absent."""
    for rank, chunk_id in enumerate(retrieved_ids, start=1):
        if chunk_id in gold_ids:
            return 1.0 / rank
    return 0.0


def vector_search(question: str, top_k: int = TOP_K) -> list[dict]:
    """Use the production vector_search implementation for Gold Chunks."""
    cfg = get_config()
    cfg.neo4j_uri = cfg.controlled_neo4j_uri
    return production_vector_search(
        question,
        top_k_chunks=top_k,
        cfg=cfg,
        vector_index=VECTOR_INDEX,
    )


def graph_search(question: str, top_k: int = TOP_K) -> list[dict]:
    cfg = get_config()
    cfg.neo4j_uri = cfg.controlled_neo4j_uri

    profile = cfg.agent_retrieval["graph"]

    return production_graph_search(
        question,
        top_k_chunks=top_k,
        top_k_entities=int(profile["top_k_entities"]),
        top_k_triples=int(profile["top_k_triples"]),
        top_k_chunk_seeds=int(profile.get("top_k_chunk_seeds", 5)),
        chunk_seed_vector_index=VECTOR_INDEX,
        damping=float(profile["damping"]),
        use_expansion=bool(profile["use_expansion"]),
        seed_mode=str(profile["seed_mode"]),
        candidate_pool_k=int(profile["candidate_pool_k"]),
        ppr_seed_weight_mode=str(profile["ppr_seed_weight_mode"]),
        graph_triple_filter=str(profile["triple_filter"]),
        cfg=cfg,
    )


def text_to_cypher_search(question: str, top_k: int = TOP_K) -> dict:
    """Return Text-to-Cypher Chunks and the generated query for tracing."""
    cfg = get_config()
    cfg.neo4j_uri = cfg.controlled_neo4j_uri
    return production_text_to_cypher_search(
        question,
        top_k_chunks=top_k,
        cfg=cfg,
    )


def write_trace(results: list[dict], output_path: Path) -> None:
    """Write one query trace per line as JSONL."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        for result in results:
            file.write(json.dumps(result, ensure_ascii=False) + "\n")


def append_trace(result: dict, output_path: Path) -> None:
    """Append one completed query trace without waiting for the full run."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(result, ensure_ascii=False) + "\n")


def write_yaml_trace(
    results: list[dict],
    output_path: Path,
    measurement: dict | None = None,
) -> None:
    """Write summary metrics followed by all completed query traces."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "query_count": len(results),
        "hit": round(statistics.fmean(row["hit"] for row in results), 3)
        if results
        else None,
        "recall": round(statistics.fmean(row["recall"] for row in results), 3)
        if results
        else None,
        "mrr": round(
            statistics.fmean(row["reciprocal_rank"] for row in results), 3
        )
        if results
        else None,
        "average_latency_ms": round(
            statistics.fmean(row["latency_ms"] for row in results), 1
        )
        if results
        else None,
        "average_answer_latency_ms": round(
            statistics.fmean(row["answer_latency_ms"] for row in results), 1
        ) if results else None,
        "average_total_latency_ms": round(
            statistics.fmean(row["total_latency_ms"] for row in results), 1
        ) if results else None,
        "token_usage": summarize_token_usage(
            [row["token_usage"] for row in results]
        ),
    }
    trace = {"summary": summary, "results": results}
    if measurement is not None:
        trace["measurement"] = measurement
        summary["token_usage_including_warmup"] = summarize_token_usage([
            summary["token_usage"],
            measurement["warmup"]["token_usage"],
        ])
    output_path.write_text(
        yaml.safe_dump(
            trace,
            allow_unicode=True,
            sort_keys=False,
            width=120,
        ),
        encoding="utf-8",
    )


def _run_agent(
    question: str,
    tool: str,
    generate_answer: bool,
) -> dict:
    """Run one evaluation Agent and return its selected Chunks and answer."""
    if not isinstance(question, str) or not question.strip():
        return {
            "chunks": [],
            "final_answer": "Do not Answer" if generate_answer else "",
            "answer_latency_ms": 0.0,
        }
    if tool not in AGENT_TOOLS:
        raise ValueError("tool must be 'agent_vector' or 'agent_graph'")

    cfg = get_config()
    cfg.neo4j_uri = cfg.controlled_neo4j_uri
    selected_tool = AGENT_TOOLS[tool]
    if selected_tool == "vector":
        cfg.agent_retrieval["vector"]["vector_index"] = VECTOR_INDEX
    else:
        cfg.agent_retrieval["graph"]["chunk_seed_vector_index"] = VECTOR_INDEX

    result = run_new_agent(
        {"original_query": question},
        tool=selected_tool,
        cfg=cfg,
        generate_answer=generate_answer,
    )
    synthesis_input = result.get("synthesis_input")
    if not isinstance(synthesis_input, dict):
        raise RuntimeError("Agent result is missing synthesis_input")

    accepted_chunks = synthesis_input.get("accepted_chunks")
    if not isinstance(accepted_chunks, list):
        raise RuntimeError("Agent synthesis_input has invalid accepted_chunks")

    chunks = []
    seen_chunk_ids = set()
    for chunk in accepted_chunks:
        if not isinstance(chunk, dict) or not chunk.get("chunk_id"):
            raise RuntimeError("Agent returned a Chunk without chunk_id")
        chunk_id = str(chunk["chunk_id"])
        if chunk_id not in seen_chunk_ids:
            chunks.append(chunk)
            seen_chunk_ids.add(chunk_id)

    return {
        "chunks": chunks,
        "final_answer": str(result.get("final_answer") or ""),
        "answer_latency_ms": float(result.get("synthesis_latency_ms") or 0.0),
        "answer_error": None,
        "synthesis_trace": result.get("synthesis_trace"),
    }


def agent_vector_search(question: str) -> list[dict]:
    """Return the Chunks selected by the evaluation Vector Agent."""
    return _run_agent(
        question,
        tool="agent_vector",
        generate_answer=False,
    )["chunks"]


def agent_graph_search(question: str) -> list[dict]:
    """Return the Chunks selected by the evaluation Graph Agent."""
    return _run_agent(
        question,
        tool="agent_graph",
        generate_answer=False,
    )["chunks"]


def evaluate_sox_queries(
    tool: str = "vector",
    version_name: str = "v1",
    mode: str = "retrieve_only",
    workers: int = 8,
    limit: int | None = None,
    start: int | None = None,
    end: int | None = None,
) -> list[dict]:
    """Evaluate SOX74, its first N cases, or an inclusive query range."""
    if mode not in EVALUATION_MODES:
        raise ValueError(f"mode must be one of {EVALUATION_MODES}")
    if workers < 1:
        raise ValueError("workers must be greater than zero")

    _validate_runtime(tool, mode)
    cfg = get_config()
    answer_audit_enabled = (
        mode == "full_answer"
        and tool not in AGENT_TOOLS
        and cfg.eval_answer_audit_enabled
    )
    all_queries = load_sox_queries()
    queries = _select_queries(all_queries, limit, start, end)
    if start is not None or end is not None:
        scope = f"sox_range{start or 1}_{end or len(all_queries)}"
        selection_start = start or 1
        selection_end = end or len(all_queries)
    else:
        scope = "sox74" if limit is None else f"sox_smoke{limit}"
        selection_start = 1
        selection_end = len(queries)
    searches = {
        "vector": vector_search,
        "graph": graph_search,
        "text_to_cypher": text_to_cypher_search,
        "agent_vector": agent_vector_search,
        "agent_graph": agent_graph_search,
    }
    search = searches[tool]
    trace_output = Path(
        str(TRACE_OUTPUT_TEMPLATE).format(
            tool=tool,
            scope=scope,
            version_name=version_name,
            mode=mode,
        )
    )
    yaml_trace_output = Path(
        str(YAML_TRACE_OUTPUT_TEMPLATE).format(
            tool=tool,
            scope=scope,
            version_name=version_name,
            mode=mode,
        )
    )
    # Warm the selected retriever, including its reranker and Triple cache.
    # Keep warm-up LLM tokens separate from the measured benchmark queries.
    warmup_tool = AGENT_TOOLS.get(tool, tool)
    print(f"Warm-up: {warmup_tool} (excluded from per-query latency)")
    with collect_token_usage() as warmup_usage:
        warmup_started = time.perf_counter()
        searches[warmup_tool](queries[0]["query"], top_k=TOP_K)
        warmup_latency_ms = (time.perf_counter() - warmup_started) * 1000
    measurement = {
        "tool": tool,
        "mode": mode,
        "workers": workers,
        "selection": {
            "start": selection_start,
            "end": selection_end,
            "query_count": len(queries),
        },
        "answer_audit_enabled": answer_audit_enabled,
        "latency_scope": (
            "Per-query wall time after warm-up; excludes executor queue, "
            "metric calculation and trace writes; includes internal lock waits. "
            "Agent retrieval includes planning, assessment and retries."
        ),
        "token_usage_scope": (
            "Provider-reported LLM tokens across all calls and retries; "
            "excludes local embeddings and reranking. Partial totals cover "
            "only calls that returned usage. Warm-up is reported separately."
        ),
        "warmup": {
            "tool": warmup_tool,
            "latency_ms": warmup_latency_ms,
            "token_usage": warmup_usage.snapshot(),
        },
    }

    llm = (
        get_llm(get_config())
        if mode == "full_answer" and tool not in AGENT_TOOLS
        else None
    )

    def evaluate_case(case: dict) -> dict:
        """Evaluate one case and return its retrieval/generation metrics."""
        agent_result = None
        answer_error = None
        final_answer = "None"
        answer_latency_ms = 0.0
        synthesis_trace = None
        generated_cypher = None
        with collect_token_usage() as usage:
            started = time.perf_counter()
            if tool in AGENT_TOOLS:
                agent_result = _run_agent(
                    case["query"],
                    tool=tool,
                    generate_answer=mode == "full_answer",
                )
                retrieved = agent_result["chunks"]
                if mode == "full_answer":
                    final_answer = agent_result["final_answer"]
                    answer_latency_ms = agent_result["answer_latency_ms"]
                    answer_error = agent_result.get("answer_error")
                    synthesis_trace = agent_result.get("synthesis_trace")
            else:
                retrieval_result = search(case["query"], top_k=TOP_K)
                if tool == "text_to_cypher":
                    retrieved = retrieval_result["chunks"]
                    generated_cypher = retrieval_result["generated_cypher"]
                else:
                    retrieved = retrieval_result
                if mode == "full_answer":
                    answer_started = time.perf_counter()
                    synthesis_trace = {}
                    try:
                        final_answer = generate_final_answer(
                            llm,
                            case["query"],
                            retrieved,
                            audit_enabled=answer_audit_enabled,
                            synthesis_trace=synthesis_trace,
                        )
                        if final_answer == GENERATION_ERROR_ANSWER:
                            answer_error = "AnswerGenerationError"
                    except Exception as exc:
                        final_answer = GENERATION_ERROR_ANSWER
                        answer_error = type(exc).__name__
                    answer_latency_ms = (time.perf_counter() - answer_started) * 1000
            total_latency_ms = (time.perf_counter() - started) * 1000
        if not 0.0 <= answer_latency_ms <= total_latency_ms:
            raise RuntimeError("Answer latency must fall within total query latency")
        retrieval_latency_ms = total_latency_ms - answer_latency_ms

        gold_ids = set(case["gold_chunks"])
        retrieved_ids = [chunk["chunk_id"] for chunk in retrieved]
        hits = gold_ids.intersection(retrieved_ids)
        hit = int(bool(hits))
        recall = len(hits) / len(gold_ids)
        reciprocal_rank = _reciprocal_rank(retrieved_ids, gold_ids)

        result = {
            "id": case["id"],
            "mode": mode,
            "answer_audit_enabled": answer_audit_enabled,
            "query": case["query"],
            "gold_chunks": case["gold_chunks"],
            "top_chunk_ids": retrieved_ids,
            "answer_points": case.get("answer_points", []),
            "final_answer": final_answer,
            "hit": hit,
            "recall": recall,
            "reciprocal_rank": reciprocal_rank,
            "latency_ms": retrieval_latency_ms,
            "answer_latency_ms": answer_latency_ms,
            "total_latency_ms": total_latency_ms,
            "token_usage": usage.snapshot(),
        }
        if answer_error:
            result["answer_error"] = answer_error
        if synthesis_trace is not None:
            result["synthesis_trace"] = synthesis_trace
        if generated_cypher is not None:
            result["generated_cypher"] = generated_cypher
        return result

    # Start a fresh trace; each completed query is appended immediately.
    write_trace([], trace_output)
    write_yaml_trace([], yaml_trace_output, measurement)
    results = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        for result in executor.map(evaluate_case, queries):
            results.append(result)
            append_trace(result, trace_output)
            write_yaml_trace(results, yaml_trace_output, measurement)
            print(
                f"{result['id']} | Hit={result['hit']} | "
                f"Recall={result['recall']:.3f} | "
                f"RR={result['reciprocal_rank']:.3f} | "
                f"Retrieval={result['latency_ms']:.1f} ms | "
                f"Answer={result['answer_latency_ms']:.1f} ms | "
                f"Total={result['total_latency_ms']:.1f} ms | "
                f"Tokens={result['token_usage']['total_tokens']} "
                f"({result['token_usage']['status']})"
            )

    print(f"\nHit: {statistics.fmean(row['hit'] for row in results):.3f}")
    print(f"Recall: {statistics.fmean(row['recall'] for row in results):.3f}")
    print(
        "MRR: "
        f"{statistics.fmean(row['reciprocal_rank'] for row in results):.3f}"
    )
    print(
        "Mean retrieval latency: "
        f"{statistics.fmean(row['latency_ms'] for row in results):.1f} ms"
    )
    print(
        "Mean total latency: "
        f"{statistics.fmean(row['total_latency_ms'] for row in results):.1f} ms"
    )
    print(f"LLM token usage: {summarize_token_usage([row['token_usage'] for row in results])}")
    print(f"Tool: {tool}")
    print(f"Mode: {mode}")
    print(f"Answer audit: {'enabled' if answer_audit_enabled else 'disabled'}")
    print(f"Trace: {trace_output}")
    print(f"YAML trace: {yaml_trace_output}")
    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate Vector/Graph/Text-to-Cypher/Agent on SOX74"
    )
    parser.add_argument(
        "--tool",
        choices=(
            "vector",
            "graph",
            "text_to_cypher",
            "agent_vector",
            "agent_graph",
        ),
        default="vector",
        help="retriever to evaluate (default: vector)",
        required=True,
    )
    parser.add_argument(
        "--version_name",
        default="v1",
        help="Version name for the evaluation (default: v1)",
    )
    parser.add_argument(
        "--mode",
        choices=EVALUATION_MODES,
        default="retrieve_only",
        help="retrieve only or also generate final answers",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=8,
        help="number of queries evaluated concurrently (default: 8)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="run only the first N queries for a quick smoke evaluation",
    )
    parser.add_argument(
        "--start",
        type=int,
        help="first query position to run, 1-based and inclusive",
    )
    parser.add_argument(
        "--end",
        type=int,
        help="last query position to run, 1-based and inclusive",
    )
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("--workers must be greater than zero")
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be greater than zero")
    if args.start is not None and args.start < 1:
        parser.error("--start must be greater than zero")
    if args.end is not None and args.end < 1:
        parser.error("--end must be greater than zero")
    if args.limit is not None and (args.start is not None or args.end is not None):
        parser.error("--limit cannot be combined with --start or --end")

    load_dotenv(ROOT / ".env")
    evaluate_sox_queries(
        tool=args.tool,
        version_name=args.version_name,
        mode=args.mode,
        workers=args.workers,
        limit=args.limit,
        start=args.start,
        end=args.end,
    )


if __name__ == "__main__":
    print(f"Running {__file__} with Python {sys.version} Agent Version 1.5")
    main()
