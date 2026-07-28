import json
from copy import deepcopy
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

import semigraph.agent.contracts as contracts
import semigraph.agent.nodes as nodes
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


def test_assess_prompt_matches_contract_and_retry_profiles():
    from semigraph.agent.prompts import ASSESS_SYSTEM_PROMPT

    contract_models = (
        contracts.AssessmentOutput,
        contracts.RequirementCoverage,
        contracts.RetryFeedback,
        contracts.RetrievalAction,
    )
    contract_enums = (
        contracts.CoverageStatus,
        contracts.AssessmentDecision,
        contracts.FailureType,
        contracts.RetryStrategy,
        contracts.AssessmentStopReason,
        contracts.ToolName,
    )

    for model in contract_models:
        for field_name in model.model_fields:
            assert f'"{field_name}"' in ASSESS_SYSTEM_PROMPT

    for enum in contract_enums:
        for member in enum:
            assert member.value in ASSESS_SYSTEM_PROMPT

    capability_summary = build_tool_retry_capability_summary(
        TOOL_RETRY_PROFILES
    )
    assert capability_summary in ASSESS_SYSTEM_PROMPT
    assert "hybrid" not in ASSESS_SYSTEM_PROMPT.casefold()
    assert "does not use generic HyDE" in ASSESS_SYSTEM_PROMPT


def _working_context_state() -> dict:
    return {
        "original_query": "How does NVDA depend on TSMC in FY2025?",
        "tasks": [
            {
                "task_id": "T1",
                "query": "NVDA TSMC dependency FY2025",
                "requirements": [
                    {
                        "requirement_id": "R1",
                        "description": "Evidence connecting NVDA to TSMC",
                    }
                ],
            }
        ],
        "current_task_index": 0,
        "current_action": {
            "tool": "graph",
            "query": "NVDA TSMC dependency FY2025",
            "top_k_chunks": 5,
        },
        "requirement_coverage": {},
        "accepted_evidence": [],
        "attempts": [
            {
                "attempt_id": "T1-A1",
                "task_id": "T1",
                "action": {
                    "tool": "graph",
                    "query": "NVDA TSMC dependency FY2025",
                    "top_k_chunks": 5,
                },
                "retrieval_status": "ok",
                "chunks": [
                    {
                        "chunk_id": "C1",
                        "rank": 1,
                        "text": "NVDA relies on TSMC for manufacturing.",
                    }
                ],
                "retrieval_trace": {
                    "abort_reason": "insufficient_bridge",
                    "seed_count": 6,
                    "seeds": [
                        {"name": f"seed-{index}"}
                        for index in range(6)
                    ],
                    "triple_filter": {
                        "reason": "bridge candidates selected",
                        "selected_triples": [
                            {"candidate_id": f"T{index}"}
                            for index in range(6)
                        ],
                    },
                    "candidate_count": 20,
                    "candidate_ranking": ["large-ranking"],
                    "projection": {"name": "large-projection"},
                },
                "assessment": None,
            }
        ],
    }


def test_working_context_contains_latest_chunks_and_compact_diagnostics():
    context = nodes._build_assess_context(
        _working_context_state(),
        SimpleNamespace(agent_assess_context_max_chars=60_000),
    )
    payload = json.loads(context)
    diagnostics = payload["latest_diagnostics"]

    assert "NVDA" in context
    assert "TSMC" in context
    assert "FY2025" in context
    assert payload["latest_chunks"][0]["text"] == (
        "NVDA relies on TSMC for manufacturing."
    )
    assert diagnostics["abort_reason"] == "insufficient_bridge"
    assert diagnostics["seed_count"] == 6
    assert len(diagnostics["seeds"]) == 5
    assert diagnostics["triple_filter"]["reason"] == (
        "bridge candidates selected"
    )
    assert len(diagnostics["triple_filter"]["selected_triples"]) == 5
    assert diagnostics["candidate_count"] == 20
    assert "candidate_ranking" not in diagnostics
    assert "projection" not in diagnostics


