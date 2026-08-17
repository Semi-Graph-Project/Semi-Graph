#!/usr/bin/env python3
"""Evaluate Vector or Graph retrieval on the shared 74-query SOX set."""

import argparse
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
from semigraph.online.vector_search import vector_search as production_vector_search  # noqa: E402
from semigraph.online.graph_search import graph_search as production_graph_search  # noqa: E402
from eval_scripts.eval_agent import (
    GENERATION_ERROR_ANSWER,
    build_graph_eval_graph,
    build_vector_eval_graph,
    generate_final_answer,
)

NEO4J_URI = "bolt://localhost:7690"
VECTOR_INDEX = "gold_chunk_embedding"
TOP_K = 5
EVALUATION_MODES = ("retrieve_only", "full_answer")
AGENT_BUILDERS = {
    "agent_vector": build_vector_eval_graph,
    "agent_graph": build_graph_eval_graph,
}
SOX_DATASET = ROOT / "benchmark/freezes/sox74_retrieval_ablation_v1/inputs/finreflectkg_sox_strict74.yaml"
SOX_QUERY_COUNT = 74
TRACE_OUTPUT_TEMPLATE = ROOT / (
    "benchmark/results/controlled_{tool}_sox74_{version_name}_{mode}.jsonl"
)
YAML_TRACE_OUTPUT_TEMPLATE = ROOT / (
    "benchmark/results/controlled_{tool}_sox74_{version_name}_{mode}.yaml"
)




def load_sox_queries() -> list[dict]:
    """Load the 74 SOX benchmark queries from YAML."""
    with SOX_DATASET.open(encoding="utf-8") as file:
        dataset = yaml.safe_load(file)

    queries = dataset["queries"]
    if len(queries) != SOX_QUERY_COUNT:
        raise ValueError(f"Expected {SOX_QUERY_COUNT} queries, got {len(queries)}")
    return queries


def vector_search(question: str, top_k: int = TOP_K) -> list[dict]:
    """Use the production vector_search implementation for Gold Chunks."""
    cfg = get_config()
    cfg.neo4j_uri = NEO4J_URI
    return production_vector_search(
        question,
        top_k_chunks=top_k,
        cfg=cfg,
        vector_index=VECTOR_INDEX,
    )

def graph_search(question: str, top_k: int = TOP_K) -> list[dict]:
    cfg = get_config()
    cfg.neo4j_uri = NEO4J_URI

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
        rerank_mode=str(profile["rerank_mode"]),
        candidate_pool_k=int(profile["candidate_pool_k"]),
        final_rerank=str(profile["final_rerank"]),
        ppr_seed_weight_mode=str(profile["ppr_seed_weight_mode"]),
        ppr_graph_mode=str(profile["ppr_graph_mode"]),
        graph_triple_filter=str(profile["triple_filter"]),
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


