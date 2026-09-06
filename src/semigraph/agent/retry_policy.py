import re

from semigraph.agent.contracts import AssessmentDecision, AssessmentOutput


def validate_assessment_context(
    assessment: AssessmentOutput,
    current_chunk_ids: set[str],
) -> list[dict]:
    """Reject chunk IDs that were not returned by the latest retrieval."""
    unknown_ids = set(assessment.accepted_chunk_ids) - current_chunk_ids
    if not unknown_ids:
        return []
    return [{
        "code": "accepted_chunk_not_in_current_attempt",
        "value": sorted(unknown_ids),
    }]


def measure_evidence_gain(
    assessment: AssessmentOutput,
    attempts: list[dict],
) -> dict:
    """Count only newly accepted evidence as progress."""
    task_id = attempts[-1].get("task_id") if attempts else None
    previous_ids = {
        chunk_id
        for attempt in attempts[:-1]
        if attempt.get("task_id") == task_id
        for chunk_id in (
            ((attempt.get("assessment") or {}).get("output") or {}).get(
                "accepted_chunk_ids", []
            )
        )
    }
    new_ids = sorted(set(assessment.accepted_chunk_ids) - previous_ids)
    return {
        "has_gain": bool(new_ids),
        "new_accepted_chunk_ids": new_ids,
    }


def _normalized_query(query: str) -> str:
    text = re.sub(r"[^\w\s]+", " ", query.casefold())
    return " ".join(text.split())


def decide_retry(
    assessment: AssessmentOutput,
    attempts: list[dict],
    evidence_gain: dict,
    max_attempts: int,
    tool: str,
    cfg,
) -> dict:
    """Approve a fixed-Tool retry only when its query is new and in budget."""
    def stop(reason: str, stop_reason: str) -> dict:
        return {
            "decision": "stop",
            "allowed": False,
            "reason": reason,
            "stop_reason": stop_reason,
            "next_action": None,
        }

    if assessment.decision is AssessmentDecision.accept:
        return {
            "decision": "accept",
            "allowed": False,
            "reason": "requirement_covered",
            "stop_reason": None,
            "next_action": None,
        }
    if assessment.decision is AssessmentDecision.stop:
        return stop("llm_stopped", "unsupported")
    if not attempts or assessment.retry_query is None:
        return stop("invalid_retry_proposal", "unsupported")

    task_id = attempts[-1].get("task_id")
    task_attempts = [
        attempt for attempt in attempts if attempt.get("task_id") == task_id
    ]
    if len(task_attempts) >= max_attempts:
        return stop("budget_exhausted", "budget_exhausted")

    retry_query = assessment.retry_query
    previous_queries = {
        _normalized_query(str((attempt.get("action") or {}).get("query", "")))
        for attempt in task_attempts
    }
    if _normalized_query(retry_query) in previous_queries:
        return stop("repeated_query", "no_evidence_gain")

    if len(task_attempts) == 2 and not evidence_gain.get("has_gain", False):
        return stop("third_attempt_requires_gain", "no_evidence_gain")

    top_k = cfg.agent_top_k_chunks
    return {
        "decision": "retry",
        "allowed": True,
        "reason": "new_query",
        "stop_reason": None,
        "next_action": {
            "tool": tool,
            "query": retry_query,
            "top_k_chunks": top_k,
        },
    }