def test_working_context_excludes_full_prior_raw_chunks_and_is_bounded():
    state = _working_context_state()
    old_text = "OLD_START-" + ("x" * 2_000) + "-OLD_SECRET_TAIL"
    old_attempt = deepcopy(state["attempts"][0])
    old_attempt.update(
        attempt_id="T1-A0",
        chunks=[{"chunk_id": "C0", "text": old_text}],
    )
    state["attempts"].insert(0, old_attempt)
    state["accepted_evidence"] = [{"chunk_id": "C0", "text": old_text}]
    state["attempts"][-1]["chunks"][0]["text"] = "latest " * 1_000
    cfg = SimpleNamespace(agent_assess_context_max_chars=2_000)

    context = nodes._build_assess_context(state, cfg)

    assert len(context) <= cfg.agent_assess_context_max_chars
    assert "OLD_SECRET_TAIL" not in context
    assert old_text not in context


def test_assessment_parser_rejects_extra_or_malformed_output():
    with pytest.raises(json.JSONDecodeError):
        nodes._parse_assessment_response("{not valid JSON")

    payload = _accept_payload()
    payload["unknown_field"] = "not allowed"
    with pytest.raises(ValidationError):
        nodes._parse_assessment_response(json.dumps(payload))


def test_normalized_errors_never_contain_raw_model_output():
    secret = "RAW_MODEL_SECRET_MARKER"
    try:
        nodes._parse_assessment_response(f'{{"reason": "{secret}"}}')
    except ValidationError as error:
        normalized = nodes._normalize_assessment_error(error)
    else:
        raise AssertionError("Invalid assessment unexpectedly passed")

    assert secret not in json.dumps(normalized)
    assert all(set(item) <= {"code", "loc", "type"} for item in normalized)


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


def _execute_state(
    *,
    attempts: list[dict] | None = None,
    evidence_pool: list[dict] | None = None,
) -> dict:
    return {
        "tasks": [{"task_id": "T1"}],
        "current_task_index": 0,
        "current_action": {
            "tool": "graph",
            "query": "NVDA FY2024 operating risk",
            "top_k_chunks": 5,
        },
        "attempts": attempts or [],
        "evidence_pool": evidence_pool or [],
    }


def _patch_execute_retriever(
    monkeypatch,
    retriever,
    *,
    technical_retries: int = 1,
) -> None:
    cfg = SimpleNamespace(agent_max_technical_retries=technical_retries)
    monkeypatch.setattr(nodes, "get_config", lambda: cfg)
    monkeypatch.setitem(nodes.RETRIEVERS, "graph", retriever)


def test_execute_appends_one_cohesive_attempt_and_raw_pool(monkeypatch):
    old_chunk = {"chunk_id": "C0", "text": "old evidence"}
    new_chunk = {"chunk_id": "C1", "text": "new evidence"}

    def fake_retriever(**kwargs):
        assert kwargs["query"] == "NVDA FY2024 operating risk"
        assert kwargs["top_k_chunks"] == 5
        return {
            "chunks": [new_chunk],
            "trace": {"retriever": "graph", "profile": "phase_t"},
        }

    _patch_execute_retriever(monkeypatch, fake_retriever)
    result = nodes.execute_attempt_node(
        _execute_state(evidence_pool=[old_chunk])
    )

    attempt = result["attempts"][0]
    assert attempt["attempt_id"] == "T1-A1"
    assert attempt["action"] == {
        "tool": "graph",
        "query": "NVDA FY2024 operating risk",
        "top_k_chunks": 5,
    }
    assert attempt["chunks"] == [new_chunk]
    assert attempt["chunks"][0] is new_chunk
    assert attempt["retrieval_trace"]["profile"] == "phase_t"
    assert len(attempt["retrieval_trace"]["technical_tries"]) == 1
    assert attempt["assessment"] is None
    assert result["evidence_pool"] == [old_chunk, new_chunk]


