#!/usr/bin/env python3
"""Measure RAGAS Faithfulness for controlled full-answer results."""

import argparse
import asyncio
from functools import lru_cache
import json
from pathlib import Path
from statistics import fmean
import sys

from openai import AsyncOpenAI
from ragas.llms import llm_factory
from ragas.metrics.collections import Faithfulness
import yaml


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from semigraph.config import get_config  # noqa: E402


DEFAULT_INPUT = ROOT / (
    "benchmark/human_verify_2/"
    "controlled_agent_graph_sox_smoke50_v1_full_answer.yaml"
)
CHUNK_STORES = (
    ROOT / "data/neo4j/finreflectkg_gold_chunks.jsonl",
    ROOT / "data/neo4j/finreflectkg_distractor_820_chunks.jsonl",
)
DEFAULT_CASE_ID = "FRKG009"
DEFAULT_MODEL = "anthropic/claude-haiku-5.5"
DEFAULT_MAX_TOKENS = 4096


def load_results(input_path: Path) -> list[dict]:
    """Load controlled results that contain final answers."""
    with input_path.open(encoding="utf-8") as file:
        data = yaml.safe_load(file)

    results = data.get("results", [])
    missing_answers = [
        result.get("id", "<unknown>")
        for result in results
        if not result.get("final_answer")
    ]
    if missing_answers:
        raise ValueError(
            "Cases with no final_answer: " + ", ".join(missing_answers)
        )
    return results


def load_case(input_path: Path, case_id: str) -> dict:
    """Load one result row by its benchmark ID."""
    for result in load_results(input_path):
        if result.get("id") == case_id:
            return result
    raise ValueError(f"Case {case_id!r} was not found in {input_path}")


def synthesis_chunk_ids(result: dict) -> list[str]:
    """Return unique chunk IDs used by final synthesis, preserving order."""
    trace = result.get("synthesis_trace") or {}
    chunk_ids = trace.get("selected_chunk_ids") or result.get("top_chunk_ids") or []
    unique_ids = list(dict.fromkeys(chunk_ids))
    if not unique_ids:
        raise ValueError(f"{result['id']} has no synthesis context IDs")
    return unique_ids


@lru_cache(maxsize=1)
def load_chunk_store() -> dict[str, str]:
    """Load the controlled chunk corpus once per evaluator process."""
    chunks_by_id = {}

    for store_path in CHUNK_STORES:
        with store_path.open(encoding="utf-8") as file:
            for line in file:
                chunk = json.loads(line)
                chunk_id = chunk.get("chunk_id")
                if chunk_id:
                    chunks_by_id[chunk_id] = chunk.get("text", "")

    return chunks_by_id


def load_contexts(chunk_ids: list[str]) -> list[str]:
    """Resolve controlled chunk IDs to their exact stored text."""
    chunks_by_id = load_chunk_store()
    wanted = set(chunk_ids)

    missing_ids = wanted - set(chunks_by_id)
    if missing_ids:
        missing = ", ".join(sorted(missing_ids))
        raise ValueError(f"Missing controlled chunk text for: {missing}")

    empty_ids = [chunk_id for chunk_id in chunk_ids if not chunks_by_id[chunk_id]]
    if empty_ids:
        raise ValueError(f"Empty controlled chunk text for: {', '.join(empty_ids)}")

    return [chunks_by_id[chunk_id] for chunk_id in chunk_ids]


async def measure_results(
    results: list[dict],
    model: str,
    max_tokens: int,
    workers: int,
) -> list[dict]:
    """Run RAGAS Faithfulness with bounded concurrency."""
    cfg = get_config()
    if not cfg.llm_api_key.strip():
        raise RuntimeError(
            f"Missing API key for llm.provider={cfg.llm_provider!r}; "
            "configure it in .env"
        )

    async with AsyncOpenAI(
        api_key=cfg.llm_api_key,
        base_url=cfg.llm_base_url,
        timeout=cfg.llm_timeout,
    ) as client:
        # OpenRouter exposes an OpenAI-compatible API.
        evaluator_llm = llm_factory(
            model,
            provider="openai",
            client=client,
            temperature=0.0,
            max_tokens=max_tokens,
        )
        semaphore = asyncio.Semaphore(workers)

        async def measure_one(index: int, result: dict) -> tuple[int, dict]:
            chunk_ids = []
            contexts = []
            try:
                chunk_ids = synthesis_chunk_ids(result)
                contexts = load_contexts(chunk_ids)
                async with semaphore:
                    metric = Faithfulness(llm=evaluator_llm)
                    score = await metric.ascore(
                        user_input=result["query"],
                        response=result["final_answer"],
                        retrieved_contexts=contexts,
                    )
                record = {
                    "case_id": result["id"],
                    "score": float(score.value),
                    "context_count": len(contexts),
                    "context_ids": chunk_ids,
                }
            except Exception as error:  # Keep the remaining batch measurable.
                record = {
                    "case_id": result["id"],
                    "score": None,
                    "context_count": len(contexts),
                    "context_ids": chunk_ids,
                    "error": f"{type(error).__name__}: {error}",
                }
            return index, record

        measured = await asyncio.gather(*(
            measure_one(index, result) for index, result in enumerate(results)
        ))

    return [record for _, record in sorted(measured)]


def build_report(
    input_path: Path,
    model: str,
    max_tokens: int,
    workers: int,
    records: list[dict],
) -> dict:
    """Build a reproducible batch summary."""
    scores = [record["score"] for record in records if record["score"] is not None]
    return {
        "input": str(input_path),
        "metric": "faithfulness",
        "judge_model": model,
        "temperature": 0.0,
        "max_tokens": max_tokens,
        "workers": workers,
        "response_field": "final_answer",
        "context_field": "synthesis_trace.selected_chunk_ids",
        "total_cases": len(records),
        "scored_cases": len(scores),
        "failed_cases": len(records) - len(scores),
        "mean_score": fmean(scores) if scores else None,
        "min_score": min(scores) if scores else None,
        "max_score": max(scores) if scores else None,
        "results": records,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Measure RAGAS Faithfulness for controlled final_answer rows."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Full-answer YAML (default: {DEFAULT_INPUT.relative_to(ROOT)})",
    )
    parser.add_argument(
        "--case-id",
        default=DEFAULT_CASE_ID,
        help=f"Benchmark case ID (default: {DEFAULT_CASE_ID})",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Measure every result in the input YAML instead of one case.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Judge model (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=DEFAULT_MAX_TOKENS,
        help=f"Maximum judge output tokens (default: {DEFAULT_MAX_TOKENS})",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=2,
        help="Maximum concurrent cases for --all (default: 2)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON report path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = args.input.expanduser().resolve()
    if args.max_tokens <= 0:
        raise ValueError("--max-tokens must be greater than zero")
    if args.workers <= 0:
        raise ValueError("--workers must be greater than zero")

    results = load_results(input_path) if args.all else [
        load_case(input_path, args.case_id)
    ]
    records = asyncio.run(measure_results(
        results=results,
        model=args.model,
        max_tokens=args.max_tokens,
        workers=args.workers if args.all else 1,
    ))
    report = build_report(
        input_path=input_path,
        model=args.model,
        max_tokens=args.max_tokens,
        workers=args.workers if args.all else 1,
        records=records,
    )

    if args.output:
        output_path = args.output.expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
