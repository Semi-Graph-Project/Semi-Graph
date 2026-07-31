import re

from semigraph.agent.contracts import (
    AssessmentDecision,
    AssessmentOutput,
    RetryStrategy,
    ToolName,
)


ToolRetryProfile = frozenset[RetryStrategy]

TOOL_RETRY_PROFILES: dict[ToolName, ToolRetryProfile] = {
    ToolName.graph: frozenset({
        RetryStrategy.anchor_enrichment,
        RetryStrategy.focus_missing,
        RetryStrategy.bridge_hint,
    }),
    ToolName.vector: frozenset({RetryStrategy.focus_missing}),
    ToolName.financial: frozenset({RetryStrategy.constraint_repair}),
    ToolName.news: frozenset({RetryStrategy.news_query_refinement}),
}


def build_tool_retry_capability_summary(
    profiles: dict[ToolName, ToolRetryProfile],
) -> str:
    """Build prompt rules from the same registry used by the controller."""
    lines = ["Registered same-Tool retry strategies:"]
    for tool in sorted(profiles, key=lambda item: item.value):
        strategies = ", ".join(
            sorted(strategy.value for strategy in profiles[tool])
        )
        lines.append(f"- {tool.value}: {strategies}")

    lines.extend([
        "Retry rules:",
        "- Graph retries stay grounded in known anchors or graph bridges; "
        "Graph does not use generic HyDE.",
        "- Financial constraint_repair changes only ticker, metric, or period "
        "already present in the user intent.",
        "- Use switch_tool only when the next Tool differs and is registered.",
    ])
    return "\n".join(lines)


def validate_assessment_context(
    assessment: AssessmentOutput,
    task: dict,
    current_chunk_ids: set[str],
    locked_tool: str | None = None,
) -> list[dict]:
    """Reject only IDs or decisions that contradict the current context."""
    requirement_ids = {
        item.get("requirement_id")
        for item in task.get("requirements", [])
        if isinstance(item, dict) and item.get("requirement_id")
    }
    covered_ids = set(assessment.covered_requirement_ids)
    errors: list[dict] = []

    unknown_requirements = covered_ids - requirement_ids
    if unknown_requirements:
        errors.append({
            "code": "unknown_covered_requirement_id",
            "value": sorted(unknown_requirements),
        })

    unknown_chunks = set(assessment.accepted_chunk_ids) - current_chunk_ids
    if unknown_chunks:
        errors.append({
            "code": "accepted_chunk_not_in_current_attempt",
            "value": sorted(unknown_chunks),
        })

    if (
        assessment.decision is AssessmentDecision.accept
        and covered_ids != requirement_ids
    ):
        errors.append({
            "code": "accept_requires_all_requirements",
            "value": sorted(requirement_ids - covered_ids),
        })

    if (
        assessment.decision is AssessmentDecision.retry
        and covered_ids == requirement_ids
    ):
        errors.append({"code": "retry_requires_missing_requirement"})

    if (
        assessment.next_action is not None
        and assessment.next_action.tool not in TOOL_RETRY_PROFILES
    ):
        errors.append({
            "code": "unregistered_next_tool",
            "value": assessment.next_action.tool.value,
        })

    if (
        locked_tool
        and assessment.next_action is not None
        and assessment.next_action.tool.value != locked_tool
    ):
        errors.append({
            "code": "locked_tool_mismatch",
            "value": assessment.next_action.tool.value,
        })

    return errors


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


def _normalized_action_identity(action: dict) -> tuple[str, str, object]:
    tool = getattr(action.get("tool"), "value", action.get("tool"))
    query = re.sub(r"[^\w\s]+", " ", str(action.get("query", "")).casefold())
    return str(tool or ""), " ".join(query.split()), action.get("top_k_chunks")


def decide_retry(
    assessment: AssessmentOutput,
    attempts: list[dict],
    evidence_gain: dict,
    max_attempts: int,
) -> dict:
    """Approve an LLM proposal only when it is novel, supported and in budget."""
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
            "reason": "all_requirements_covered",
            "stop_reason": None,
            "next_action": None,
        }
    if assessment.decision is AssessmentDecision.stop:
        return stop("llm_stopped", "unsupported")

    if not attempts or assessment.next_action is None:
        return stop("invalid_retry_proposal", "unsupported")

    latest = attempts[-1]
    task_id = latest.get("task_id")
    task_attempts = [
        attempt for attempt in attempts if attempt.get("task_id") == task_id
    ]
    if len(task_attempts) >= max_attempts:
        return stop("budget_exhausted", "budget_exhausted")

    action = assessment.next_action.model_dump(mode="json")
    candidate = _normalized_action_identity(action)
    previous_actions = [
        _normalized_action_identity(attempt.get("action", {}))
        for attempt in task_attempts
    ]
    if candidate in previous_actions:
        return stop("repeated_action", "no_evidence_gain")

    latest_action = previous_actions[-1]
    latest_result_ids = {
        str(chunk["chunk_id"])
        for chunk in latest.get("chunks", [])
        if isinstance(chunk, dict) and chunk.get("chunk_id")
    }
    if (
        not latest_result_ids
        and candidate[:2] == latest_action[:2]
        and candidate[2] != latest_action[2]
    ):
        return stop("zero_result_without_material_change", "no_evidence_gain")

    same_tool = candidate[0] == latest_action[0]
    strategy = assessment.retry_strategy
    profile = TOOL_RETRY_PROFILES.get(assessment.next_action.tool)
    if profile is None:
        return stop("unregistered_next_tool", "unsupported")
    if same_tool and strategy not in profile:
        return stop("unsupported_retry_strategy", "unsupported")
    if not same_tool and strategy is not RetryStrategy.switch_tool:
        return stop("tool_switch_requires_switch_strategy", "unsupported")

    if len(task_attempts) > 1 and same_tool:
        previous_result_ids = {
            str(chunk["chunk_id"])
            for chunk in task_attempts[-2].get("chunks", [])
            if isinstance(chunk, dict) and chunk.get("chunk_id")
        }
        previous_output = (
            (task_attempts[-2].get("assessment") or {}).get("output") or {}
        )
        if (
            latest_result_ids
            and latest_result_ids == previous_result_ids
            and strategy.value == previous_output.get("retry_strategy")
        ):
            return stop("duplicate_result", "no_evidence_gain")

    if len(task_attempts) == 2 and not evidence_gain.get("has_gain", False):
        return stop("third_attempt_requires_gain", "no_evidence_gain")

    return {
        "decision": "retry",
        "allowed": True,
        "reason": "same_tool_retry" if same_tool else "tool_switch",
        "stop_reason": None,
        "next_action": action,
    }


if __name__ == "__main__":
    print(build_tool_retry_capability_summary(TOOL_RETRY_PROFILES))
