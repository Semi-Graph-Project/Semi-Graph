#!/usr/bin/env python3

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import sys
import time
from typing import Any, Iterable

from dotenv import load_dotenv
import yaml


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
DEFAULT_QUERY_FILE = (
    ROOT
    / "benchmark/freezes/sox74_retrieval_ablation_v1/inputs/"
    / "finreflectkg_sox_strict74.yaml"
)
TOOLS = ("vector", "graph", "agent_vector", "agent_graph")
MODES = ("retrieve_only", "full_answer")


def load_queries(path: Path = DEFAULT_QUERY_FILE) -> list[dict[str, Any]]:
    """Load benchmark query cases without running retrieval or generation."""
    with path.open(encoding="utf-8") as file:
        dataset = yaml.safe_load(file)

    queries = dataset.get("queries") if isinstance(dataset, dict) else dataset
    if not isinstance(queries, list):
        raise ValueError("Query file must contain a 'queries' list")

    validated: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for case in queries:
        if not isinstance(case, dict):
            raise ValueError("Each query case must be a mapping")
        case_id = str(case.get("id") or "").strip()
        query = str(case.get("query") or "").strip()
        if not case_id or not query:
            raise ValueError("Each query case needs non-empty 'id' and 'query'")
        if case_id in seen_ids:
            raise ValueError(f"Duplicate query id: {case_id}")
        seen_ids.add(case_id)
        validated.append(case)
    return validated


def build_jobs(
    queries: Iterable[dict[str, Any]],
    tools: Iterable[str] = TOOLS,
    mode: str = "full_answer",
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Expand query cases into deterministic, pending batch jobs."""
    selected_tools = [str(tool) for tool in tools]
    invalid_tools = sorted(set(selected_tools) - set(TOOLS))
    if invalid_tools:
        raise ValueError(f"Unsupported tool(s): {', '.join(invalid_tools)}")
    if not selected_tools:
        raise ValueError("At least one tool is required")
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    if limit is not None and limit < 1:
        raise ValueError("limit must be greater than zero")

    cases = list(queries)
    if limit is not None:
        cases = cases[:limit]

    jobs: list[dict[str, Any]] = []
    for case in cases:
        query_id = str(case["id"])
        for tool in selected_tools:
            job = dict(case)
            job.update(
                {
                    "job_id": f"{query_id}:{tool}:{mode}",
                    "query_id": query_id,
                    "tool": tool,
                    "mode": mode,
                    "status": "pending",
                }
            )
            jobs.append(job)
    return jobs


def write_jobs(jobs: Iterable[dict[str, Any]], output_path: Path) -> int:
    """Write pending jobs as UTF-8 JSONL and return the number written."""
    rows = list(jobs)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")
    return len(rows)


def _run_one_job(job: dict[str, Any], top_k: int) -> dict[str, Any]:
    """Run one Agent Vector job and attach retrieval metrics."""
    from eval_scripts.evaluate import _run_agent, _reciprocal_rank

    started = time.perf_counter()
    try:
        agent_result = _run_agent(
            question=str(job["query"]),
            top_k=top_k,
            tool="agent_vector",
            generate_answer=job.get("mode") == "full_answer",
        )
        retrieved_ids = [
            str(chunk["chunk_id"])
            for chunk in agent_result.get("chunks", [])
            if chunk.get("chunk_id")
        ]
        gold_ids = {
            str(chunk_id) for chunk_id in (job.get("gold_chunks") or [])
        }
        hits = gold_ids.intersection(retrieved_ids)
        answer_latency_ms = float(agent_result.get("answer_latency_ms") or 0.0)
        result = {
            **job,
            "status": "completed",
            "top_chunk_ids": retrieved_ids,
            "hit": int(bool(hits)) if gold_ids else None,
            "recall": len(hits) / len(gold_ids) if gold_ids else None,
            "reciprocal_rank": _reciprocal_rank(retrieved_ids, gold_ids)
            if gold_ids
            else None,
            "latency_ms": max(
                0.0,
                (time.perf_counter() - started) * 1000 - answer_latency_ms,
            ),
            "answer_latency_ms": answer_latency_ms,
        }
        if agent_result.get("answer_error"):
            result["answer_error"] = agent_result["answer_error"]
        return result
    except Exception as exc:
        return {
            **job,
            "status": "error",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "latency_ms": (time.perf_counter() - started) * 1000,
        }


def run_jobs(
    jobs: Iterable[dict[str, Any]],
    workers: int = 8,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """Run pending jobs concurrently and return results in input order."""
    if workers < 1:
        raise ValueError("workers must be greater than zero")
    if top_k < 1:
        raise ValueError("top_k must be greater than zero")

    pending = list(jobs)
    results: list[dict[str, Any] | None] = [None] * len(pending)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(_run_one_job, job, top_k): index
            for index, job in enumerate(pending)
        }
        for completed, future in enumerate(as_completed(futures), start=1):
            index = futures[future]
            result = future.result()
            results[index] = result
            print(
                f"[{completed}/{len(pending)}] {result['job_id']} "
                f"{result['status']}"
            )
    return [result for result in results if result is not None]


def _warm_embedding_model() -> None:
    """Load the shared embedding model before worker threads start."""
    from semigraph.offline.embeddings import get_embedding_model

    get_embedding_model().model


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Load evaluation cases and prepare pending LLM batch jobs"
    )
    parser.add_argument(
        "--queries",
        type=Path,
        default=DEFAULT_QUERY_FILE,
        help="benchmark YAML file (default: frozen SOX74 dataset)",
    )
    parser.add_argument(
        "--tools",
        nargs="+",
        choices=TOOLS,
        default=list(TOOLS),
        help="retrievers to include (default: all four ablation tools)",
    )
    parser.add_argument(
        "--mode",
        choices=MODES,
        default="full_answer",
        help="evaluation mode stored on each job (default: full_answer)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="load only the first N query cases",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="JSONL path for the pending manifest or run results",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="run the prepared jobs with Agent Vector after loading them",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=8,
        help="parallel workers when --run is used (default: 8)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="retrieval top-k passed to Agent Vector (default: 5)",
    )
    args = parser.parse_args()

    if args.workers < 1:
        parser.error("--workers must be greater than zero")
    if args.top_k < 1:
        parser.error("--top-k must be greater than zero")
    if args.run and args.tools != ["agent_vector"]:
        parser.error("--run currently supports only --tools agent_vector")

    queries = load_queries(args.queries)
    jobs = build_jobs(queries, tools=args.tools, mode=args.mode, limit=args.limit)
    selected_count = len(queries if args.limit is None else queries[:args.limit])
    print(f"Loaded {selected_count} query cases")

    if args.run:
        load_dotenv(ROOT / ".env")
        _warm_embedding_model()
        jobs = run_jobs(jobs, workers=args.workers, top_k=args.top_k)
        count = write_jobs(jobs, args.output)
        print(f"Completed {count} Agent Vector jobs")
        print(f"Batch results: {args.output}")
    else:
        count = write_jobs(jobs, args.output)
        print(f"Prepared {count} pending jobs")
        print(f"Batch manifest: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
