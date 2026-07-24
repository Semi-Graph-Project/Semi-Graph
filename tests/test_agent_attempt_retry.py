from copy import deepcopy

import pytest
from pydantic import ValidationError

import semigraph.agent.contracts as contracts
from semigraph.agent.contracts import AssessmentOutput
from semigraph.agent.retry_policy import (
    TOOL_RETRY_PROFILES,
    build_tool_retry_capability_summary,
    decide_retry,
    merge_coverage_and_measure_gain,
    validate_assessment_context,
)


def _accept_payload() -> dict:
    return {
        "reason": "All requirements are covered.",
        "requirement_coverage": [
            {
                "requirement_id": "R1",
                "status": "covered",
                "supporting_chunk_ids": ["chunk-10"],
            }
        ],
        "accepted_chunk_ids": ["chunk-10"],
        "decision": "accept",
        "missing_evidence": [],
    }


def _retry_payload() -> dict:
    return {
        "reason": "Revenue evidence is still missing.",
        "requirement_coverage": [
            {
                "requirement_id": "R1",
                "status": "missing",
                "supporting_chunk_ids": [],
            }
        ],
        "accepted_chunk_ids": [],
        "decision": "retry",
        "missing_evidence": ["NVDA FY2025 revenue evidence"],
        "retry_feedback": {
            "target_requirement_ids": ["R1"],
            "failure_type": "zero_results",
            "preserved_anchors": ["NVDA", "FY2025", "revenue"],
            "diagnostic_summary": "No supporting chunks were returned.",
            "retry_strategy": "anchor_enrichment",
        },
        "next_action": {
            "tool": "graph",
            "query": "NVDA FY2025 revenue",
            "top_k_chunks": 5,
        },
    }


def _stop_payload() -> dict:
    payload = _retry_payload()
    payload.update(
        decision="stop",
        stop_reason="budget_exhausted",
    )
    payload.pop("retry_feedback")
    payload.pop("next_action")
    return payload


def test_assessment_output_accepts_covered_requirements():
    payload = _accept_payload()

    assessment = AssessmentOutput.model_validate(payload)

    assert assessment.model_dump(mode="json", exclude_none=True) == payload


@pytest.mark.parametrize(
    "missing_field",
    ["retry_feedback", "next_action", "missing_evidence"],
)
def test_retry_requires_feedback_action_and_missing_evidence(missing_field):
    payload = _retry_payload()
    payload.pop(missing_field)

    with pytest.raises(ValidationError):
        AssessmentOutput.model_validate(payload)


@pytest.mark.parametrize("status", ["missing", "partial"])
def test_accept_rejects_missing_or_partial_coverage(status):
    payload = _accept_payload()
    coverage = payload["requirement_coverage"][0]
    coverage["status"] = status
    coverage["supporting_chunk_ids"] = [] if status == "missing" else ["chunk-10"]

    with pytest.raises(ValidationError):
        AssessmentOutput.model_validate(payload)


def test_stop_requires_stop_reason_and_forbids_next_action():
    without_reason = _stop_payload()
    without_reason.pop("stop_reason")

    with pytest.raises(ValidationError):
        AssessmentOutput.model_validate(without_reason)

    with_next_action = _stop_payload()
    with_next_action["next_action"] = _retry_payload()["next_action"]

    with pytest.raises(ValidationError):
        AssessmentOutput.model_validate(with_next_action)


def test_assessment_rejects_unknown_fields_and_duplicate_ids():
    with_unknown_field = _accept_payload()
    with_unknown_field["confidence"] = 1.0

    with pytest.raises(ValidationError):
        AssessmentOutput.model_validate(with_unknown_field)

    with_duplicate_accepted_ids = _accept_payload()
    with_duplicate_accepted_ids["accepted_chunk_ids"] = ["chunk-10", "chunk-10"]

    with pytest.raises(ValidationError):
        AssessmentOutput.model_validate(with_duplicate_accepted_ids)

    with_duplicate_supporting_ids = _accept_payload()
    coverage = with_duplicate_supporting_ids["requirement_coverage"][0]
    coverage["supporting_chunk_ids"] = ["chunk-10", "chunk-10"]

    with pytest.raises(ValidationError):
        AssessmentOutput.model_validate(with_duplicate_supporting_ids)

    with_duplicate_requirement_ids = _accept_payload()
    duplicate_coverage = deepcopy(
        with_duplicate_requirement_ids["requirement_coverage"][0]
    )
    with_duplicate_requirement_ids["requirement_coverage"].append(
        duplicate_coverage
    )

    with pytest.raises(ValidationError):
        AssessmentOutput.model_validate(with_duplicate_requirement_ids)

    with_duplicate_target_ids = _retry_payload()
    retry_feedback = with_duplicate_target_ids["retry_feedback"]
    retry_feedback["target_requirement_ids"] = ["R1", "R1"]

    with pytest.raises(ValidationError):
        AssessmentOutput.model_validate(with_duplicate_target_ids)