def test_execute_retry_appends_instead_of_overwriting_previous_attempt(
    monkeypatch,
):
    previous = {
        "attempt_id": "T1-A1",
        "task_id": "T1",
        "attempt_number": 1,
        "action": {
            "tool": "graph",
            "query": "NVDA risk",
            "top_k_chunks": 5,
        },
        "retrieval_status": "ok",
        "chunks": [{"chunk_id": "C1"}],
        "retrieval_trace": {"retriever": "graph"},
        "assessment": {"status": "valid"},
    }
    previous_snapshot = deepcopy(previous)
    _patch_execute_retriever(
        monkeypatch,
        lambda **_: [{"chunk_id": "C2", "text": "retry evidence"}],
    )

    result = nodes.execute_attempt_node(
        _execute_state(attempts=[previous])
    )

    assert len(result["attempts"]) == 2
    assert result["attempts"][0] == previous_snapshot
    assert previous == previous_snapshot
    assert result["attempts"][1]["attempt_id"] == "T1-A2"


def test_transient_failure_then_success_uses_one_agent_attempt(monkeypatch):
    calls = 0

    def flaky_retriever(**_):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise TimeoutError("temporary timeout")
        return [{"chunk_id": "C1"}]

    _patch_execute_retriever(monkeypatch, flaky_retriever)
    result = nodes.execute_attempt_node(_execute_state())

    assert calls == 2
    assert len(result["attempts"]) == 1
    assert [
        item["status"]
        for item in result["attempts"][0]["retrieval_trace"]["technical_tries"]
    ] == ["error", "ok"]


def test_exhausted_transient_failure_records_terminal_tool_error(monkeypatch):
    calls = 0

    def unavailable_retriever(**_):
        nonlocal calls
        calls += 1
        raise TimeoutError("still unavailable")

    _patch_execute_retriever(monkeypatch, unavailable_retriever)
    result = nodes.execute_attempt_node(_execute_state())

    attempt = result["attempts"][0]
    assert calls == 2
    assert len(result["attempts"]) == 1
    assert attempt["retrieval_status"] == "tool_error"
    assert attempt["chunks"] == []
    assert attempt["assessment"] is None
    assert attempt["retrieval_trace"]["status"] == "terminal"
    assert len(attempt["retrieval_trace"]["technical_tries"]) == 2
    assert result["current_action"] == {}
    assert result["stop_reason"] == "tool_error"


def test_non_transient_programming_error_is_not_retried(monkeypatch):
    calls = 0

    def broken_retriever(**_):
        nonlocal calls
        calls += 1
        raise ValueError("programming error")

    _patch_execute_retriever(
        monkeypatch,
        broken_retriever,
        technical_retries=3,
    )
    result = nodes.execute_attempt_node(_execute_state())

    assert calls == 1
    assert result["attempts"][0]["retrieval_status"] == "tool_error"


def test_zero_result_is_valid_evidence_attempt_not_tool_error(monkeypatch):
    old_pool = [{"chunk_id": "C0"}]
    _patch_execute_retriever(monkeypatch, lambda **_: [])

    result = nodes.execute_attempt_node(
        _execute_state(evidence_pool=old_pool)
    )

    attempt = result["attempts"][0]
    assert attempt["retrieval_status"] == "ok"
    assert attempt["chunks"] == []
    assert attempt["assessment"] is None
    assert result["evidence_pool"] == old_pool
    assert result["stop_reason"] is None


def test_execute_preserves_phase_t_trace_and_deduplicates_pool(monkeypatch):
    old_chunk = {"chunk_id": "C1", "text": "first copy"}
    duplicate = {"chunk_id": "C1", "text": "later copy"}
    new_chunk = {"chunk_id": "C2", "text": "new evidence"}
    phase_t_trace = {
        "retriever": "graph",
        "profile": "phase_t",
        "projection": {"name": "semigraph_ppr_entity_chunk"},
        "returned_chunk_ids": ["C1", "C2"],
    }
    _patch_execute_retriever(
        monkeypatch,
        lambda **_: {
            "chunks": [duplicate, new_chunk],
            "trace": phase_t_trace,
        },
    )

    result = nodes.execute_attempt_node(
        _execute_state(evidence_pool=[old_chunk])
    )

    attempt = result["attempts"][0]
    assert attempt["chunks"] == [duplicate, new_chunk]
    assert attempt["retrieval_trace"]["projection"] == {
        "name": "semigraph_ppr_entity_chunk"
    }
    assert attempt["retrieval_trace"]["returned_chunk_ids"] == ["C1", "C2"]
    assert result["evidence_pool"] == [old_chunk, new_chunk]
    assert result["evidence_pool"][0] is old_chunk
