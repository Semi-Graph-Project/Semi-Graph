"""Run the 60-question Financial Agent benchmark with a NumPy vector backend.

The production Agent is reused unchanged. Inside this evaluation process only,
the ``financial`` retriever is replaced by plain cosine retrieval over the
PostgreSQL-derived financial fact corpus. Results are scored with the same gold
rows and final-answer rules as the SQL Agent benchmark.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import statistics
import time
from contextlib import redirect_stdout
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import numpy as np

from evaluate_financial_agent_e2e import (
    load_dataset,
    score_abstention,
    score_final_numbers,
    score_retrieval,
)
from evaluate_financial_vector_numpy import (
    DEFAULT_CACHE,
    DEFAULT_CORPUS,
    build_corpus,
    find_sql_summary,
    load_corpus,
    load_or_build_embeddings,
)
from semigraph.agent.graph import build_agent
from semigraph.agent.tools import RETRIEVERS
from semigraph.offline.embeddings import get_embedding_model


DEFAULT_DATASET = Path("benchmark/datasets/financial_agent_e2e_60.yaml")
DEFAULT_RESULTS_ROOT = Path("benchmark/results/financial_agent_vector_e2e")

CSV_FIELDS = (
    "id",
    "category",
    "expected_outcome",
    "query",
    "status",
    "latency_sec",
    "first_tool",
    "tool_correct",
    "retrieved_chunk_count",
    "gold_row_count",
    "retrieved_gold_count",
    "retrieval_recall",
    "retrieval_exact",
    "retrieval_precision",
    "final_gold_count",
    "final_numeric_recall",
    "final_answer_correct",
    "abstention_correct",
    "citation_count",
    "citations_valid",
    "overall_pass",
    "error_type",
    "error",
)


class NumpyFinancialAgentRetriever:
    """Agent adapter around normalized NumPy financial fact embeddings."""

    def __init__(
        self,
        *,
        corpus_path: Path,
        cache_path: Path,
        top_k: int,
        rebuild_corpus: bool,
        rebuild_embeddings: bool,
    ) -> None:
        self.corpus_path = corpus_path
        self.cache_path = cache_path
        self.top_k = top_k
        if rebuild_corpus or not corpus_path.exists():
            self.facts = build_corpus(corpus_path)
        else:
            self.facts = load_corpus(corpus_path)
        self.embeddings = load_or_build_embeddings(
            self.facts,
            corpus_path,
            cache_path,
            rebuild=rebuild_embeddings,
        )
        self.model = get_embedding_model()

    def __call__(self, query: str, top_k_chunks: int, cfg: Any) -> dict[str, Any]:
        started = time.perf_counter()
        query_vector = self.model.encode([query])[0]
        scores = self.embeddings @ query_vector
        top_k = min(self.top_k, len(self.facts))
        indices = np.argsort(-scores, kind="stable")[:top_k]
        chunks = [
            self._chunk(self.facts[index], float(scores[index]))
            for index in indices
        ]
        return {
            "chunks": chunks,
            "trace": {
                "retriever": "financial",
                "profile": "numpy_financial_fact_vector_v1",
                "parameters": {
                    "top_k_chunks": top_k,
                    "agent_requested_top_k": top_k_chunks,
                    "corpus_document_count": len(self.facts),
                    "embedding_model": cfg.embed_model,
                    "search": "normalized_numpy_dot_product",
                },
                "backend_latency_sec": round(time.perf_counter() - started, 6),
                "candidate_ranking": [
                    {
                        "chunk_id": chunk["chunk_id"],
                        "ticker": chunk["ticker"],
                        "metric": chunk["metric"],
                        "fiscal_year": chunk["fiscal_year"],
                        "score": chunk["score"],
                    }
                    for chunk in chunks
                ],
                "returned_chunk_ids": [chunk["chunk_id"] for chunk in chunks],
            },
        }

    @staticmethod
    def _chunk(fact: dict[str, Any], score: float) -> dict[str, Any]:
        provenance = dict(fact.get("provenance") or {})
        provenance["vector_document_id"] = fact["document_id"]
        provenance["source_evidence_id"] = fact["evidence_id"]
        return {
            "chunk_id": f"finvec_{fact['document_id']}",
            "text": fact["text"],
            "ticker": fact["ticker"],
            "fiscal_year": fact.get("fiscal_year"),
            "section": f"Financial_{fact['metric']}",
            "score": round(score, 8),
            "metric": fact["metric"],
            "value": fact["value"],
            "unit": fact["unit"],
            "frequency": fact["frequency"],
            "fiscal_quarter": fact.get("fiscal_quarter"),
            "period_end": fact.get("period_end"),
            "observed_at": fact.get("observed_at"),
            "status": fact.get("status", "ok"),
            "source_kind": fact["source_kind"],
            "provenance": provenance,
        }


def score_vector_case(
    case: dict[str, Any],
    state: dict[str, Any],
    latency_sec: float,
    error: Exception | None,
) -> dict[str, Any]:
    logs = list(state.get("tool_call_log") or [])
    traces = list(state.get("retrieval_trace_history") or [])
    chunks = list(state.get("chunks_history") or [])
    citations = list(state.get("citation_map") or [])
    answer = str(state.get("final_answer") or "")

    first_tool = logs[0].get("tool", "") if logs else ""
    tool_correct = first_tool == case["expected_tool"]
    chunk_ids = {str(chunk.get("chunk_id")) for chunk in chunks}
    citations_valid = bool(citations) and all(
        str(citation.get("chunk_id")) in chunk_ids for citation in citations
    )

    gold_rows = list(case.get("gold_rows") or [])
    gold_count = len(gold_rows)
    retrieved_count = 0
    retrieval_recall = 0.0
    retrieval_exact: bool | None = None
    retrieval_precision: float | None = None
    final_count = 0
    final_recall = 0.0
    final_correct: bool | None = None
    abstention_correct: bool | None = None

    if case["expected_outcome"] == "answer":
        retrieved_count, retrieval_recall, retrieval_exact = score_retrieval(
            chunks, gold_rows
        )
        retrieval_precision = retrieved_count / len(chunks) if chunks else 0.0
        tolerance = Decimal(
            str(case.get("numeric_tolerance", {}).get("final_answer_relative", 0.005))
        )
        final_count, final_recall, final_correct = score_final_numbers(
            answer, gold_rows, tolerance
        )
        overall_pass = all(
            (
                tool_correct,
                retrieval_exact,
                final_correct,
                citations_valid,
                error is None,
            )
        )
    else:
        abstention_correct = score_abstention(answer, traces)
        overall_pass = abstention_correct and error is None

    return {
        "id": case["id"],
        "category": case["category"],
        "expected_outcome": case["expected_outcome"],
        "query": case["query"],
        "status": "error" if error else "completed",
        "latency_sec": round(latency_sec, 3),
        "first_tool": first_tool,
        "tool_correct": tool_correct,
        "retrieved_chunk_count": len(chunks),
        "gold_row_count": gold_count,
        "retrieved_gold_count": retrieved_count,
        "retrieval_recall": round(retrieval_recall, 6),
        "retrieval_exact": retrieval_exact,
        "retrieval_precision": (
            round(retrieval_precision, 6)
            if retrieval_precision is not None
            else None
        ),
        "final_gold_count": final_count,
        "final_numeric_recall": round(final_recall, 6),
        "final_answer_correct": final_correct,
        "abstention_correct": abstention_correct,
        "citation_count": len(citations),
        "citations_valid": citations_valid,
        "overall_pass": bool(overall_pass),
        "error_type": type(error).__name__ if error else "",
        "error": str(error) if error else "",
        "final_answer": answer,
        "tools_used": [log.get("tool") for log in logs],
        "financial_trace_count": sum(
            trace.get("tool") == "financial" for trace in traces
        ),
    }


def _rate(rows: list[dict[str, Any]], field: str) -> float | None:
    values = [bool(row[field]) for row in rows if row.get(field) is not None]
    return round(sum(values) / len(values), 6) if values else None


def _mean(rows: list[dict[str, Any]], field: str) -> float | None:
    values = [float(row[field]) for row in rows if row.get(field) is not None]
    return round(statistics.mean(values), 6) if values else None


def build_vector_summary(
    results: list[dict[str, Any]],
    *,
    dataset: Path,
    corpus: Path,
    top_k: int,
    sql_path: Path | None,
    sql_summary: dict[str, Any] | None,
) -> dict[str, Any]:
    answerable = [row for row in results if row["expected_outcome"] == "answer"]
    unsupported = [row for row in results if row["expected_outcome"] == "abstain"]
    gold_total = sum(int(row["gold_row_count"]) for row in answerable)
    found_total = sum(int(row["retrieved_gold_count"]) for row in answerable)
    latencies = [float(row["latency_sec"]) for row in results]

    categories: dict[str, dict[str, Any]] = {}
    for category in sorted({row["category"] for row in results}):
        rows = [row for row in results if row["category"] == category]
        categories[category] = {
            "count": len(rows),
            "retrieval_exact_rate": _rate(rows, "retrieval_exact"),
            "final_answer_accuracy": _rate(rows, "final_answer_correct"),
            "abstention_accuracy": _rate(rows, "abstention_correct"),
            "overall_pass_rate": _rate(rows, "overall_pass"),
        }

    vector = {
        "tool_selection_accuracy": _rate(results, "tool_correct"),
        "retrieval_exact_rate": _rate(answerable, "retrieval_exact"),
        "retrieval_micro_recall": (
            round(found_total / gold_total, 6) if gold_total else None
        ),
        "mean_retrieval_precision": _mean(answerable, "retrieval_precision"),
        "final_answer_accuracy": _rate(answerable, "final_answer_correct"),
        "abstention_accuracy": _rate(unsupported, "abstention_correct"),
        "citation_valid_rate": _rate(answerable, "citations_valid"),
        "overall_pass_rate": _rate(results, "overall_pass"),
        "latency_sec": {
            "mean": round(statistics.mean(latencies), 3) if latencies else None,
            "median": round(statistics.median(latencies), 3) if latencies else None,
            "max": round(max(latencies), 3) if latencies else None,
        },
    }
    sql = None
    deltas = None
    if sql_summary:
        sql = {
            "source": str(sql_path),
            "tool_selection_accuracy": sql_summary.get("tool_selection_accuracy"),
            "retrieval_exact_rate": sql_summary.get("retrieval_exact_rate"),
            "retrieval_micro_recall": sql_summary.get("retrieval_micro_recall"),
            "final_answer_accuracy": sql_summary.get("final_answer_accuracy"),
            "abstention_accuracy": sql_summary.get("abstention_accuracy"),
            "citation_valid_rate": sql_summary.get("citation_valid_rate"),
            "overall_pass_rate": sql_summary.get("overall_pass_rate"),
            "latency_sec": sql_summary.get("latency_sec"),
        }
        comparable = (
            "tool_selection_accuracy",
            "retrieval_exact_rate",
            "retrieval_micro_recall",
            "final_answer_accuracy",
            "abstention_accuracy",
            "citation_valid_rate",
            "overall_pass_rate",
        )
        deltas = {
            f"sql_minus_vector_{field}": round(
                float(sql[field]) - float(vector[field]), 6
            )
            for field in comparable
            if sql.get(field) is not None and vector.get(field) is not None
        }

    return {
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "evaluation_scope": "full Agent E2E with financial backend swapped only",
        "dataset": str(dataset),
        "vector_corpus": str(corpus),
        "embedding_model": get_embedding_model().cfg.embed_model,
        "top_k": top_k,
        "query_count": len(results),
        "answerable_count": len(answerable),
        "unsupported_count": len(unsupported),
        "error_count": sum(row["status"] == "error" for row in results),
        "agent_vector": vector,
        "agent_sql_reference": sql,
        "sql_minus_vector": deltas,
        "by_category": categories,
    }


def _write_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


def write_outputs(
    output_dir: Path,
    results: list[dict[str, Any]],
    traces: list[dict[str, Any]],
    summary: dict[str, Any],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_buffer = io.StringIO()
    writer = csv.DictWriter(
        csv_buffer,
        fieldnames=CSV_FIELDS,
        extrasaction="ignore",
    )
    writer.writeheader()
    writer.writerows(results)
    _write_atomic(output_dir / "results.csv", csv_buffer.getvalue())
    _write_atomic(
        output_dir / "traces.jsonl",
        "".join(
            json.dumps(trace, ensure_ascii=False, default=str) + "\n"
            for trace in traces
        ),
    )
    _write_atomic(
        output_dir / "summary.json",
        json.dumps(summary, ensure_ascii=False, indent=2),
    )
    _write_atomic(output_dir / "report.md", _markdown_report(summary))


def _percent(value: Any) -> str:
    return "N/A" if value is None else f"{float(value) * 100:.2f}%"


def _markdown_report(summary: dict[str, Any]) -> str:
    vector = summary["agent_vector"]
    sql = summary.get("agent_sql_reference") or {}
    metrics = (
        ("Tool selection accuracy", "tool_selection_accuracy"),
        ("Retrieval exact rate", "retrieval_exact_rate"),
        ("Retrieval micro recall", "retrieval_micro_recall"),
        ("Final-answer accuracy", "final_answer_accuracy"),
        ("Abstention accuracy", "abstention_accuracy"),
        ("Citation validity", "citation_valid_rate"),
        ("Overall pass rate", "overall_pass_rate"),
    )
    rows = "\n".join(
        f"| {label} | {_percent(vector.get(field))} | {_percent(sql.get(field))} |"
        for label, field in metrics
    )
    category_rows = "\n".join(
        "| {name} | {count} | {retrieval} | {final} | {abstention} | {overall} |".format(
            name=name,
            count=values["count"],
            retrieval=_percent(values["retrieval_exact_rate"]),
            final=_percent(values["final_answer_accuracy"]),
            abstention=_percent(values["abstention_accuracy"]),
            overall=_percent(values["overall_pass_rate"]),
        )
        for name, values in summary["by_category"].items()
    )
    return f"""# Financial Agent: NumPy Vector vs SQL

