"""Run and score the Financial Agent E2E benchmark."""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import statistics
import time
from contextlib import redirect_stdout
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import yaml

from semigraph.agent.graph import build_agent


DEFAULT_DATASET = Path("benchmark/datasets/financial_agent_e2e_60.yaml")
DEFAULT_RESULTS_ROOT = Path("benchmark/results/financial_agent_e2e")

ABSTENTION_PHRASES = (
    "not enough evidence",
    "insufficient",
    "not sufficient",
    "cannot answer",
    "cannot directly",
    "cannot be directly answered",
    "cannot be made",
    "can't answer",
    "unable to answer",
    "do not have enough",
    "not available",
    "not directly provided",
    "does not contain",
    "does not include",
    "not supported",
    "unsupported",
    "no evidence",
)
VALUE_PATTERN = re.compile(
    r"(?P<sign_before>[+-]?)\s*(?P<currency>\$)?\s*(?P<sign_after>[+-]?)"
    r"(?P<number>\d[\d,]*(?:\.\d+)?)"
    r"\s*(?P<scale>trillion|billion|million|thousand|[TBMK])?"
    r"\s*(?P<percent>%|percent)?",
    re.IGNORECASE,
)
NEGATIVE_CUE_PATTERN = re.compile(
    r"(?:\b(?:decline|decrease|loss)\s+(?:of|by)|"
    r"\b(?:down|dropped|fell)\s+by|\bnegative)\s*$",
    re.IGNORECASE,
)
SCALES = {
    "k": Decimal("1000"),
    "thousand": Decimal("1000"),
    "m": Decimal("1000000"),
    "million": Decimal("1000000"),
    "b": Decimal("1000000000"),
    "billion": Decimal("1000000000"),
    "t": Decimal("1000000000000"),
    "trillion": Decimal("1000000000000"),
}
NUMERIC_TEXT_TRANSLATION = str.maketrans({
    "\u2212": "-",  # mathematical minus used by some LLM responses
    "\uff0d": "-",  # full-width minus
    "\u00a0": " ",  # no-break space
    "\u202f": " ",  # narrow no-break space
})
CSV_FIELDS = (
    "id",
    "category",
    "expected_outcome",
    "query",
    "status",
    "latency_sec",
    "first_tool",
    "tool_correct",
    "spec_correct",
    "spec_match_mode",
    "sql_success",
    "gold_row_count",
    "retrieved_gold_count",
    "retrieval_recall",
    "retrieval_exact",
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


def load_dataset(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    metadata = dict(data.get("metadata") or {})
    queries = list(data.get("queries") or [])
    if not queries:
        raise ValueError(f"No benchmark queries found in {path}")
    return metadata, queries


def successful_financial_traces(
    traces: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return financial attempts that reached the backend and returned rows."""

    return [
        trace
        for trace in traces
        if trace.get("tool") == "financial"
        and trace.get("status") not in {"error", "skipped"}
        and int(trace.get("returned_count") or 0) > 0
    ]


def specs_match(
    actual: dict[str, Any],
    expected: dict[str, Any],
    fields: list[str],
) -> bool:
    if not actual:
        return False
    for field in fields:
        actual_value = actual.get(field)
        expected_value = expected.get(field)
        if field in {"tickers", "metrics"}:
            if set(actual_value or []) != set(expected_value or []):
                return False
        elif actual_value != expected_value:
            return False
    return True


def score_query_specs(
    traces: list[dict[str, Any]],
    expected: dict[str, Any],
    fields: list[str],
    expected_template_id: str,
) -> tuple[bool, str]:
    """Score an exact spec or an equivalent decomposed lookup plan."""

    successful = successful_financial_traces(traces)
    for trace in successful:
        actual = dict(trace.get("query_spec") or {})
        template_id = (trace.get("parameters") or {}).get("template_id")
        if specs_match(actual, expected, fields) and template_id == expected_template_id:
            return True, "exact"

    specs = [dict(trace.get("query_spec") or {}) for trace in successful]
    if not specs or expected.get("operation") not in {"compare", "trend"}:
        return False, ""

    compatible_operations = {
        "compare": {"compare", "lookup"},
        "trend": {"trend", "lookup"},
    }[expected["operation"]]
    if any(spec.get("operation") not in compatible_operations for spec in specs):
        return False, ""

    combined_tickers = {
        ticker
        for spec in specs
        for ticker in (spec.get("tickers") or [])
    }
    combined_metrics = {
        metric
        for spec in specs
        for metric in (spec.get("metrics") or [])
    }
    if combined_tickers != set(expected.get("tickers") or []):
        return False, ""
    if combined_metrics != set(expected.get("metrics") or []):
        return False, ""

    scalar_fields = {"frequency", "quarter", "aggregation"} & set(fields)
    if any(
        any(spec.get(field) != expected.get(field) for spec in specs)
        for field in scalar_fields
    ):
        return False, ""

    def endpoint_matches(field: str, reducer) -> bool:
        values = [spec.get(field) for spec in specs]
        expected_value = expected.get(field)
        if expected_value is None:
            return all(value is None for value in values)
        if any(value is None for value in values):
            return False
        return reducer(values) == expected_value

    if "start_year" in fields and not endpoint_matches("start_year", min):
        return False, ""
    if "end_year" in fields and not endpoint_matches("end_year", max):
        return False, ""
    return True, "decomposed"


def _decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value).replace(",", ""))
    except (InvalidOperation, ValueError):
        return None


def score_retrieval(
    chunks: list[dict[str, Any]],
    gold_rows: list[dict[str, Any]],
) -> tuple[int, float, bool]:
    found = 0
    for gold in gold_rows:
        gold_value = _decimal(gold.get("value"))
        matched = any(
            chunk.get("ticker") == gold.get("ticker")
            and chunk.get("metric") == gold.get("metric")
            and chunk.get("frequency") == gold.get("frequency")
            and chunk.get("fiscal_year") == gold.get("fiscal_year")
            and chunk.get("period_end") == gold.get("period_end")
            and _decimal(chunk.get("value")) == gold_value
            and str(chunk.get("unit", "")).lower()
            == str(gold.get("unit", "")).lower()
            for chunk in chunks
        )
        found += int(matched)
    total = len(gold_rows)
    recall = found / total if total else 0.0
    return found, recall, found == total and total > 0


def numeric_candidates(text: str) -> list[Decimal]:
    text = text.translate(NUMERIC_TEXT_TRANSLATION)
    values: list[Decimal] = []
    for match in VALUE_PATTERN.finditer(text):
        value = _decimal(match.group("number"))
        if value is None:
            continue
        explicit_negative = "-" in {
            match.group("sign_before"),
            match.group("sign_after"),
        }
        preceding_text = text[max(0, match.start() - 48):match.start()]
        if explicit_negative or NEGATIVE_CUE_PATTERN.search(preceding_text):
            value = -value
        scale = (match.group("scale") or "").lower()
        percent = bool(match.group("percent"))
        currency = bool(match.group("currency"))
        if scale:
            value *= SCALES[scale]
        if percent:
            value /= Decimal("100")
        if not (currency or scale or percent) and value == value.to_integral():
            if Decimal("1900") <= value <= Decimal("2100"):
                continue  # fiscal years and dates are context, not answers
        values.append(value)
    return values


def score_final_numbers(
    answer: str,
    gold_rows: list[dict[str, Any]],
    relative_tolerance: Decimal,
) -> tuple[int, float, bool]:
    candidates = numeric_candidates(answer)
    used: set[int] = set()
    matched = 0
    for gold in gold_rows:
        expected = _decimal(gold.get("value"))
        if expected is None:
            continue
        tolerance = max(abs(expected) * relative_tolerance, Decimal("0.000001"))
        for index, candidate in enumerate(candidates):
            if index not in used and abs(candidate - expected) <= tolerance:
                used.add(index)
                matched += 1
                break
    total = len(gold_rows)
    recall = matched / total if total else 0.0
    return matched, recall, matched == total and total > 0


def score_abstention(
    answer: str,
    traces: list[dict[str, Any]],
) -> bool:
    """Require a user-visible refusal; numeric context may still be cited."""

    lowered = answer.lower()
    has_text_refusal = any(phrase in lowered for phrase in ABSTENTION_PHRASES)
    has_structured_refusal = any(
        trace.get("tool") == "financial"
        and trace.get("reason") in {"unsupported_metric", "no_corpus_ticker"}
        for trace in traces
    )
    return has_text_refusal or (has_structured_refusal and not answer.strip())


def score_case(
    case: dict[str, Any],
    state: dict[str, Any],
    latency_sec: float,
    critical_fields: list[str],
    error: Exception | None,
) -> dict[str, Any]:
    logs = list(state.get("tool_call_log") or [])
    traces = list(state.get("retrieval_trace_history") or [])
    chunks = list(state.get("chunks_history") or [])
    citations = list(state.get("citation_map") or [])
    answer = str(state.get("final_answer") or "")

    first_tool = logs[0].get("tool", "") if logs else ""
    tool_correct = first_tool == case["expected_tool"]
    expected_spec = case.get("gold_spec")

    spec_correct: bool | None = None
    spec_match_mode = ""
    sql_success: bool | None = None
    retrieval_exact: bool | None = None
    final_answer_correct: bool | None = None
    abstention_correct: bool | None = None
    gold_count = len(case.get("gold_rows") or [])
    retrieved_count = 0
    retrieval_recall = 0.0
    final_count = 0
    final_recall = 0.0

    chunk_ids = {str(chunk.get("chunk_id")) for chunk in chunks}
    citations_valid = bool(citations) and all(
        str(citation.get("chunk_id")) in chunk_ids for citation in citations
    )

    if case["expected_outcome"] == "answer":
        spec_correct, spec_match_mode = score_query_specs(
            traces,
            expected_spec,
            critical_fields,
            case["expected_template_id"],
        )
        sql_success = bool(successful_financial_traces(traces))
        retrieved_count, retrieval_recall, retrieval_exact = score_retrieval(
            chunks, case["gold_rows"]
        )
        tolerance = Decimal(
            str(case.get("numeric_tolerance", {}).get("final_answer_relative", 0.005))
        )
        final_count, final_recall, final_answer_correct = score_final_numbers(
            answer, case["gold_rows"], tolerance
        )
        overall_pass = all(
            (
                tool_correct,
                spec_correct,
                sql_success,
                retrieval_exact,
                final_answer_correct,
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
        "spec_correct": spec_correct,
        "spec_match_mode": spec_match_mode,
        "sql_success": sql_success,
        "gold_row_count": gold_count,
        "retrieved_gold_count": retrieved_count,
        "retrieval_recall": round(retrieval_recall, 6),
        "retrieval_exact": retrieval_exact,
        "final_gold_count": final_count,
        "final_numeric_recall": round(final_recall, 6),
        "final_answer_correct": final_answer_correct,
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


def _rate(results: list[dict[str, Any]], field: str) -> float | None:
    values = [row[field] for row in results if row.get(field) is not None]
    return round(sum(bool(value) for value in values) / len(values), 6) if values else None


def build_summary(
    results: list[dict[str, Any]],
    dataset: Path,
) -> dict[str, Any]:
    answerable = [row for row in results if row["expected_outcome"] == "answer"]
    unsupported = [row for row in results if row["expected_outcome"] == "abstain"]
    gold_total = sum(row["gold_row_count"] for row in answerable)
    retrieved_total = sum(row["retrieved_gold_count"] for row in answerable)
    latencies = [float(row["latency_sec"]) for row in results]

    categories: dict[str, dict[str, Any]] = {}
    for category in sorted({row["category"] for row in results}):
        rows = [row for row in results if row["category"] == category]
        categories[category] = {
            "count": len(rows),
            "overall_pass_rate": _rate(rows, "overall_pass"),
        }

    return {
        "dataset": str(dataset),
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "query_count": len(results),
        "answerable_count": len(answerable),
        "unsupported_count": len(unsupported),
        "error_count": sum(row["status"] == "error" for row in results),
        "tool_selection_accuracy": _rate(results, "tool_correct"),
        "query_spec_accuracy": _rate(answerable, "spec_correct"),
        "sql_execution_success_rate": _rate(answerable, "sql_success"),
        "retrieval_exact_rate": _rate(answerable, "retrieval_exact"),
        "retrieval_micro_recall": (
            round(retrieved_total / gold_total, 6) if gold_total else None
        ),
        "final_answer_accuracy": _rate(answerable, "final_answer_correct"),
        "abstention_accuracy": _rate(unsupported, "abstention_correct"),
        "citation_valid_rate": _rate(answerable, "citations_valid"),
        "overall_pass_rate": _rate(results, "overall_pass"),
        "latency_sec": {
            "mean": round(statistics.mean(latencies), 3) if latencies else None,
            "median": round(statistics.median(latencies), 3) if latencies else None,
            "max": round(max(latencies), 3) if latencies else None,
        },
        "by_category": categories,
    }


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

    trace_text = "".join(
        json.dumps(trace, ensure_ascii=False, default=str) + "\n"
        for trace in traces
    )
    _write_atomic(output_dir / "traces.jsonl", trace_text)
    _write_atomic(
        output_dir / "summary.json",
        json.dumps(summary, ensure_ascii=False, indent=2),
    )


def _write_atomic(path: Path, content: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--recursion-limit", type=int, default=50)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.limit is not None and args.limit < 1:
        raise SystemExit("--limit must be positive")

    metadata, cases = load_dataset(args.dataset)
    cases = cases[: args.limit] if args.limit else cases
    critical_fields = list(metadata.get("critical_spec_fields") or [])
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_dir = args.output_dir or DEFAULT_RESULTS_ROOT / timestamp
    graph = build_agent()
    print(f"Writing checkpoints to: {output_dir}", flush=True)

    results: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []
    summary: dict[str, Any] = {}
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
        except Exception as exc:  # keep the remaining benchmark runnable
            error = exc

        result = score_case(
            case,
            state,
            time.perf_counter() - started,
            critical_fields,
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
        summary = build_summary(results, args.dataset)
        write_outputs(output_dir, results, traces, summary)
        verdict = "PASS" if result["overall_pass"] else "FAIL"
        print(
            f"[{index:02d}/{len(cases):02d}] {case['id']} {verdict} "
            f"tool={result['first_tool'] or '-'} latency={result['latency_sec']}s",
            flush=True,
        )

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"Results written to: {output_dir}")


if __name__ == "__main__":
    main()
