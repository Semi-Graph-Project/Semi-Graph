


import re
from typing import TypedDict
from semigraph.agent.contracts import (
    AssessmentOutput,
    AssessmentDecision,
    CoverageStatus,
    FailureType,
    RetryStrategy,
    ToolName,
)


class ToolRetryProfile(TypedDict):
    same_tool_strategies: dict[FailureType, frozenset[RetryStrategy]]


TOOL_RETRY_PROFILES: dict[ToolName, ToolRetryProfile] = {
    ToolName.graph: {
        "same_tool_strategies": {
            FailureType.zero_results: frozenset(
                {RetryStrategy.anchor_enrichment, RetryStrategy.bridge_hint}
            ),
            FailureType.partial_coverage: frozenset(
                {RetryStrategy.focus_missing, RetryStrategy.bridge_hint}
            ),
            FailureType.irrelevant_results: frozenset(
                {RetryStrategy.anchor_enrichment, RetryStrategy.focus_missing}
            ),
            FailureType.duplicate_results: frozenset(
                {RetryStrategy.focus_missing, RetryStrategy.bridge_hint}
            ),
        }
    },
    ToolName.vector: {
        "same_tool_strategies": {
            failure_type: frozenset({RetryStrategy.focus_missing})
            for failure_type in (
                FailureType.zero_results,
                FailureType.partial_coverage,
                FailureType.irrelevant_results,
                FailureType.duplicate_results,
            )
        }
    },
    ToolName.financial: {
        "same_tool_strategies": {
            failure_type: frozenset({RetryStrategy.constraint_repair})
            for failure_type in (
                FailureType.zero_results,
                FailureType.partial_coverage,
                FailureType.irrelevant_results,
                FailureType.duplicate_results,
            )
        }
    },
    ToolName.news: {
        "same_tool_strategies": {
            failure_type: frozenset({RetryStrategy.news_query_refinement})
            for failure_type in (
                FailureType.zero_results,
                FailureType.partial_coverage,
                FailureType.irrelevant_results,
                FailureType.duplicate_results,
            )
        }
    },
}


def build_tool_retry_capability_summary(
    profiles: dict[ToolName, ToolRetryProfile],
) -> str:
    """Build deterministic, prompt-facing retry rules from the registry."""
    summary_lines = ["Registered retry capabilities:"]

    for tool in sorted(profiles, key=lambda item: item.value):
        summary_lines.append(f"- {tool.value}:")
        profile = profiles[tool]
        strategies_by_failure = profile["same_tool_strategies"]

        for failure_type in sorted(
            strategies_by_failure,
            key=lambda item: item.value,
        ):
            strategies = strategies_by_failure[failure_type]
            strategy_list = ", ".join(
                sorted(strategy.value for strategy in strategies)
            )
            summary_lines.append(
                f"  - {failure_type.value}: {strategy_list}"
            )

    summary_lines.extend(
        [
            "Retry rules:",
            "- Graph retry must stay grounded in known anchors or graph bridges; "
            "Graph does not use generic HyDE.",
            "- Financial constraint_repair may adjust only ticker, metric, or "
            "period grounded in the user intent; it must not add values absent "
            "from the intent.",
            "- switch_tool is valid only when the next Tool is different and "
            "that Tool has a registered retry profile.",
        ]
    )
    return "\n".join(summary_lines)