def write_yaml_trace(results: list[dict], output_path: Path) -> None:
    """Write summary metrics followed by all completed query traces."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "hit": round(statistics.fmean(row["hit"] for row in results), 3)
        if results
        else None,
        "recall": round(statistics.fmean(row["recall"] for row in results), 3)
        if results
        else None,
        "average_latency_ms": round(
            statistics.fmean(row["latency_ms"] for row in results), 1
        )
        if results
        else None,
    }
    output_path.write_text(
        yaml.safe_dump(
            {"summary": summary, "results": results},
            allow_unicode=True,
            sort_keys=False,
            width=120,
        ),
        encoding="utf-8",
    )

def _run_agent(
    question: str,
    top_k: int,
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
    if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k < 1:
        raise ValueError("top_k must be a positive integer")

    graph = AGENT_BUILDERS[tool](
        top_k=top_k,
        generate_answer=generate_answer,
    )
    result = graph.invoke({"original_query": question})
    synthesis_trace = result.get("synthesis_trace")
    if not isinstance(synthesis_trace, dict):
        raise RuntimeError("Agent result is missing synthesis_trace")

    selected_chunk_ids = synthesis_trace.get("selected_chunk_ids")
    if not isinstance(selected_chunk_ids, list):
        raise RuntimeError(
            "Agent synthesis_trace has invalid selected_chunk_ids"
        )

    chunks_by_id = {
        chunk["chunk_id"]: chunk
        for attempt in (result.get("attempts") or [])
        for chunk in (attempt.get("chunks") or [])
        if isinstance(chunk, dict) and chunk.get("chunk_id")
    }
    missing_ids = set(selected_chunk_ids) - set(chunks_by_id)
    if missing_ids:
        raise RuntimeError(f"Agent selected unknown Chunk IDs: {missing_ids}")

    return {
        "chunks": [chunks_by_id[chunk_id] for chunk_id in selected_chunk_ids],
        "final_answer": str(result.get("final_answer") or ""),
        "answer_latency_ms": (
            float(synthesis_trace.get("latency_sec") or 0.0) * 1000
            if synthesis_trace.get("llm_calls")
            else 0.0
        ),
        "answer_error": synthesis_trace.get("error_type"),
    }


def agent_vector_search(question: str, top_k: int = TOP_K) -> list[dict]:
    """Return the Chunks selected by the evaluation Vector Agent."""
    return _run_agent(
        question,
        top_k,
        tool="agent_vector",
        generate_answer=False,
    )["chunks"]


def agent_graph_search(question: str, top_k: int = TOP_K) -> list[dict]:
    """Return the Chunks selected by the evaluation Graph Agent."""
    return _run_agent(
        question,
        top_k,
        tool="agent_graph",
        generate_answer=False,
    )["chunks"]


def evaluate_sox_queries(
    tool: str = "vector",
    version_name: str = "v1",
    mode: str = "retrieve_only",
) -> list[dict]:
    """Evaluate one production retriever on the 74 SOX queries."""
    if mode not in EVALUATION_MODES:
        raise ValueError(f"mode must be one of {EVALUATION_MODES}")

    queries = load_sox_queries()
    searches = {
        "vector": vector_search,
        "graph": graph_search,
        "agent_vector": agent_vector_search,
        "agent_graph": agent_graph_search,
    }
    search = searches[tool]
    trace_output = Path(
        str(TRACE_OUTPUT_TEMPLATE).format(
            tool=tool,
            version_name=version_name,
            mode=mode,
        )
    )
    yaml_trace_output = Path(
        str(YAML_TRACE_OUTPUT_TEMPLATE).format(
            tool=tool,
            version_name=version_name,
            mode=mode,
        )
    )


    # Load the embedding model before measuring per-query latency.
    vector_search(queries[0]["query"], top_k=TOP_K)

    llm = (
        get_llm(get_config())
        if mode == "full_answer" and tool not in AGENT_BUILDERS
        else None
    )

    # Start a fresh trace; each completed query is appended immediately.
    write_trace([], trace_output)
    write_yaml_trace([], yaml_trace_output)
    results = []
    for case in queries:
        started = time.perf_counter()
        agent_result = None
        if tool in AGENT_BUILDERS:
            agent_result = _run_agent(
                case["query"],
                TOP_K,
                tool=tool,
                generate_answer=mode == "full_answer",
            )
            retrieved = agent_result["chunks"]
        else:
            retrieved = search(case["query"], top_k=TOP_K)
        total_latency_ms = (time.perf_counter() - started) * 1000

        gold_ids = set(case["gold_chunks"])
        retrieved_ids = [chunk["chunk_id"] for chunk in retrieved]
        hits = gold_ids.intersection(retrieved_ids)
        hit = int(bool(hits))
        recall = len(hits) / len(gold_ids)

        answer_error = None
        final_answer = "None"
        answer_latency_ms = 0.0
        if mode == "full_answer" and agent_result is not None:
            final_answer = agent_result["final_answer"]
            answer_latency_ms = agent_result["answer_latency_ms"]
            answer_error = agent_result.get("answer_error")
        elif mode == "full_answer":
            answer_started = time.perf_counter()
            try:
                final_answer = generate_final_answer(llm, case["query"], retrieved)
                if final_answer == GENERATION_ERROR_ANSWER:
                    answer_error = "AnswerGenerationError"
            except Exception as exc:
                final_answer = GENERATION_ERROR_ANSWER
                answer_error = type(exc).__name__
            answer_latency_ms = (time.perf_counter() - answer_started) * 1000

        latency_ms = max(0.0, total_latency_ms - answer_latency_ms)

        result = {
            "id": case["id"],
            "mode": mode,
            "query": case["query"],
            "gold_chunks": case["gold_chunks"],
            "top_chunk_ids": retrieved_ids,
            "answer_points": case.get("answer_points", []),
            "final_answer": final_answer,
            "hit": hit,
            "recall": recall,
            "latency_ms": latency_ms,
            "answer_latency_ms": answer_latency_ms,
        }
        if answer_error:
            result["answer_error"] = answer_error
        results.append(result)
        append_trace(result, trace_output)
        write_yaml_trace(results, yaml_trace_output)
        print(
            f"{result['id']} | Hit={hit} | "
            f"Recall={recall:.3f} | Retrieval={latency_ms:.1f} ms | "
            f"Answer={answer_latency_ms:.1f} ms"
        )

    print(f"\nHit: {statistics.fmean(row['hit'] for row in results):.3f}")
    print(f"Recall: {statistics.fmean(row['recall'] for row in results):.3f}")
    print(
        "Mean latency: "
        f"{statistics.fmean(row['latency_ms'] for row in results):.1f} ms"
    )
    print(f"Tool: {tool}")
    print(f"Mode: {mode}")
    print(f"Trace: {trace_output}")
    print(f"YAML trace: {yaml_trace_output}")
    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate Vector or Graph retrieval on the 74 SOX queries"
    )
    parser.add_argument(
        "--tool",
        choices=("vector", "graph", "agent_vector", "agent_graph"),
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
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    evaluate_sox_queries(
        tool=args.tool,
        version_name=args.version_name,
        mode=args.mode,
    )


if __name__ == "__main__":
    main()
