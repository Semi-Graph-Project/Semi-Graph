"""Evaluate the SemiGraph agent on the FinReflectKG multi-hop benchmark.

The evaluator uses the production Four-Node Harness with one of three
tool-selection policies:

* agent_vector: always retrieve with the Phase T vector retriever.
* agent_graph: always retrieve with the Phase T graph retriever.
* full_agent: let PlanRoute and Assess use all registered tools.

Each run writes retrieval metrics, the final answer, agent traces, and a
RAGAS-ready JSONL file.  No RAGAS judge is called by this script.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import statistics
import sys
import time
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from semigraph.agent.graph import build_agent  # noqa: E402
from semigraph.agent.contracts import DEFAULT_TOP_K  # noqa: E402
from semigraph.agent.ledger import (  # noqa: E402
    retrieval_traces,
    retrieved_chunks,
    select_synthesis_chunks,
    tool_calls,
)
from semigraph.config import get_config  # noqa: E402


DEFAULT_DATASET = ROOT / "benchmark" / "datasets" / "finreflectkg_sox_strict74.yaml"
DEFAULT_OUTPUT_ROOT = ROOT / "benchmark" / "results" / "finreflectkg_agent"
MODES = ("agent_vector", "agent_graph", "full_agent")
CHECKPOINT_SCHEMA_VERSION = 2
RunKey = tuple[str, str]
CheckpointRecords = dict[RunKey, tuple[dict[str, Any], dict[str, Any]]]


def load_dataset(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Load and validate the shared retrieval benchmark contract."""

    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a YAML mapping")

    metadata = dict(payload.get("metadata") or {})
    queries = payload.get("queries") or []
    if not isinstance(queries, list) or not queries:
        raise ValueError(f"{path} must contain a non-empty 'queries' list")

    seen_ids: set[str] = set()
    for index, item in enumerate(queries, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Query #{index} must be a mapping")
        query_id = str(item.get("id") or "").strip()
        query = str(item.get("query") or "").strip()
        if not query_id or not query:
            raise ValueError(f"Query #{index} must have non-empty id and query")
        if query_id in seen_ids:
            raise ValueError(f"Duplicate query id: {query_id}")
        seen_ids.add(query_id)

    return metadata, queries


def build_evaluation_agent(mode: str, top_k: int):
    """Build one harness; only the ablation Tool policy differs by mode."""
    locked_tools = {
        "agent_vector": "vector",
        "agent_graph": "graph",
        "full_agent": None,
    }
    if mode not in locked_tools:
        raise ValueError(f"Unknown evaluation mode: {mode}")
    return build_agent(locked_tool=locked_tools[mode], top_k=top_k)


def _ordered_unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def chunk_ids(chunks: list[dict[str, Any]]) -> list[str]:
    return _ordered_unique([
        str(chunk.get("chunk_id") or "")
        for chunk in chunks
        if isinstance(chunk, dict)
    ])


def score_chunks(returned_ids: list[str], gold_ids: list[str]) -> dict[str, Any]:
    """Score ChunkHit, ChunkRecall, and MRR exactly as the Phase T evaluator."""

    if not gold_ids:
        return {"scored": False, "hit": None, "recall": None, "mrr": None, "hits": []}

    gold = set(gold_ids)
    hits = [chunk_id for chunk_id in returned_ids if chunk_id in gold]
    first_rank = next(
        (rank for rank, chunk_id in enumerate(returned_ids, start=1) if chunk_id in gold),
        None,
    )
    return {
        "scored": True,
        "hit": int(bool(hits)),
        "recall": len(set(hits)) / len(gold),
        "mrr": 1 / first_rank if first_rank else 0.0,
        "hits": hits,
    }


def evidence_groups(item: dict[str, Any], gold_ids: list[str]) -> dict[str, list[str]]:
    """Use explicit evidence groups, falling back to one legacy gold group."""

    raw_groups = item.get("gold_evidence_groups") or {}
    groups: dict[str, list[str]] = {}
    if isinstance(raw_groups, dict):
        for name, ids in raw_groups.items():
            if isinstance(ids, list):
                cleaned = [str(chunk_id) for chunk_id in ids if chunk_id]
                if cleaned:
                    groups[str(name)] = cleaned
    if groups:
        return groups
    return {"gold_chunks": gold_ids} if gold_ids else {}


def score_groups(
    returned_ids: list[str],
    groups: dict[str, list[str]],
) -> dict[str, Any]:
    """Score GroupRecall and Answerable using Phase T evidence semantics."""

    if not groups:
        return {"scored": False, "group_recall": None, "answerable": None, "group_hits": {}}

    returned = set(returned_ids)
    group_hits = {
        name: sorted(returned & set(ids))
        for name, ids in groups.items()
    }
    satisfied = sum(bool(hits) for hits in group_hits.values())
    return {
        "scored": True,
        "group_recall": satisfied / len(groups),
        "answerable": int(satisfied == len(groups)),
        "group_hits": group_hits,
    }


def _deduped_chunks(state: dict[str, Any]) -> list[dict[str, Any]]:
    """Derive all chronologically unique retrieved chunks from Attempts."""
    return retrieved_chunks(state.get("attempts", []) or [])


def _synthesis_chunks(state: dict[str, Any]) -> list[dict[str, Any]]:
    """Recreate the exact Attempt Ledger selection used by Synthesis."""
    return select_synthesis_chunks(
        state.get("attempts", []) or [],
        max_total=get_config().agent_max_synthesis_chunks,
    )


def _evidence_pool_chunks(state: dict[str, Any]) -> list[dict[str, Any]]:
    """Derive every accepted/fail-open chunk without adding duplicate state."""
    attempts = state.get("attempts", []) or []
    raw_count = sum(len(attempt.get("chunks") or []) for attempt in attempts)
    limit = max(1, raw_count)
    return select_synthesis_chunks(
        attempts,
        max_per_task=limit,
        max_total=limit,
    )


def _tool_call_log(state: dict[str, Any]) -> list[dict[str, Any]]:
    return tool_calls(state.get("attempts", []) or [])


def _retrieval_traces(state: dict[str, Any]) -> list[dict[str, Any]]:
    return retrieval_traces(state.get("attempts", []) or [])


def _assessment_traces(state: dict[str, Any]) -> list[dict[str, Any]]:
    traces = []
    for attempt in state.get("attempts", []) or []:
        assessment = attempt.get("assessment") or {}
        if not assessment:
            continue
        traces.append({
            "attempt_id": attempt.get("attempt_id"),
            "task_id": attempt.get("task_id"),
            "status": assessment.get("status"),
            "controller": assessment.get("controller") or {},
            "trace": assessment.get("trace") or {},
        })
    return traces


def _stage_summary(state: dict[str, Any], total_latency_sec: float) -> dict[str, Any]:
    plan_trace = state.get("plan_trace") or {}
    synthesis_trace = state.get("synthesis_trace") or {}
    assessments = _assessment_traces(state)

    plan_calls = int(plan_trace.get("llm_calls") or 0)
    assess_calls = sum(
        int(item["trace"].get("llm_calls") or 0)
        for item in assessments
    )
    synthesis_calls = int(synthesis_trace.get("llm_calls") or 0)

    plan_latency = float(plan_trace.get("latency_sec") or 0)
    retrieval_latency = sum(
        float(technical_try.get("latency_sec") or 0)
        for attempt in state.get("attempts", []) or []
        for technical_try in (
            (attempt.get("retrieval_trace") or {}).get("technical_tries") or []
        )
    )
    assess_latency = sum(
        float(item["trace"].get("latency_sec") or 0)
        for item in assessments
    )
    synthesis_latency = float(synthesis_trace.get("latency_sec") or 0)
    recorded_latency = (
        plan_latency + retrieval_latency + assess_latency + synthesis_latency
    )

    return {
        "llm_calls": {
            "plan_route": plan_calls,
            "assess": assess_calls,
            "synthesize": synthesis_calls,
            "orchestration_total": plan_calls + assess_calls + synthesis_calls,
        },
        "latency_sec": {
            "plan_route": round(plan_latency, 3),
            "retrieval": round(retrieval_latency, 3),
            "assess": round(assess_latency, 3),
            "synthesize": round(synthesis_latency, 3),
            "recorded_total": round(recorded_latency, 3),
            "unattributed": round(max(0.0, total_latency_sec - recorded_latency), 3),
        },
    }


def _context_texts(chunks: list[dict[str, Any]]) -> list[str]:
    return [
        str(chunk.get("text") or "").strip()
        for chunk in chunks
        if str(chunk.get("text") or "").strip()
    ]


def _reference_answer(item: dict[str, Any]) -> str:
    points = item.get("answer_points") or []
    if isinstance(points, list):
        return "\n".join(str(point).strip() for point in points if str(point).strip())
    return str(points).strip()


def _metric_set(
    returned_ids: list[str],
    gold_ids: list[str],
    groups: dict[str, list[str]],
) -> dict[str, Any]:
    return {**score_chunks(returned_ids, gold_ids), **score_groups(returned_ids, groups)}


def agent_state_errors(state: dict[str, Any]) -> list[str]:
    """Return retryable failures that production nodes recorded in state."""

    errors = []
    plan_trace = state.get("plan_trace") or {}
    if plan_trace.get("status") == "error":
        errors.append(f"plan: {plan_trace.get('fallback_source', 'plan_error')}")

    for attempt in state.get("attempts", []) or []:
        if attempt.get("retrieval_status") != "tool_error":
            continue
        action = attempt.get("action") or {}
        trace = attempt.get("retrieval_trace") or {}
        message = str(trace.get("error_type") or "retrieval error")
        errors.append(f"{action.get('tool', 'unknown')}: {message}")

    final_answer = str(state.get("final_answer") or "").strip()
    if not final_answer:
        errors.append("missing final answer")
    elif (state.get("synthesis_trace") or {}).get("status") == "provider_error":
        errors.append("synthesis failed")
    return list(dict.fromkeys(errors))


def result_from_state(
    item: dict[str, Any],
    mode: str,
    state: dict[str, Any],
    latency_sec: float,
    score_k: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build the detailed record and its RAGAS-ready projection."""

    all_chunks = _deduped_chunks(state)
    evidence_pool_chunks = _evidence_pool_chunks(state)
    synthesis_chunks = _synthesis_chunks(state)
    all_ids = chunk_ids(all_chunks)
    evidence_pool_ids = chunk_ids(evidence_pool_chunks)
    synthesis_ids = chunk_ids(synthesis_chunks)
    gold_ids = _ordered_unique([str(value) for value in item.get("gold_chunks", []) if value])
    groups = evidence_groups(item, gold_ids)
    tool_log = _tool_call_log(state)
    retrieval_traces = _retrieval_traces(state)
    assessment_traces = _assessment_traces(state)
    stage_summary = _stage_summary(state, latency_sec)
    called_tools = [str(entry.get("tool") or "") for entry in tool_log if entry.get("tool")]
    gold_tools = [str(tool) for tool in item.get("gold_tools", []) if tool]
    state_errors = agent_state_errors(state)
    status = "error" if state_errors else "ok"

    detail = {
        "id": str(item["id"]),
        "mode": mode,
        "type": item.get("type"),
        "query": str(item["query"]),
        "status": status,
        "latency_sec": round(latency_sec, 3),
        "score_k": score_k,
        "gold_tools": gold_tools,
        "called_tools": called_tools,
        "tool_match": int(bool(set(called_tools) & set(gold_tools))) if gold_tools else None,
        "tool_call_count": len(tool_log),
        "orchestration_llm_calls": stage_summary["llm_calls"][
            "orchestration_total"
        ],
        "unique_retrieved_count": len(all_ids),
        "evidence_pool_count": len(evidence_pool_ids),
        "synthesis_context_count": len(synthesis_ids),
        "gold_chunk_ids": gold_ids,
        "returned_chunk_ids": all_ids,
        "evidence_pool_chunk_ids": evidence_pool_ids,
        "synthesis_chunk_ids": synthesis_ids,
        "metrics_at_k": _metric_set(all_ids[:score_k], gold_ids, groups),
        "metrics_all_retrieved": _metric_set(all_ids, gold_ids, groups),
        "metrics_evidence_pool": _metric_set(evidence_pool_ids, gold_ids, groups),
        "metrics_synthesis_context": _metric_set(synthesis_ids, gold_ids, groups),
        "final_answer": str(state.get("final_answer") or ""),
        "citation_map": list(state.get("citation_map") or []),
        "tasks": list(state.get("tasks") or []),
        "completed_tasks": list(state.get("completed_tasks") or []),
        "attempts": list(state.get("attempts") or []),
        "plan_trace": dict(state.get("plan_trace") or {}),
        "synthesis_trace": dict(state.get("synthesis_trace") or {}),
        "stop_reason": state.get("stop_reason"),
        "tool_call_log": tool_log,
        "retrieval_trace_history": retrieval_traces,
        "assessment_trace_history": assessment_traces,
        "stage_summary": stage_summary,
        "error_type": "AgentStateError" if state_errors else "",
        "error": "; ".join(state_errors),
    }
    ragas = {
        "id": str(item["id"]),
        "mode": mode,
        "user_input": str(item["query"]),
        "response": detail["final_answer"],
        "retrieved_contexts": _context_texts(synthesis_chunks),
        "reference": _reference_answer(item),
        "retrieved_context_ids": synthesis_ids,
        "reference_context_ids": gold_ids,
        "status": status,
    }
    return detail, ragas


def error_result(
    item: dict[str, Any],
    mode: str,
    exc: Exception,
    latency_sec: float,
    score_k: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    gold_ids = _ordered_unique([str(value) for value in item.get("gold_chunks", []) if value])
    groups = evidence_groups(item, gold_ids)
    empty_metrics = _metric_set([], gold_ids, groups)
    detail = {
        "id": str(item["id"]),
        "mode": mode,
        "type": item.get("type"),
        "query": str(item["query"]),
        "status": "error",
        "latency_sec": round(latency_sec, 3),
        "score_k": score_k,
        "gold_tools": list(item.get("gold_tools") or []),
        "called_tools": [],
        "tool_match": None,
        "tool_call_count": 0,
        "orchestration_llm_calls": 0,
        "unique_retrieved_count": 0,
        "evidence_pool_count": 0,
        "synthesis_context_count": 0,
        "gold_chunk_ids": gold_ids,
        "returned_chunk_ids": [],
        "evidence_pool_chunk_ids": [],
        "synthesis_chunk_ids": [],
        "metrics_at_k": empty_metrics,
        "metrics_all_retrieved": empty_metrics,
        "metrics_evidence_pool": empty_metrics,
        "metrics_synthesis_context": empty_metrics,
        "final_answer": "",
        "citation_map": [],
        "tasks": [],
        "completed_tasks": [],
        "attempts": [],
        "plan_trace": {},
        "synthesis_trace": {},
        "stop_reason": "runtime_error",
        "tool_call_log": [],
        "retrieval_trace_history": [],
        "assessment_trace_history": [],
        "stage_summary": {
            "llm_calls": {
                "plan_route": 0,
                "assess": 0,
                "synthesize": 0,
                "orchestration_total": 0,
            },
            "latency_sec": {
                "plan_route": 0.0,
                "retrieval": 0.0,
                "assess": 0.0,
                "synthesize": 0.0,
                "recorded_total": 0.0,
                "unattributed": round(latency_sec, 3),
            },
        },
        "error_type": type(exc).__name__,
        "error": str(exc),
    }
    ragas = {
        "id": str(item["id"]),
        "mode": mode,
        "user_input": str(item["query"]),
        "response": "",
        "retrieved_contexts": [],
        "reference": _reference_answer(item),
        "retrieved_context_ids": [],
        "reference_context_ids": gold_ids,
        "status": "error",
    }
    return detail, ragas


def _mean(rows: list[dict[str, Any]], path: tuple[str, ...]) -> float:
    values: list[float] = []
    for row in rows:
        value: Any = row
        for key in path:
            value = value.get(key) if isinstance(value, dict) else None
        if value is not None:
            values.append(float(value))
    return statistics.fmean(values) if values else 0.0


def aggregate_results(rows: list[dict[str, Any]], modes: list[str]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for mode in modes:
        selected = [row for row in rows if row["mode"] == mode]
        successful = [row for row in selected if row["status"] == "ok"]
        summary[mode] = {
            "queries": len(selected),
            "successful": len(successful),
            "errors": len(selected) - len(successful),
            "chunk_hit_at_k": _mean(selected, ("metrics_at_k", "hit")),
            "chunk_recall_at_k": _mean(selected, ("metrics_at_k", "recall")),
            "group_recall_at_k": _mean(selected, ("metrics_at_k", "group_recall")),
            "answerable_at_k": _mean(selected, ("metrics_at_k", "answerable")),
            "chunk_hit_all": _mean(selected, ("metrics_all_retrieved", "hit")),
            "chunk_recall_all": _mean(selected, ("metrics_all_retrieved", "recall")),
            "group_recall_all": _mean(selected, ("metrics_all_retrieved", "group_recall")),
            "answerable_all": _mean(selected, ("metrics_all_retrieved", "answerable")),
            "synthesis_chunk_hit": _mean(selected, ("metrics_synthesis_context", "hit")),
            "synthesis_chunk_recall": _mean(selected, ("metrics_synthesis_context", "recall")),
            "synthesis_group_recall": _mean(selected, ("metrics_synthesis_context", "group_recall")),
            "synthesis_answerable": _mean(selected, ("metrics_synthesis_context", "answerable")),
            "avg_latency_sec": _mean(successful, ("latency_sec",)),
            "avg_tool_calls": _mean(successful, ("tool_call_count",)),
            "avg_orchestration_llm_calls": _mean(
                successful,
                ("orchestration_llm_calls",),
            ),
            "avg_unique_retrieved": _mean(successful, ("unique_retrieved_count",)),
        }
    return summary


def _json_text(value: Any, *, indent: int | None = None) -> str:
    return json.dumps(value, ensure_ascii=False, default=str, indent=indent)


def _atomic_write(path: Path, content: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    content = "\n".join(_json_text(row) for row in rows)
    _atomic_write(path, content + ("\n" if content else ""))


def dataset_sha256(path: Path) -> str:
    """Return a stable fingerprint used to reject unsafe resume attempts."""

    return hashlib.sha256(path.read_bytes()).hexdigest()


def result_key(row: dict[str, Any]) -> RunKey:
    query_id = str(row.get("id") or "").strip()
    mode = str(row.get("mode") or "").strip()
    if not query_id or not mode:
        raise ValueError("Checkpoint record must contain non-empty id and mode")
    return query_id, mode


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {path}:{line_number}: {exc}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"Checkpoint row {path}:{line_number} must be an object")
        rows.append(row)
    return rows


def _index_unique_rows(rows: list[dict[str, Any]], label: str) -> dict[RunKey, dict[str, Any]]:
    indexed: dict[RunKey, dict[str, Any]] = {}
    for row in rows:
        key = result_key(row)
        if key in indexed:
            raise ValueError(f"Duplicate {label} checkpoint key: {key}")
        indexed[key] = row
    return indexed


def load_checkpoint(run_dir: Path) -> CheckpointRecords:
    """Load the canonical checkpoint, or migrate legacy paired outputs."""

    checkpoint_path = run_dir / "checkpoint.jsonl"
    if checkpoint_path.exists():
        records: CheckpointRecords = {}
        for payload in _read_jsonl(checkpoint_path):
            if payload.get("schema_version") != CHECKPOINT_SCHEMA_VERSION:
                raise ValueError(
                    "Unsupported checkpoint schema version: "
                    f"{payload.get('schema_version')!r}"
                )
            detail = payload.get("detail")
            ragas = payload.get("ragas")
            if not isinstance(detail, dict) or not isinstance(ragas, dict):
                raise ValueError("Canonical checkpoint rows require detail and ragas objects")
            key = result_key(detail)
            if result_key(ragas) != key:
                raise ValueError(f"Detail/RAGAS checkpoint key mismatch: {key}")
            if key in records:
                raise ValueError(f"Duplicate canonical checkpoint key: {key}")
            records[key] = (detail, ragas)
        return records

    details_path = run_dir / "details.jsonl"
    ragas_path = run_dir / "ragas.jsonl"
    if not details_path.exists() and not ragas_path.exists():
        return {}
    if not details_path.exists() or not ragas_path.exists():
        raise ValueError(
            "Legacy resume requires both details.jsonl and ragas.jsonl"
        )

    details = _index_unique_rows(_read_jsonl(details_path), "detail")
    ragas_rows = _index_unique_rows(_read_jsonl(ragas_path), "RAGAS")
    if set(details) != set(ragas_rows):
        raise ValueError("Legacy detail and RAGAS checkpoint keys do not match")
    return {key: (details[key], ragas_rows[key]) for key in details}


def ordered_checkpoint_rows(
    records: CheckpointRecords,
    planned_keys: list[RunKey],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    details: list[dict[str, Any]] = []
    ragas_rows: list[dict[str, Any]] = []
    for key in planned_keys:
        pair = records.get(key)
        if pair is None:
            continue
        detail, ragas = pair
        details.append(detail)
        ragas_rows.append(ragas)
    return details, ragas_rows


def write_checkpoint(
    run_dir: Path,
    records: CheckpointRecords,
    planned_keys: list[RunKey],
    modes: list[str],
    score_k: int,
) -> dict[str, Any]:
    """Atomically commit canonical state, then refresh every derived report."""

    details, ragas_rows = ordered_checkpoint_rows(records, planned_keys)
    canonical_rows = [
        {
            "schema_version": CHECKPOINT_SCHEMA_VERSION,
            "key": {"id": detail["id"], "mode": detail["mode"]},
            "detail": detail,
            "ragas": ragas,
        }
        for detail, ragas in zip(details, ragas_rows)
    ]

    # This is the transaction boundary. Derived files can always be rebuilt
    # from this atomically replaced canonical snapshot after an interruption.
    write_jsonl(run_dir / "checkpoint.jsonl", canonical_rows)
    write_jsonl(run_dir / "details.jsonl", details)
    write_jsonl(run_dir / "ragas.jsonl", ragas_rows)

    summary = aggregate_results(details, modes)
    _atomic_write(run_dir / "summary.json", _json_text(summary, indent=2) + "\n")
    write_summary_markdown(run_dir / "summary.md", summary, score_k)

    successful = sum(row.get("status") == "ok" for row in details)
    retryable = len(details) - successful
    progress = {
        "total_units": len(planned_keys),
        "completed_units": successful,
        "retryable_units": retryable,
        "pending_units": len(planned_keys) - len(details),
        "updated_at": datetime.now().astimezone().isoformat(),
    }
    _atomic_write(run_dir / "progress.json", _json_text(progress, indent=2) + "\n")
    return summary


def validate_resume_config(
    existing: dict[str, Any],
    expected: dict[str, Any],
) -> None:
    """Fail closed when a resume request would mix experiment contracts."""

    comparable_fields = (
        "agent_harness",
        "dataset",
        "dataset_sha256",
        "modes",
        "selected_query_ids",
        "query_count",
        "agent_run_count",
        "top_k_per_tool_call",
        "score_k",
        "recursion_limit",
    )
    mismatches = [
        field
        for field in comparable_fields
        if existing.get(field) != expected.get(field)
    ]
    if mismatches:
        raise ValueError(
            "Resume configuration mismatch: " + ", ".join(mismatches)
        )


def write_summary_markdown(
    path: Path,
    summary: dict[str, Any],
    score_k: int,
) -> None:
    lines = [
        "# FinReflectKG Agent Evaluation",
        "",
        (
            f"| Mode | Queries | Errors | Hit@{score_k} | Recall@{score_k} | "
            f"GroupRecall@{score_k} | Answerable@{score_k} | Hit@All | "
            "Recall@All | Synthesis GroupRecall | Avg Tool Calls | "
            "Avg Agent LLM Calls | Avg Latency |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for mode, row in summary.items():
        lines.append(
            f"| {mode} | {row['queries']} | {row['errors']} | "
            f"{row['chunk_hit_at_k']:.3f} | {row['chunk_recall_at_k']:.3f} | "
            f"{row['group_recall_at_k']:.3f} | {row['answerable_at_k']:.3f} | "
            f"{row['chunk_hit_all']:.3f} | {row['chunk_recall_all']:.3f} | "
            f"{row['synthesis_group_recall']:.3f} | {row['avg_tool_calls']:.2f} | "
            f"{row['avg_orchestration_llm_calls']:.2f} | "
            f"{row['avg_latency_sec']:.2f}s |"
        )
    _atomic_write(path, "\n".join(lines) + "\n")


def run_agent(
    graph,
    query: str,
    recursion_limit: int,
    verbose_agent: bool,
) -> dict[str, Any]:
    if verbose_agent:
        return graph.invoke(
            {"original_query": query},
            config={"recursion_limit": recursion_limit},
        )

    captured = io.StringIO()
    with redirect_stdout(captured):
        return graph.invoke(
            {"original_query": query},
            config={"recursion_limit": recursion_limit},
        )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate Agent+Vector, Agent+Graph, and the full autonomous Agent "
            "on FinReflectKG while preserving final answers for RAGAS."
        )
    )
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--modes", nargs="+", choices=MODES, default=list(MODES))
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    parser.add_argument(
        "--score-k",
        type=int,
        default=DEFAULT_TOP_K,
        help="Number of chronologically unique chunks used for Phase T-style @K metrics.",
    )
    parser.add_argument("--recursion-limit", type=int, default=50)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument(
        "--query-id",
        action="append",
        default=[],
        help="Run only this query id; repeat the flag for multiple ids.",
    )
    parser.add_argument("--run-name", default=None)
    parser.add_argument(
        "--resume",
        action="store_true",
        help=(
            "Resume --run-name, skip successful (query id, mode) units, and "
            "retry incomplete or failed units."
        ),
    )
    parser.add_argument("--verbose-agent", action="store_true")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate inputs and print the run matrix without calling external services.",
    )
    args = parser.parse_args()
    if args.top_k <= 0 or args.score_k <= 0:
        parser.error("--top-k and --score-k must be positive")
    if args.recursion_limit <= 0:
        parser.error("--recursion-limit must be positive")
    if args.limit is not None and args.limit <= 0:
        parser.error("--limit must be positive")
    if args.resume and not args.run_name:
        parser.error("--resume requires --run-name")
    return args


def main() -> None:
    args = _parse_args()
    dataset_metadata, queries = load_dataset(args.dataset)

    if args.query_id:
        requested = set(args.query_id)
        queries = [item for item in queries if str(item["id"]) in requested]
        missing = sorted(requested - {str(item["id"]) for item in queries})
        if missing:
            raise ValueError(f"Unknown query id(s): {', '.join(missing)}")
    if args.limit is not None:
        queries = queries[: args.limit]

    run_matrix_size = len(queries) * len(args.modes)
    print(f"Dataset: {args.dataset}")
    print(f"Queries: {len(queries)}")
    print(f"Modes: {', '.join(args.modes)}")
    print(f"Agent runs: {run_matrix_size}")
    print(f"Retriever top-k per call: {args.top_k}; score-k: {args.score_k}")
    if args.dry_run:
        print("Dry run complete: dataset and arguments are valid; no Agent was called.")
        return

    selected_query_ids = [str(item["id"]) for item in queries]
    planned_keys = [
        (query_id, mode)
        for query_id in selected_query_ids
        for mode in args.modes
    ]
    contract = {
        "agent_harness": "four_node_v1",
        "dataset": str(args.dataset.resolve()),
        "dataset_sha256": dataset_sha256(args.dataset),
        "dataset_metadata": dataset_metadata,
        "modes": list(args.modes),
        "selected_query_ids": selected_query_ids,
        "query_count": len(queries),
        "agent_run_count": run_matrix_size,
        "top_k_per_tool_call": args.top_k,
        "score_k": args.score_k,
        "recursion_limit": args.recursion_limit,
        "created_at": datetime.now().astimezone().isoformat(),
        "ragas_contract": {
            "question": "user_input",
            "answer": "response",
            "contexts": "retrieved_contexts",
            "ground_truth": "reference",
        },
    }

    stamp = args.run_name or datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = args.output_root / stamp
    if args.resume:
        if not run_dir.is_dir():
            raise FileNotFoundError(f"Resume run directory does not exist: {run_dir}")
        config_path = run_dir / "run_config.json"
        if not config_path.exists():
            raise FileNotFoundError(f"Resume run_config.json is missing: {config_path}")
        existing_config = json.loads(config_path.read_text(encoding="utf-8"))
        validate_resume_config(existing_config, contract)
        records = load_checkpoint(run_dir)
        unexpected_keys = sorted(set(records) - set(planned_keys))
        if unexpected_keys:
            raise ValueError(
                "Checkpoint contains units outside the requested run: "
                + ", ".join(f"{query_id}/{mode}" for query_id, mode in unexpected_keys)
            )
        run_config = {**existing_config, **contract}
        run_config["resume_count"] = int(existing_config.get("resume_count", 0)) + 1
        run_config["last_resumed_at"] = datetime.now().astimezone().isoformat()
        print(f"Resuming checkpoint: {run_dir}")
    else:
        run_dir.mkdir(parents=True, exist_ok=False)
        records: CheckpointRecords = {}
        run_config = {
            **contract,
            "checkpoint_schema_version": CHECKPOINT_SCHEMA_VERSION,
            "created_at": datetime.now().astimezone().isoformat(),
            "resume_count": 0,
        }

    _atomic_write(run_dir / "run_config.json", _json_text(run_config, indent=2) + "\n")
    summary = write_checkpoint(
        run_dir,
        records,
        planned_keys,
        list(args.modes),
        args.score_k,
    )

    successful_keys = {
        key
        for key, (detail, _) in records.items()
        if detail.get("status") == "ok"
    }
    if args.resume:
        print(
            f"Checkpoint loaded: {len(successful_keys)} complete, "
            f"{len(records) - len(successful_keys)} retryable, "
            f"{len(planned_keys) - len(records)} pending"
        )

    graphs = {
        mode: build_evaluation_agent(mode, args.top_k)
        for mode in args.modes
    }
    position = 0
    for item in queries:
        for mode in args.modes:
            position += 1
            key = (str(item["id"]), mode)
            previous = records.get(key)
            if previous and previous[0].get("status") == "ok":
                print(
                    f"[{position}/{run_matrix_size}] SKIP {item['id']} {mode}",
                    flush=True,
                )
                continue

            action = "RETRY" if previous else "RUN"
            print(
                f"[{position}/{run_matrix_size}] {action} {item['id']} {mode}",
                flush=True,
            )
            started = time.perf_counter()
            try:
                state = run_agent(
                    graphs[mode],
                    str(item["query"]),
                    args.recursion_limit,
                    args.verbose_agent,
                )
                detail, ragas = result_from_state(
                    item,
                    mode,
                    state,
                    time.perf_counter() - started,
                    args.score_k,
                )
            except Exception as exc:
                detail, ragas = error_result(
                    item,
                    mode,
                    exc,
                    time.perf_counter() - started,
                    args.score_k,
                )
                print(f"  ERROR {type(exc).__name__}: {exc}", flush=True)

            records[key] = (detail, ragas)
            summary = write_checkpoint(
                run_dir,
                records,
                planned_keys,
                list(args.modes),
                args.score_k,
            )

    print(f"Completed. Results: {run_dir}")
    for mode, row in summary.items():
        print(
            f"{mode}: errors={row['errors']} "
            f"hit@{args.score_k}={row['chunk_hit_at_k']:.3f} "
            f"recall@{args.score_k}={row['chunk_recall_at_k']:.3f} "
            f"group_recall_all={row['group_recall_all']:.3f}"
        )
    retryable_count = sum(
        detail.get("status") != "ok"
        for detail, _ in records.values()
    )
    if retryable_count:
        print(
            f"Retryable units: {retryable_count}. Re-run the same command with --resume."
        )


if __name__ == "__main__":
    main()