def test_agent_state_owner_declares_ticket03_fields():
    from semigraph.agent.state import AgentState

    expected_fields = {
        "attempts",
        "evidence_pool",
        "accepted_evidence",
        "requirement_coverage",
    }

    assert expected_fields <= set(AgentState.__annotations__)
    assert not hasattr(contracts, "AgentState")


def test_retry_capability_summary_is_registry_based_and_deterministic():
    summary = build_tool_retry_capability_summary(TOOL_RETRY_PROFILES)

    assert "- graph:" in summary
    assert "anchor_enrichment, bridge_hint" in summary
    assert "- vector:" in summary
    assert "focus_missing" in summary
    assert "constraint_repair" in summary
    assert "news_query_refinement" in summary
    assert "Graph does not use generic HyDE" in summary
    assert "must not add values absent from the intent" in summary
    assert "switch_tool is valid only when the next Tool is different" in summary

    assert summary == build_tool_retry_capability_summary(TOOL_RETRY_PROFILES)


def _assessment_context_payload() -> dict:
    payload = _retry_payload()
    payload["requirement_coverage"] = [
        {
            "requirement_id": "R1",
            "status": "covered",
            "supporting_chunk_ids": ["chunk-current"],
        },
        {
            "requirement_id": "R2",
            "status": "partial",
            "supporting_chunk_ids": ["chunk-previous"],
        },
    ]
    payload["accepted_chunk_ids"] = ["chunk-current"]
    payload["retry_feedback"]["target_requirement_ids"] = ["R2"]
    return payload


def _assessment_context_task() -> dict:
    return {
        "task_id": "T1",
        "requirements": [
            {"requirement_id": "R1"},
            {"requirement_id": "R2"},
        ],
    }


def test_context_validator_accepts_ids_from_allowed_context():
    assessment = AssessmentOutput.model_validate(_assessment_context_payload())

    assert validate_assessment_context(
        assessment,
        _assessment_context_task(),
        current_chunk_ids={"chunk-current"},
        previously_accepted_ids={"chunk-previous"},
    ) == []


def test_context_validator_rejects_unknown_requirement_and_chunk_ids():
    payload = _assessment_context_payload()
    payload["requirement_coverage"][0]["supporting_chunk_ids"] = ["chunk-unknown"]
    payload["accepted_chunk_ids"] = []
    payload["retry_feedback"]["target_requirement_ids"] = ["R-unknown"]
    assessment = AssessmentOutput.model_validate(payload)

    errors = validate_assessment_context(
        assessment,
        _assessment_context_task(),
        current_chunk_ids={"chunk-current"},
        previously_accepted_ids={"chunk-previous"},
    )

    assert {error["code"] for error in errors} == {
        "unknown_supporting_chunk_id",
        "unknown_retry_requirement_id",
    }


def test_context_validator_requires_exact_task_requirement_ids():
    payload = _assessment_context_payload()
    payload["requirement_coverage"].pop()
    assessment = AssessmentOutput.model_validate(payload)

    errors = validate_assessment_context(
        assessment,
        _assessment_context_task(),
        current_chunk_ids={"chunk-current"},
        previously_accepted_ids={"chunk-previous"},
    )

    assert errors[0]["code"] == "requirement_ids_mismatch"
    assert errors[0]["value"] == {"missing": ["R2"], "unexpected": []}


