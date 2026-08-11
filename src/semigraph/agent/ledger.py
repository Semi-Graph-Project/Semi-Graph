"""Read-only views derived from the Attempt Ledger."""

import json
from typing import Any

from semigraph.agent.state import TaskWorkerState
from semigraph.config import Config


def retrieved_chunks(attempts: list[dict]) -> list[dict[str, Any]]:
    """Return unique raw chunks in retrieval order."""
    chunks = []
    seen_ids: set[str] = set()
    for attempt in attempts:
        for chunk in attempt.get("chunks", []) or []:
            chunk_id = str(chunk.get("chunk_id") or "")
            if not chunk_id or chunk_id in seen_ids:
                continue
            chunks.append(chunk)
            seen_ids.add(chunk_id)
    return chunks


def tool_calls(attempts: list[dict]) -> list[dict[str, Any]]:
    """Return one compact Tool-call row per Attempt."""
    return [
        {
            "attempt_id": attempt.get("attempt_id"),
            "task_id": attempt.get("task_id"),
            "tool": (attempt.get("action") or {}).get("tool"),
            "query": (attempt.get("action") or {}).get("query"),
            "top_k_chunks": (attempt.get("action") or {}).get("top_k_chunks"),
            "n_chunks": len(attempt.get("chunks") or []),
            "status": attempt.get("retrieval_status"),
        }
        for attempt in attempts
    ]


def retrieval_traces(attempts: list[dict]) -> list[dict[str, Any]]:
    """Return Retriever traces with their Attempt and action identity."""
    traces = []
    for attempt in attempts:
        action = attempt.get("action") or {}
        traces.append({
            "attempt_id": attempt.get("attempt_id"),
            "task_id": attempt.get("task_id"),
            "tool": action.get("tool"),
            "query": action.get("query"),
            "retrieval_status": attempt.get("retrieval_status"),
            **(attempt.get("retrieval_trace") or {}),
        })
    return traces


def select_synthesis_chunks(
    attempts: list[dict],
    max_per_task: int = 3,
    max_total: int = 10,
) -> list[dict]:
    """Return prioritized, unique raw chunks ready for Synthesis."""
    if max_per_task < 1 or max_total < 1:
        raise ValueError("Synthesis chunk limits must be positive")

    attempts_by_task: dict[str, list[dict]] = {}
    for attempt in attempts:
        task_id = attempt.get("task_id")
        if task_id:
            attempts_by_task.setdefault(task_id, []).append(attempt)
    # print("=== select_synthesis_chunks: attempts_by_task ===")
    # print("type = ", type(attempts_by_task))
    # for task_id, task_attempts in attempts_by_task.items():
    #     print(f"Task ID: {task_id}, Attempts: {task_attempts}\n\n")
    # print("=== Raw attempts by task ===")
    # print(attempts_by_task)

    accepted: dict[str, list[dict]] = {}
    fallback: dict[str, list[dict]] = {}

    for task_id, task_attempts in attempts_by_task.items():
        accepted[task_id] = []
        fallback[task_id] = []
        seen_task_ids: set[str] = set()

        for attempt in reversed(task_attempts):
            assessment = attempt.get("assessment") or {}
            if assessment.get("status") not in {"valid", "repaired"}:
                continue
            output = assessment.get("output") or {}
            accepted_ids = set(output.get("accepted_chunk_ids") or [])
            for chunk in attempt.get("chunks") or []:
                chunk_id = chunk.get("chunk_id")
                if chunk_id in accepted_ids and chunk_id not in seen_task_ids:
                    accepted[task_id].append(chunk)
                    seen_task_ids.add(chunk_id)

        # Prefer the first two results from every Attempt, then use remaining
        # ranks only when the global synthesis budget still has room.
        for attempt in reversed(task_attempts):
            for chunk in (attempt.get("chunks") or [])[:2]:
                chunk_id = chunk.get("chunk_id")
                if chunk_id and chunk_id not in seen_task_ids:
                    fallback[task_id].append(chunk)
                    seen_task_ids.add(chunk_id)

        for attempt in reversed(task_attempts):
            for chunk in (attempt.get("chunks") or [])[2:]:
                chunk_id = chunk.get("chunk_id")
                if chunk_id and chunk_id not in seen_task_ids:
                    fallback[task_id].append(chunk)
                    seen_task_ids.add(chunk_id)

    def fair_order(queues: dict[str, list[dict]]) -> list[dict]:
        ordered = [
            chunk
            for task_id in attempts_by_task
            for chunk in queues[task_id][:max_per_task]
        ]
        longest = max((len(queue) for queue in queues.values()), default=0)
        ordered.extend(
            queues[task_id][index]
            for index in range(max_per_task, longest)
            for task_id in attempts_by_task
            if index < len(queues[task_id])
        )
        return ordered

    selected: list[dict] = []
    seen_ids: set[str] = set()
    candidates = [*fair_order(accepted), *fair_order(fallback)]
    for chunk in candidates:
        chunk_id = chunk.get("chunk_id")
        if not chunk_id or chunk_id in seen_ids:
            continue
        selected.append(chunk)
        seen_ids.add(chunk_id)
        if len(selected) == max_total:
            break

    return selected


