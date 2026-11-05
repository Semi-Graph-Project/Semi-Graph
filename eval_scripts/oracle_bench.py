#!/usr/bin/env python3
"""Generate SOX answers from Gold Chunks using the existing Agent Synthesize node."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import statistics
import sys
import time

import yaml


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for directory in (ROOT, SRC):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

from eval_scripts.evaluate_new_agent import (  # noqa: E402
    GENERATION_ERROR_ANSWER,
    SOX_DATASET,
    load_sox_queries,
)
from eval_scripts.token_usage import collect_token_usage, summarize_token_usage  # noqa: E402
from eval_scripts.transfer_gold_chunks import INPUT_FILE as GOLD_CHUNKS_FILE  # noqa: E402
from semigraph.agents.nodes import synthesize_node  # noqa: E402
from semigraph.config import get_config  # noqa: E402


DEFAULT_LIMIT = 50
OUTPUT_TEMPLATE = ROOT / "benchmark/results2/oracle_sox_smoke{limit}_full_answer.yaml"
EVIDENCE_FIELDS = (
    "chunk_id", "text", "ticker", "fiscal_year", "section", "source_file", "page_id",
)


def load_gold_chunks(path: Path = GOLD_CHUNKS_FILE) -> dict[str, dict]:
    """Index the same Gold Chunk texts that are imported into evaluation Neo4j."""
    chunks = {}
    with path.open(encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue
            record = json.loads(line)
            chunk_id = record["chunk_id"]
            if chunk_id in chunks:
                raise ValueError(f"Duplicate Gold Chunk: {chunk_id}")
            if not isinstance(record.get("text"), str) or not record["text"].strip():
                raise ValueError(f"Gold Chunk has no text: {chunk_id}")
            # Keep evidence metadata; embeddings and benchmark labels are not prompt input.
            chunks[chunk_id] = {
                field: record[field] for field in EVIDENCE_FIELDS if field in record
            }
    return chunks


def write_results(results: list[dict], output_path: Path, metadata: dict) -> None:
    """Checkpoint completed answers, replacing the YAML only after writing it fully."""
    payload = {
        **metadata,
        "summary": {
            "query_count": len(results),
            "error_count": sum(bool(row.get("answer_error")) for row in results),
            "average_answer_latency_ms": round(statistics.fmean(
                row["answer_latency_ms"] for row in results
            ), 1) if results else None,
            "token_usage": summarize_token_usage([row["token_usage"] for row in results]),
        },
        "results": results,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary_path.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False, width=120),
        encoding="utf-8",
    )
    temporary_path.replace(output_path)


def run_oracle_bench(
    *,
    limit: int = DEFAULT_LIMIT,
    workers: int = 8,
    output_path: Path | None = None,
    dataset_path: Path | None = None,
    gold_chunks_path: Path | None = None,
) -> list[dict]:
    """Send the first N questions and all their Gold Chunks directly to Synthesize."""
    selected_dataset = Path(dataset_path) if dataset_path is not None else SOX_DATASET
    selected_gold = Path(gold_chunks_path) if gold_chunks_path is not None else GOLD_CHUNKS_FILE
    use_selected_gold = gold_chunks_path is not None
    dataset_revision = "sox74_original"
    expected_gold_hash = None
    if dataset_path is None:
        queries = load_sox_queries()
    else:
        dataset = yaml.safe_load(selected_dataset.read_text(encoding="utf-8"))
        queries = dataset["queries"]
        dataset_revision = str(dataset.get("metadata", {}).get(
            "dataset_revision", selected_dataset.stem
        ))
        expected_gold_hash = dataset.get("metadata", {}).get("gold_chunks_sha256")
        if gold_chunks_path is None and dataset.get("metadata", {}).get("gold_chunks_file"):
            selected_gold = selected_dataset.parent / dataset["metadata"]["gold_chunks_file"]
            use_selected_gold = True
        if not isinstance(queries, list) or not queries:
            raise ValueError("dataset must contain a non-empty queries list")
        if len({case["id"] for case in queries}) != len(queries):
            raise ValueError("dataset contains duplicate query IDs")
    if not 1 <= limit <= len(queries):
        raise ValueError(f"limit must be between 1 and {len(queries)}")
    if workers < 1:
        raise ValueError("workers must be greater than zero")
    queries = queries[:limit]
    gold_hash = hashlib.sha256(selected_gold.read_bytes()).hexdigest()
    if expected_gold_hash is not None and gold_hash != expected_gold_hash:
        raise ValueError("Gold Chunk file does not match the dataset's gold_chunks_sha256")
    chunks = load_gold_chunks(selected_gold) if use_selected_gold else load_gold_chunks()
    # Validate every selected question before spending any LLM calls.
    for case in queries:
        if not isinstance(case.get("query"), str) or not case["query"].strip():
            raise ValueError(f"{case['id']} has no question text")
        if not case.get("gold_chunks"):
            raise ValueError(f"{case['id']} has no Gold Chunks")
        missing = [chunk_id for chunk_id in case["gold_chunks"] if chunk_id not in chunks]
        if missing:
            raise ValueError(f"{case['id']} is missing Gold Chunks: {missing}")

    cfg = deepcopy(get_config())
    if not cfg.llm_api_key.strip():
        raise RuntimeError(
            f"Oracle synthesis requires the API key for llm.provider={cfg.llm_provider!r}; "
            "set it in .env before running"
        )
    if output_path is not None:
        output_path = Path(output_path)
    elif dataset_path is not None:
        revision_slug = re.sub(r"[^A-Za-z0-9_-]+", "_", dataset_revision).strip("_") or "custom"
        output_path = ROOT / f"benchmark/results2/oracle_{revision_slug}_first{limit}_full_answer.yaml"
    else:
        output_path = Path(str(OUTPUT_TEMPLATE).format(limit=limit))
    metadata = {
        "measurement": {
            "tool": "oracle",
            "mode": "full_answer",
            "dataset": str(selected_dataset),
            "dataset_revision": dataset_revision,
            "dataset_sha256": hashlib.sha256(selected_dataset.read_bytes()).hexdigest(),
            "gold_chunks_file": str(selected_gold),
            "gold_chunks_sha256": gold_hash,
            "selection": {"start": 1, "end": limit, "query_count": limit},
            "workers": workers,
            "synthesis_node": "semigraph.agents.nodes.synthesize_node",
            "answer_audit_enabled": False,
            "latency_scope": "Synthesis only; excludes loading Gold Chunks, executor queue and YAML writes.",
        },
        "config_snapshot": {
            "llm": {
                "provider": cfg.llm_provider,
                "model": cfg.llm_model,
                "temperature": cfg.llm_temperature,
                "reasoning": cfg.llm_reasoning,
                "json_mode": cfg.llm_json_mode,
                "timeout": cfg.llm_timeout,
            },
        },
    }

    def evaluate_case(case: dict) -> dict:
        # Only the question and evidence enter the node; answer_points stay in the output.
        synthesis_input = {
            "original_query": case["query"],
            "accepted_chunks": [deepcopy(chunks[chunk_id]) for chunk_id in case["gold_chunks"]],
        }
        answer_error = None
        synthesis_trace = None
        with collect_token_usage() as usage:
            started = time.perf_counter()
            try:
                result = synthesize_node({"synthesis_input": synthesis_input}, cfg=cfg)
                final_answer = result["final_answer"]
                synthesis_trace = result["synthesis_trace"]
            except Exception as exc:
                final_answer = GENERATION_ERROR_ANSWER
                answer_error = type(exc).__name__
            answer_latency_ms = (time.perf_counter() - started) * 1000
        row = {
            "id": case["id"],
            "mode": "full_answer",
            "query": case["query"],
            "gold_chunks": case["gold_chunks"],
            "top_chunk_ids": case["gold_chunks"],
            "answer_points": case.get("answer_points", []),
            "synthesis_input": synthesis_input,
            "final_answer": final_answer,
            "answer_latency_ms": answer_latency_ms,
            "token_usage": usage.snapshot(),
            "synthesis_trace": synthesis_trace,
        }
        if answer_error:
            row["answer_error"] = answer_error
        return row

    results = []
    write_results(results, output_path, metadata)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        for row in executor.map(evaluate_case, queries):
            results.append(row)
            write_results(results, output_path, metadata)
            print(
                f"{len(results)}/{limit} {row['id']} | Gold Chunks={len(row['gold_chunks'])} | "
                f"Answer={row['answer_latency_ms']:.1f} ms | "
                f"Status={row.get('answer_error', 'ok')}",
                flush=True,
            )
    print(f"YAML results: {output_path}")
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT,
                        help="number of questions from the start of SOX74 (default: 50)")
    parser.add_argument("--workers", type=int, default=8,
                        help="number of concurrent synthesis calls (default: 8)")
    parser.add_argument("--output", type=Path,
                        help="output YAML path (default: benchmark/results2/oracle_sox_smoke50_full_answer.yaml)")
    parser.add_argument("--dataset", type=Path,
                        help="optional benchmark YAML containing queries and dataset revision")
    parser.add_argument("--gold-chunks", type=Path,
                        help="optional Gold Chunk JSONL matching the selected dataset")
    args = parser.parse_args()
    run_oracle_bench(limit=args.limit, workers=args.workers, output_path=args.output,
                     dataset_path=args.dataset, gold_chunks_path=args.gold_chunks)


if __name__ == "__main__":
    main()
