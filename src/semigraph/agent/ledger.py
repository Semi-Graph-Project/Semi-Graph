"""Read-only views derived from the Attempt Ledger."""

from typing import Any


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