def validate_assessment_context(
    assessment: AssessmentOutput,
    task: dict,
    current_chunk_ids: set[str],
    previously_accepted_ids: set[str],
) -> list[dict]:
    """Return deterministic errors for IDs and retry tools outside context."""
    task_requirement_ids = {
        item["requirement_id"]
        for item in task.get("requirements", [])
    }
    task_requirement_ids.discard(None)

    coverage_ids = {
        coverage.requirement_id
        for coverage in assessment.requirement_coverage
    }
    errors: list[dict] = []

    if coverage_ids != task_requirement_ids:
        errors.append(
            {
                "code": "requirement_ids_mismatch",
                "field": "requirement_coverage",
                "value": {
                    "missing": sorted(task_requirement_ids - coverage_ids),
                    "unexpected": sorted(coverage_ids - task_requirement_ids),
                },
            }
        )

    available_chunk_ids = set(current_chunk_ids) | set(previously_accepted_ids)
    current_chunk_ids = set(current_chunk_ids)

    for index, coverage in enumerate(assessment.requirement_coverage):
        unknown_ids = set(coverage.supporting_chunk_ids) - available_chunk_ids
        # if Chunk is never retrieved, it cannot be used to support a requirement, even if it was accepted in a previous attempt
        if unknown_ids:
            errors.append(
                {
                    "code": "unknown_supporting_chunk_id",
                    "field": (
                        f"requirement_coverage[{index}].supporting_chunk_ids"
                    ),
                    "value": sorted(unknown_ids),
                }
            )

    accepted_outside_current = (
        set(assessment.accepted_chunk_ids) - current_chunk_ids
    )
    if accepted_outside_current:
        errors.append(
            {
                "code": "accepted_chunk_not_in_current_attempt",
                "field": "accepted_chunk_ids",
                "value": sorted(accepted_outside_current),
            }
        )

    if assessment.retry_feedback is not None:
        unknown_targets = (
            set(assessment.retry_feedback.target_requirement_ids)
            - task_requirement_ids
        )
        if unknown_targets:
            errors.append(
                {
                    "code": "unknown_retry_requirement_id",
                    "field": "retry_feedback.target_requirement_ids",
                    "value": sorted(unknown_targets),
                }
            )

    if assessment.next_action is not None:
        next_tool = assessment.next_action.tool
        if next_tool not in TOOL_RETRY_PROFILES:
            errors.append(
                {
                    "code": "unregistered_next_tool",
                    "field": "next_action.tool",
                    "value": next_tool.value,
                }
            )

    return errors


_COVERAGE_RANK = {
    CoverageStatus.missing: 0,
    CoverageStatus.partial: 1,
    CoverageStatus.covered: 2,
}

def merge_coverage_and_measure_gain(
    previous: dict[str, dict],
    assessment: AssessmentOutput,
) -> tuple[dict[str, dict], dict]:
    merged: dict[str, dict] = {}
    improved_ids: list[str] = []
    new_support: dict[str, list[str]] = {}
    accepted_ids = set(assessment.accepted_chunk_ids)

    for coverage in assessment.requirement_coverage:
        requirement_id = coverage.requirement_id
        old = previous.get(requirement_id, {})
        previous_status = CoverageStatus(
            old.get("status", CoverageStatus.missing)
        )
        previous_support = old.get("supporting_chunk_ids", [])
        current_support = coverage.supporting_chunk_ids
        added_support = sorted(
            (set(current_support) & accepted_ids)
            - set(previous_support)
        )
        status_improved = bool(added_support) and (
            _COVERAGE_RANK[coverage.status]
            > _COVERAGE_RANK[previous_status]
        )

        if added_support:
            new_support[requirement_id] = added_support
        if status_improved:
            improved_ids.append(requirement_id)

        merged[requirement_id] = {
            "status": (
                coverage.status if status_improved else previous_status
            ).value,
            "supporting_chunk_ids": list(
                dict.fromkeys([*previous_support, *current_support])
            ),
        }

    return merged, {
        "has_gain": bool(new_support),
        "improved_requirement_ids": improved_ids,
        "new_support_by_requirement": new_support,
    }


def _normalized_action_identity(action: dict) -> tuple[str, str, object]:
    """
    Normalize the action identity by extracting and cleaning relevant fields.
    input: example action dictionary
    output: tuple of (tool, normalized_query, top_k_chunks)
    """
    tool = getattr(action.get("tool"), "value", action.get("tool"))
    query = re.sub(r"[^\w\s]+", " ", str(action.get("query", "")).casefold())
    return str(tool or ""), " ".join(query.split()), action.get("top_k_chunks")


def _result_id_set(attempt: dict) -> set[str]:
    return {
        str(chunk["chunk_id"])
        for chunk in attempt.get("chunks", [])
        if isinstance(chunk, dict) and chunk.get("chunk_id")
    }