def test_context_validator_requires_accepted_ids_from_current_attempt():
    payload = _assessment_context_payload()
    payload["accepted_chunk_ids"] = ["chunk-previous"]
    assessment = AssessmentOutput.model_validate(payload)

    errors = validate_assessment_context(
        assessment,
        _assessment_context_task(),
        current_chunk_ids={"chunk-current"},
        previously_accepted_ids={"chunk-previous"},
    )

    assert errors[0]["code"] == "accepted_chunk_not_in_current_attempt"
    assert errors[0]["value"] == ["chunk-previous"]


def test_context_validator_requires_registered_next_tool(monkeypatch):
    payload = _assessment_context_payload()
    assessment = AssessmentOutput.model_validate(payload)
    monkeypatch.setattr(
        "semigraph.agent.retry_policy.TOOL_RETRY_PROFILES",
        {},
    )

    errors = validate_assessment_context(
        assessment,
        _assessment_context_task(),
        current_chunk_ids={"chunk-current"},
        previously_accepted_ids={"chunk-previous"},
    )

    assert errors == [
        {
            "code": "unregistered_next_tool",
            "field": "next_action.tool",
            "value": "graph",
        }
    ]


def test_status_cannot_improve_without_new_accepted_support():
    previous = {
        "R1": {
            "status": "partial",
            "supporting_chunk_ids": ["C1"],
        }
    }
    payload = _accept_payload()
    payload["requirement_coverage"][0].update(
        status="covered",
        supporting_chunk_ids=["C1"],
    )
    payload["accepted_chunk_ids"] = ["C1"]

    merged, gain = merge_coverage_and_measure_gain(
        previous,
        AssessmentOutput.model_validate(payload),
    )

    assert merged["R1"]["status"] == "partial"
    assert gain == {
        "has_gain": False,
        "improved_requirement_ids": [],
        "new_support_by_requirement": {},
    }


def test_new_accepted_support_can_improve_status():
    previous = {
        "R1": {
            "status": "partial",
            "supporting_chunk_ids": ["C1"],
        }
    }
    payload = _accept_payload()
    payload["requirement_coverage"][0].update(
        status="covered",
        supporting_chunk_ids=["C1", "C2"],
    )
    payload["accepted_chunk_ids"] = ["C2"]

    merged, gain = merge_coverage_and_measure_gain(
        previous,
        AssessmentOutput.model_validate(payload),
    )

    assert merged["R1"] == {
        "status": "covered",
        "supporting_chunk_ids": ["C1", "C2"],
    }
    assert gain == {
        "has_gain": True,
        "improved_requirement_ids": ["R1"],
        "new_support_by_requirement": {"R1": ["C2"]},
    }


def test_new_irrelevant_chunk_id_is_not_evidence_gain():
    previous = {
        "R1": {
            "status": "partial",
            "supporting_chunk_ids": ["C1"],
        }
    }
    payload = _retry_payload()
    payload["requirement_coverage"][0].update(
        status="partial",
        supporting_chunk_ids=["C1"],
    )
    payload["accepted_chunk_ids"] = []
    # C2 may exist in the raw retrieval batch, but is not accepted evidence.

    _, gain = merge_coverage_and_measure_gain(
        previous,
        AssessmentOutput.model_validate(payload),
    )

    assert gain["has_gain"] is False
    assert gain["new_support_by_requirement"] == {}


def test_coverage_merge_never_regresses_or_drops_support():
    previous = {
        "R1": {
            "status": "covered",
            "supporting_chunk_ids": ["C1"],
        }
    }
    payload = _retry_payload()
    payload["requirement_coverage"][0].update(
        status="partial",
        supporting_chunk_ids=["C2"],
    )
    payload["accepted_chunk_ids"] = ["C2"]

    merged, gain = merge_coverage_and_measure_gain(
        previous,
        AssessmentOutput.model_validate(payload),
    )

    assert merged["R1"] == {
        "status": "covered",
        "supporting_chunk_ids": ["C1", "C2"],
    }
    assert gain["has_gain"] is True
    assert gain["improved_requirement_ids"] == []