def _chunk_preview(
    chunk: dict,
    text_limit: int | None = None,
) -> dict:
    """Return Assess-facing chunk data without mutating the raw chunk."""
    if text_limit is not None and text_limit < 0:
        raise ValueError("text_limit must be non-negative")

    metadata_fields = (
        "chunk_id",
        "rank",
        "original_rank",
        "score",
        "rerank_score",
        "ticker",
        "fiscal_year",
        "fiscal_quarter",
        "period_end",
        "section",
        "metric",
        "value",
        "unit",
        "frequency",
        "source_kind",
        "published_at",
        "source_url",
    )
    preview = {
        field: chunk[field]
        for field in metadata_fields
        if chunk.get(field) is not None
    }
    text = str(chunk.get("text") or "")
    preview["text"] = text if text_limit is None else text[:text_limit]
    return preview


def _compact_assess_diagnostics(trace: dict) -> dict:
    """Keep only retrieval diagnostics that help Assess make a decision."""
    fields = (
        "status",
        "reason",
        "abort_reason",
        "returned_chunk_ids",
        "seed_count",
        "candidate_count",
        "error_type",
    )
    diagnostics = {
        field: trace[field]
        for field in fields
        if trace.get(field) is not None
    }

    seeds = [item for item in trace.get("seeds", []) if isinstance(item, dict)]
    if seeds:
        diagnostics["seeds"] = seeds[:5]

    triple_filter = trace.get("triple_filter")
    if isinstance(triple_filter, dict):
        selected_triples = [
            item
            for item in triple_filter.get("selected_triples", [])
            if isinstance(item, dict)
        ][:5]
        compact_filter = {
            "reason": triple_filter.get("reason"),
            "selected_triples": selected_triples,
        }
        diagnostics["triple_filter"] = {
            field: value
            for field, value in compact_filter.items()
            if value is not None
        }

    return diagnostics


def build_assess_context(state: TaskWorkerState, cfg: Config) -> str:
    """Derive a bounded Assess view from the Attempt Ledger."""
    current_task = state["task"]
    task_id = current_task["task_id"]
    task_attempts = [
        attempt
        for attempt in (state.get("attempts") or [])
        if isinstance(attempt, dict) and attempt.get("task_id") == task_id
    ]
    latest_attempt = task_attempts[-1] if task_attempts else {}
    latest_chunks = [
        _chunk_preview(chunk)
        for chunk in (latest_attempt.get("chunks") or [])
        if isinstance(chunk, dict)
    ]
    accepted_ids: set[str] = set()
    covered_ids: set[str] = set()
    for attempt in task_attempts[:-1]:
        assessment = attempt.get("assessment") or {}
        output = assessment.get("output") or {}
        accepted_ids.update(output.get("accepted_chunk_ids", []))
        covered_ids.update(output.get("covered_requirement_ids", []))
        if assessment.get("status") == "fail_open":
            accepted_ids.update(
                chunk.get("chunk_id")
                for chunk in attempt.get("chunks", [])
                if isinstance(chunk, dict) and chunk.get("chunk_id")
            )

    accepted_evidence = [
        chunk
        for attempt in task_attempts[:-1]
        for chunk in attempt.get("chunks", [])
        if isinstance(chunk, dict) and chunk.get("chunk_id") in accepted_ids
    ][-9:]
    prior_attempts = [
        {
            "attempt_id": attempt.get("attempt_id"),
            "action": attempt.get("action"),
            "retrieval_status": attempt.get("retrieval_status"),
            "accepted_chunk_ids": (
                ((attempt.get("assessment") or {}).get("output") or {}).get(
                    "accepted_chunk_ids", []
                )
            ),
            "returned_chunk_ids": [
                chunk.get("chunk_id")
                for chunk in (attempt.get("chunks") or [])
                if isinstance(chunk, dict) and chunk.get("chunk_id")
            ],
        }
        for attempt in task_attempts[:-1]
    ]

    context = {
        "original_query": state.get("original_query", ""),
        "current_task": current_task,
        "current_action": latest_attempt.get("action")
        or state.get("current_action", {}),
        "latest_chunks": latest_chunks,
        "covered_requirement_ids": sorted(covered_ids),
        "accepted_evidence": [
            _chunk_preview(chunk, text_limit=240)
            for chunk in accepted_evidence
        ],
        "prior_attempts": prior_attempts,
        "latest_diagnostics": _compact_assess_diagnostics(
            latest_attempt.get("retrieval_trace", {})
            if isinstance(latest_attempt.get("retrieval_trace"), dict)
            else {}
        ),
    }

    max_chars = cfg.agent_assess_context_max_chars
    serialized = json.dumps(context, ensure_ascii=False, separators=(",", ":"))

    while len(serialized) > max_chars and context["prior_attempts"]:
        context["prior_attempts"].pop(0)
        serialized = json.dumps(
            context, ensure_ascii=False, separators=(",", ":")
        )

    while len(serialized) > max_chars and context["accepted_evidence"]:
        context["accepted_evidence"].pop(0)
        serialized = json.dumps(
            context, ensure_ascii=False, separators=(",", ":")
        )

    while len(serialized) > max_chars:
        for chunk in reversed(context["latest_chunks"]):
            text = chunk.get("text", "")
            if text:
                excess = len(serialized) - max_chars
                chunk["text"] = text[: max(0, len(text) - max(1, excess))]
                break
        else:
            raise ValueError("Required Assess context exceeds configured limit")
        serialized = json.dumps(
            context, ensure_ascii=False, separators=(",", ":")
        )

    return serialized