def _attempt_retry_strategy(attempt: dict) -> RetryStrategy | None:
    assessment = attempt.get("assessment") or {}
    output = assessment.get("output", assessment)
    feedback = output.get("retry_feedback") if isinstance(output, dict) else None
    value = feedback.get("retry_strategy") if isinstance(feedback, dict) else None
    return RetryStrategy(value) if value else None


def decide_retry(
    assessment: AssessmentOutput,
    attempts: list[dict],
    evidence_gain: dict,
    max_attempts: int,
) -> dict:
    """Approve a validated retry proposal without calling external services."""
    def stop(reason: str, stop_reason: str) -> dict:
        return {
            "decision": "stop",
            "allowed": False,
            "reason": reason,
            "stop_reason": stop_reason,
            "next_action": None,
            "warnings": [],
            "profile": None,
        }

    if assessment.decision is not AssessmentDecision.retry:
        return {
            "decision": assessment.decision.value,
            "allowed": False,
            "reason": assessment.reason,
            "stop_reason": (
                assessment.stop_reason.value
                if assessment.stop_reason is not None
                else None
            ),
            "next_action": None,
            "warnings": [],
            "profile": None,
        }

    if len(attempts) >= max_attempts:
        return stop("budget_exhausted", "budget_exhausted")

    feedback = assessment.retry_feedback
    next_action = assessment.next_action
    if feedback is None or next_action is None or not attempts:
        return stop("invalid_retry_proposal", "unsupported")

    action = next_action.model_dump(mode="json")
    candidate_identity = _normalized_action_identity(action)
    previous_identities = [
        _normalized_action_identity(attempt.get("action", {}))
        for attempt in attempts
    ]
    if candidate_identity in previous_identities:
        return stop("repeated_action", "no_evidence_gain")

    latest = attempts[-1]
    latest_identity = _normalized_action_identity(latest.get("action", {}))
    if (
        not _result_id_set(latest)
        and candidate_identity[:2] == latest_identity[:2]
        and candidate_identity[2] != latest_identity[2]
    ):
        return stop("zero_result_without_material_change", "no_evidence_gain")

    if len(attempts) > 1 and _result_id_set(latest):
        duplicate_results = _result_id_set(attempts[-2]) == _result_id_set(latest)
        same_tool = candidate_identity[0] == latest_identity[0]
        same_strategy = feedback.retry_strategy is _attempt_retry_strategy(latest)
        if duplicate_results and same_tool and same_strategy:
            return stop("duplicate_result", "no_evidence_gain")

    next_tool = next_action.tool
    profile = TOOL_RETRY_PROFILES.get(next_tool)
    if profile is None:
        return stop("unregistered_next_tool", "unsupported")

    same_tool = candidate_identity[0] == latest_identity[0]
    if same_tool:
        allowed = profile["same_tool_strategies"].get(
            feedback.failure_type,
            frozenset(),
        )
        if feedback.retry_strategy not in allowed:
            return stop("unsupported_retry_strategy", "unsupported")
    elif feedback.retry_strategy is not RetryStrategy.switch_tool:
        return stop("tool_switch_requires_switch_strategy", "unsupported")

    if len(attempts) + 1 == 3 and not evidence_gain.get("has_gain", False):
        adapted_same_tool = (
            len(attempts) > 1
            and _normalized_action_identity(attempts[-1].get("action", {}))[0]
            == _normalized_action_identity(attempts[-2].get("action", {}))[0]
        )
        if same_tool or not adapted_same_tool:
            return stop(
                "third_attempt_requires_gain_or_fallback",
                "no_evidence_gain",
            )

    return {
        "decision": "retry",
        "allowed": True,
        "reason": "tool_switch" if not same_tool else "same_tool_retry",
        "stop_reason": None,
        "next_action": action,
        "warnings": [],
        "profile": next_tool.value,
    }


if __name__ == "__main__":
    print(build_tool_retry_capability_summary(TOOL_RETRY_PROFILES))