Both configurations use the same Agent graph, Planner, tool name, prompts,
LLM, benchmark, and financial facts. Only the backend behind the `financial`
tool is changed.

## Overall result

| Metric | Agent + Vector | Agent + SQL |
|---|---:|---:|
{rows}

## Agent + Vector by category

| Category | N | Retrieval Exact | Final Answer | Abstention | Overall Pass |
|---|---:|---:|---:|---:|---:|
{category_rows}

## Runtime

- Agent + Vector median latency: {vector['latency_sec']['median']} seconds
- Agent + SQL median latency: {(sql.get('latency_sec') or {}).get('median')} seconds
- Vector top-k: {summary['top_k']}
- Vector corpus: `{summary['vector_corpus']}`
- SQL reference: `{sql.get('source', 'not found')}`
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--embedding-cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--sql-summary", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--recursion-limit", type=int, default=50)
    parser.add_argument("--rebuild-corpus", action="store_true")
    parser.add_argument("--rebuild-embeddings", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.top_k < 1:
        raise SystemExit("--top-k must be positive")
    if args.limit is not None and args.limit < 1:
        raise SystemExit("--limit must be positive")

    _, cases = load_dataset(args.dataset)
    cases = cases[: args.limit] if args.limit else cases
    retriever = NumpyFinancialAgentRetriever(
        corpus_path=args.corpus,
        cache_path=args.embedding_cache,
        top_k=args.top_k,
        rebuild_corpus=args.rebuild_corpus,
        rebuild_embeddings=args.rebuild_embeddings,
    )
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_dir = args.output_dir or DEFAULT_RESULTS_ROOT / timestamp
    sql_path, sql_summary = find_sql_summary(
        args.sql_summary,
        expected_query_count=len(cases),
    )

    original_financial_retriever = RETRIEVERS["financial"]
    RETRIEVERS["financial"] = retriever
    try:
        graph = build_agent()
        print(f"Writing checkpoints to: {output_dir}", flush=True)
        results: list[dict[str, Any]] = []
        traces: list[dict[str, Any]] = []
        for index, case in enumerate(cases, start=1):
            started = time.perf_counter()
            state: dict[str, Any] = {}
            error: Exception | None = None
            try:
                with redirect_stdout(io.StringIO()):
                    state = graph.invoke(
                        {"original_query": case["query"]},
                        config={"recursion_limit": args.recursion_limit},
                    )
            except Exception as exc:  # preserve checkpoints after one failure
                error = exc

            result = score_vector_case(
                case,
                state,
                time.perf_counter() - started,
                error,
            )
            results.append(result)
            traces.append(
                {
                    "id": case["id"],
                    "query": case["query"],
                    "result": result,
                    "state": state,
                }
            )
            summary = build_vector_summary(
                results,
                dataset=args.dataset,
                corpus=args.corpus,
                top_k=args.top_k,
                sql_path=sql_path,
                sql_summary=sql_summary,
            )
            write_outputs(output_dir, results, traces, summary)
            verdict = "PASS" if result["overall_pass"] else "FAIL"
            print(
                f"[{index:02d}/{len(cases):02d}] {case['id']} {verdict} "
                f"tool={result['first_tool'] or '-'} latency={result['latency_sec']}s",
                flush=True,
            )
    finally:
        RETRIEVERS["financial"] = original_financial_retriever

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Results written to: {output_dir}")


if __name__ == "__main__":
    main()