def _workbench() -> None:
    """Show the Synthesis chunk policy with a small mock Attempt Ledger."""
    attempts = [
        {
            "attempt_id": "T1-A1",
            "task_id": "T1",
            "chunks": [
                {"chunk_id": "C1", "text": "T1 older accepted evidence"},
                {"chunk_id": "C2", "text": "T1 older duplicate evidence"},
                {"chunk_id": "C5", "text": "T1 lower-rank fallback"},
            ],
            "assessment": {
                "status": "valid",
                "output": {"accepted_chunk_ids": ["C1", "C2"]},
            },
        },
        {
            "attempt_id": "T1-A2",
            "task_id": "T1",
            "chunks": [
                {"chunk_id": "C2", "text": "T1 newer retry evidence"},
                {"chunk_id": "C3", "text": "T1 new accepted evidence"},
                {"chunk_id": "C4", "text": "T1 retry fallback"},
            ],
            "assessment": {
                "status": "repaired",
                "output": {"accepted_chunk_ids": ["C2", "C3"]},
            },
        },
        {
            "attempt_id": "T2-A1",
            "task_id": "T2",
            "chunks": [
                {"chunk_id": "C6", "text": "T2 accepted evidence"},
                {"chunk_id": "C7", "text": "T2 fallback evidence"},
                {"chunk_id": "C8", "text": "T2 lower-rank fallback"},
            ],
            "assessment": {
                "status": "valid",
                "output": {"accepted_chunk_ids": ["C6"]},
            },
        },
        {
            "attempt_id": "T2-A2",
            "task_id": "T2",
            "chunks": [
                {"chunk_id": "C9", "text": "T2 fail-open fallback"},
                {"chunk_id": "C10", "text": "T2 fail-open fallback 2"},
            ],
            "assessment": {"status": "fail_open", "output": None},
        },
        {
            "attempt_id": "T3-A1",
            "task_id": "T3",
            "chunks": [
                {"chunk_id": "C11", "text": "T3 fallback 1"},
                {"chunk_id": "C12", "text": "T3 fallback 2"},
                {"chunk_id": "C13", "text": "T3 fallback 3"},
            ],
            "assessment": {"status": "fail_open", "output": None},
        },
    ]

    selected = select_synthesis_chunks(attempts)
    selected_ids = [chunk["chunk_id"] for chunk in selected]

    print("=== Mock Attempt Ledger ===")
    for attempt in attempts:
        chunk_ids = [chunk["chunk_id"] for chunk in attempt["chunks"]]
        assessment = attempt["assessment"]
        accepted_ids = (assessment.get("output") or {}).get(
            "accepted_chunk_ids", []
        )
        print(
            f"{attempt['attempt_id']}: status={assessment['status']}, "
            f"chunks={chunk_ids}, accepted={accepted_ids}"
        )

    print("\n=== select_synthesis_chunks(attempts) ===")
    print("Policy: accepted first → fair per Task → unique IDs → max_total=10")
    print(f"Selected ({len(selected_ids)}): {selected_ids}")
    print("C2 is the newer retry chunk; C12/C13 are outside the global budget.")


if __name__ == "__main__":
    _workbench()