def _attempt(
    query: str,
    *,
    tool: str = "graph",
    top_k: int = 5,
    chunk_ids: list[str] | None = None,
    strategy: str | None = None,
) -> dict:
    attempt = {
        "action": {"tool": tool, "query": query, "top_k_chunks": top_k},
        "chunks": [{"chunk_id": chunk_id} for chunk_id in (chunk_ids or [])],
    }
    if strategy:
        attempt["assessment"] = {
            "retry_feedback": {"retry_strategy": strategy}
        }
    return attempt


def test_decide_retry_passes_accept_and_stop():
    accept = AssessmentOutput.model_validate(_accept_payload())
    stop = AssessmentOutput.model_validate(_stop_payload())

    assert decide_retry(accept, [], {}, 3)["decision"] == "accept"
    assert decide_retry(stop, [], {}, 3)["stop_reason"] == "budget_exhausted"


def test_decide_retry_rejects_budget_and_repeated_action():
    payload = _retry_payload()
    payload["next_action"]["query"] = "NVDA revenue"
    assessment = AssessmentOutput.model_validate(payload)
    attempt = _attempt("NVDA revenue", chunk_ids=["C1"])

    budget = decide_retry(assessment, [attempt, attempt, attempt], {}, 3)
    repeated = decide_retry(assessment, [attempt], {}, 3)

    assert budget["stop_reason"] == "budget_exhausted"
    assert repeated["stop_reason"] == "no_evidence_gain"


def test_decide_retry_rejects_zero_result_top_k_only_change():
    payload = _retry_payload()
    payload["next_action"]["query"] = "NVDA revenue"
    payload["next_action"]["top_k_chunks"] = 10
    assessment = AssessmentOutput.model_validate(payload)

    result = decide_retry(
        assessment,
        [_attempt("NVDA revenue", chunk_ids=[], top_k=5)],
        {},
        3,
    )

    assert result["reason"] == "zero_result_without_material_change"


def test_decide_retry_enforces_same_tool_profile():
    payload = _retry_payload()
    payload["next_action"]["query"] = "NVDA FY2025 margin causes"
    assessment = AssessmentOutput.model_validate(payload)
    allowed = decide_retry(
        assessment,
        [_attempt("NVDA margin", chunk_ids=[])],
        {},
        3,
    )

    payload["retry_feedback"]["retry_strategy"] = "constraint_repair"
    invalid = AssessmentOutput.model_validate(payload)
    rejected = decide_retry(
        invalid,
        [_attempt("NVDA margin", chunk_ids=[])],
        {},
        3,
    )

    assert allowed["allowed"] is True
    assert rejected["stop_reason"] == "unsupported"


def test_decide_retry_allows_registered_tool_switch():
    payload = _retry_payload()
    payload["retry_feedback"]["retry_strategy"] = "switch_tool"
    payload["next_action"].update(
        tool="vector",
        query="NVDA FY2025 margin causes",
    )
    assessment = AssessmentOutput.model_validate(payload)

    result = decide_retry(
        assessment,
        [_attempt("NVDA margin", chunk_ids=[])],
        {},
        3,
    )

    assert result["allowed"] is True
    assert result["profile"] == "vector"


def test_decide_retry_third_attempt_requires_gain_or_fallback():
    payload = _retry_payload()
    payload["next_action"]["query"] = "NVDA FY2025 margin causes"
    assessment = AssessmentOutput.model_validate(payload)
    attempts = [
        _attempt("NVDA margin", chunk_ids=["C1"]),
        _attempt("NVDA FY2025 margin", chunk_ids=["C2"]),
    ]

    rejected = decide_retry(assessment, attempts, {"has_gain": False}, 3)
    allowed_by_gain = decide_retry(assessment, attempts, {"has_gain": True}, 3)

    switch_payload = _retry_payload()
    switch_payload["retry_feedback"]["retry_strategy"] = "switch_tool"
    switch_payload["next_action"].update(
        tool="vector",
        query="NVDA FY2025 margin causes",
    )
    allowed_by_switch = decide_retry(
        AssessmentOutput.model_validate(switch_payload),
        attempts,
        {"has_gain": False},
        3,
    )

    assert rejected["stop_reason"] == "no_evidence_gain"
    assert allowed_by_gain["allowed"] is True
    assert allowed_by_switch["allowed"] is True
