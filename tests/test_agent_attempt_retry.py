import json
from copy import deepcopy
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

import semigraph.agent.contracts as contracts
import semigraph.agent.ledger as ledger
import semigraph.agent.nodes as nodes
from semigraph.agent.contracts import AssessmentOutput
from semigraph.agent.retry_policy import (
    TOOL_RETRY_PROFILES,
    build_tool_retry_capability_summary,
    decide_retry,
    measure_evidence_gain,
    validate_assessment_context,
)


def _accept_payload(chunk_id: str = "C1") -> dict:
    return {
        "accepted_chunk_ids": [chunk_id],
        "covered_requirement_ids": ["R1"],
        "decision": "accept",
        "retry_strategy": None,
        "next_action": None,
    }


def _retry_payload() -> dict:
    return {
        "accepted_chunk_ids": [],
        "covered_requirement_ids": [],
        "decision": "retry",
        "retry_strategy": "anchor_enrichment",
        "next_action": {
            "tool": "graph",
            "query": "NVDA FY2025 revenue anchor",
            "top_k_chunks": 5,
        },
    }


def _stop_payload() -> dict:
    return {
        "accepted_chunk_ids": [],
        "covered_requirement_ids": [],
        "decision": "stop",
        "retry_strategy": None,
        "next_action": None,
    }


def _task() -> dict:
    return {
        "task_id": "T1",
        "requirements": [
            {"requirement_id": "R1", "description": "Revenue evidence"}
        ],
    }


def test_assessment_contract_accepts_three_decisions():
    for payload in (_accept_payload(), _retry_payload(), _stop_payload()):
        output = AssessmentOutput.model_validate(payload)
        assert output.model_dump(mode="json") == payload


@pytest.mark.parametrize("field", ["retry_strategy", "next_action"])
def test_retry_requires_strategy_and_action(field):
    payload = _retry_payload()
    payload[field] = None

    with pytest.raises(ValidationError):
        AssessmentOutput.model_validate(payload)


def test_non_retry_forbids_retry_fields_and_requires_accepted_evidence():
    payload = _accept_payload()
    payload["retry_strategy"] = "focus_missing"
    with pytest.raises(ValidationError):
        AssessmentOutput.model_validate(payload)

    payload = _accept_payload()
    payload["accepted_chunk_ids"] = []
    with pytest.raises(ValidationError):
        AssessmentOutput.model_validate(payload)


def test_assessment_contract_leaves_duplicate_ids_to_context_handling():
    payload = _accept_payload()
    payload["accepted_chunk_ids"] *= 2
    payload["covered_requirement_ids"] *= 2

    output = AssessmentOutput.model_validate(payload)

    assert output.accepted_chunk_ids == ["C1", "C1"]
    assert output.covered_requirement_ids == ["R1", "R1"]
    assert validate_assessment_context(output, _task(), {"C1"}) == []


def test_contract_and_state_keep_only_lean_ticket03_models():
    from semigraph.agent.state import AgentState, TaskWorkerState

    assert "attempts" in AgentState.__annotations__
    assert "current_task_index" not in AgentState.__annotations__
    assert "current_action" not in AgentState.__annotations__
    assert "task" in TaskWorkerState.__annotations__
    assert "current_task_index" not in TaskWorkerState.__annotations__
    assert "tasks" not in TaskWorkerState.__annotations__
    assert "_locked_tool" not in AgentState.__annotations__
    assert "_locked_tool" not in TaskWorkerState.__annotations__
    assert "_assess_prompt_mode" not in TaskWorkerState.__annotations__
    for field in ("evidence_pool", "accepted_evidence", "requirement_coverage"):
        assert field not in AgentState.__annotations__
    for model in ("RequirementCoverage", "RetryFeedback", "FailureType"):
        assert not hasattr(contracts, model)


def test_assess_prompt_matches_lean_contract_and_retry_registry():
    from semigraph.agent.prompts import ASSESS_SYSTEM_PROMPT

    for field in contracts.AssessmentOutput.model_fields:
        assert f'"{field}"' in ASSESS_SYSTEM_PROMPT
    for enum in (
        contracts.AssessmentDecision,
        contracts.RetryStrategy,
        contracts.ToolName,
    ):
        for member in enum:
            assert member.value in ASSESS_SYSTEM_PROMPT

    summary = build_tool_retry_capability_summary(TOOL_RETRY_PROFILES)
    assert summary in ASSESS_SYSTEM_PROMPT
    assert "failure_type" not in ASSESS_SYSTEM_PROMPT
    assert "requirement_coverage" not in ASSESS_SYSTEM_PROMPT
    assert "generic HyDE" in ASSESS_SYSTEM_PROMPT
    assert "hybrid" not in ASSESS_SYSTEM_PROMPT.casefold()
    assert "useful partial evidence" in ASSESS_SYSTEM_PROMPT


def test_locked_eval_assess_prompt_is_opt_in_and_vector_specific():
    from semigraph.agent.prompts import (
        ASSESS_SYSTEM_PROMPT,
        build_assess_system_prompt,
    )

    assert build_assess_system_prompt() == ASSESS_SYSTEM_PROMPT

    prompt = build_assess_system_prompt("vector")
    assert "Locked Vector Evaluation" in prompt
    assert "focus_missing" in prompt
    assert "next_action.tool` must always be `vector`" in prompt

    with pytest.raises(ValueError, match="Unsupported locked tool"):
        build_assess_system_prompt("financial")


def test_context_validator_checks_only_real_task_and_chunk_ids():
    valid = AssessmentOutput.model_validate(_accept_payload())
    assert validate_assessment_context(valid, _task(), {"C1"}) == []

    payload = _accept_payload("UNKNOWN")
    payload["covered_requirement_ids"] = ["UNKNOWN-R"]
    errors = validate_assessment_context(
        AssessmentOutput.model_validate(payload),
        _task(),
        {"C1"},
    )
    assert {error["code"] for error in errors} == {
        "unknown_covered_requirement_id",
        "accepted_chunk_not_in_current_attempt",
        "accept_requires_all_requirements",
    }


def test_context_validator_rejects_accept_with_uncovered_requirement():
    payload = _accept_payload()
    payload["covered_requirement_ids"] = []
    errors = validate_assessment_context(
        AssessmentOutput.model_validate(payload),
        _task(),
        {"C1"},
    )

    assert errors == [
        {"code": "accept_requires_all_requirements", "value": ["R1"]}
    ]


def _attempt(
    query: str,
    *,
    tool: str = "graph",
    chunks: list[str] | None = None,
    accepted: list[str] | None = None,
    strategy: str | None = None,
) -> dict:
    output = None
    if accepted is not None or strategy is not None:
        output = {
            "accepted_chunk_ids": accepted or [],
            "covered_requirement_ids": [],
            "decision": "retry",
            "retry_strategy": strategy,
            "next_action": None,
        }
    return {
        "attempt_id": "T1-A1",
        "task_id": "T1",
        "action": {"tool": tool, "query": query, "top_k_chunks": 5},
        "retrieval_status": "ok",
        "chunks": [{"chunk_id": chunk_id} for chunk_id in (chunks or [])],
        "retrieval_trace": {},
        "assessment": {"status": "valid", "output": output} if output else None,
    }


def test_evidence_gain_counts_only_new_accepted_ids():
    previous = _attempt("first", chunks=["C1"], accepted=["C1"])
    latest = _attempt("second", chunks=["C1", "C2"])

    no_gain = AssessmentOutput.model_validate({
        **_retry_payload(),
        "accepted_chunk_ids": [],
    })
    gain = AssessmentOutput.model_validate({
        **_retry_payload(),
        "accepted_chunk_ids": ["C2"],
    })

    assert measure_evidence_gain(no_gain, [previous, latest]) == {
        "has_gain": False,
        "new_accepted_chunk_ids": [],
    }
    assert measure_evidence_gain(gain, [previous, latest]) == {
        "has_gain": True,
        "new_accepted_chunk_ids": ["C2"],
    }

    previous["task_id"] = "T0"
    same_id_new_task = AssessmentOutput.model_validate({
        **_retry_payload(),
        "accepted_chunk_ids": ["C1"],
    })
    assert measure_evidence_gain(same_id_new_task, [previous, latest])["has_gain"]


def test_decide_retry_handles_accept_stop_budget_and_repeat():
    attempt = _attempt("NVDA revenue", chunks=["C1"])
    retry = _retry_payload()
    retry["next_action"]["query"] = "NVDA revenue"

    assert decide_retry(
        AssessmentOutput.model_validate(_accept_payload()), [attempt], {}, 3
    )["decision"] == "accept"
    assert decide_retry(
        AssessmentOutput.model_validate(_stop_payload()), [attempt], {}, 3
    )["stop_reason"] == "unsupported"
    assert decide_retry(
        AssessmentOutput.model_validate(retry), [attempt], {}, 3
    )["reason"] == "repeated_action"
    assert decide_retry(
        AssessmentOutput.model_validate(_retry_payload()),
        [attempt, attempt, attempt],
        {},
        3,
    )["stop_reason"] == "budget_exhausted"


def test_decide_retry_rejects_top_k_only_change_after_zero_result():
    payload = _retry_payload()
    payload["next_action"].update(query="NVDA revenue", top_k_chunks=10)

    result = decide_retry(
        AssessmentOutput.model_validate(payload),
        [_attempt("NVDA revenue")],
        {},
        3,
    )

    assert result["reason"] == "zero_result_without_material_change"


def test_decide_retry_validates_same_tool_strategy_and_switch():
    attempt = _attempt("NVDA revenue")
    same_tool = _retry_payload()
    same_tool["next_action"]["query"] = "NVDA revenue relationship bridge"
    assert decide_retry(
        AssessmentOutput.model_validate(same_tool), [attempt], {}, 3
    )["allowed"] is True

    same_tool["retry_strategy"] = "constraint_repair"
    assert decide_retry(
        AssessmentOutput.model_validate(same_tool), [attempt], {}, 3
    )["reason"] == "unsupported_retry_strategy"

    switched = _retry_payload()
    switched.update(retry_strategy="switch_tool")
    switched["next_action"].update(
        tool="vector",
        query="NVDA revenue filing narrative",
    )
    assert decide_retry(
        AssessmentOutput.model_validate(switched), [attempt], {}, 3
    )["reason"] == "tool_switch"


def test_third_attempt_requires_new_accepted_evidence():
    attempts = [
        _attempt("NVDA revenue"),
        _attempt("NVDA revenue anchor"),
    ]
    payload = _retry_payload()
    payload["next_action"]["query"] = "NVDA revenue bridge"
    assessment = AssessmentOutput.model_validate(payload)

    rejected = decide_retry(assessment, attempts, {"has_gain": False}, 3)
    allowed = decide_retry(assessment, attempts, {"has_gain": True}, 3)

    assert rejected["reason"] == "third_attempt_requires_gain"
    assert allowed["allowed"] is True


def _working_context_state() -> dict:
    previous = _attempt(
        "NVDA TSMC dependency",
        chunks=["C0"],
        accepted=["C0"],
        strategy="bridge_hint",
    )
    previous["chunks"][0]["text"] = "Historical accepted evidence"
    latest = _attempt("NVDA TSMC dependency FY2025", chunks=["C1"])
    latest["attempt_id"] = "T1-A2"
    latest["chunks"][0].update(
        rank=1,
        text="NVDA relies on TSMC for manufacturing.",
    )
    latest["retrieval_trace"] = {
        "abort_reason": "insufficient_bridge",
        "seed_count": 6,
        "seeds": [{"name": f"seed-{index}"} for index in range(6)],
        "triple_filter": {
            "reason": "bridge candidates selected",
            "selected_triples": [
                {"candidate_id": f"T{index}"} for index in range(6)
            ],
        },
        "candidate_count": 20,
        "candidate_ranking": ["large-ranking"],
    }
    return {
        "original_query": "How does NVDA depend on TSMC in FY2025?",
        "task": _task(),
        "current_action": latest["action"],
        "attempts": [previous, latest],
    }


def test_working_context_is_derived_from_ledger_and_compact():
    context = ledger.build_assess_context(
        _working_context_state(),
        SimpleNamespace(agent_assess_context_max_chars=60_000),
    )
    payload = json.loads(context)

    assert payload["latest_chunks"][0]["text"].startswith("NVDA relies")
    assert payload["accepted_evidence"][0]["chunk_id"] == "C0"
    assert payload["latest_diagnostics"]["abort_reason"] == "insufficient_bridge"
    assert len(payload["latest_diagnostics"]["seeds"]) == 5
    assert "candidate_ranking" not in payload["latest_diagnostics"]


def test_working_context_is_bounded_without_old_raw_history():
    state = _working_context_state()
    state["attempts"][0]["chunks"][0]["text"] = (
        "OLD_START-" + "x" * 3_000 + "-OLD_SECRET_TAIL"
    )
    state["attempts"][-1]["chunks"][0]["text"] = "latest " * 1_000
    cfg = SimpleNamespace(agent_assess_context_max_chars=2_000)

    context = ledger.build_assess_context(state, cfg)

    assert len(context) <= cfg.agent_assess_context_max_chars
    assert "OLD_SECRET_TAIL" not in context


def test_assessment_parser_and_errors_reject_malformed_or_secret_output():
    with pytest.raises(json.JSONDecodeError):
        nodes._parse_assessment_response("{bad json")

    secret = "RAW_MODEL_SECRET_MARKER"
    with pytest.raises(ValidationError) as exc_info:
        nodes._parse_assessment_response(json.dumps({"secret": secret}))

    normalized = nodes._normalize_assessment_error(exc_info.value)
    assert secret not in json.dumps(normalized)


class _FakeAssessLLM:
    def __init__(self, outputs):
        self.outputs = iter(outputs)
        self.calls = 0

    def invoke(self, _messages):
        self.calls += 1
        output = next(self.outputs)
        if isinstance(output, Exception):
            raise output
        return SimpleNamespace(content=output)


def _assess_state(chunks=None) -> dict:
    state = _working_context_state()
    state["attempts"] = [state["attempts"][-1]]
    state["attempts"][0]["attempt_id"] = "T1-A1"
    state["attempts"][0]["chunks"] = (
        [{"chunk_id": "C1", "text": "current evidence"}]
        if chunks is None
        else chunks
    )
    return state


def _run_assess(monkeypatch, state, outputs):
    llm = _FakeAssessLLM(outputs)
    cfg = SimpleNamespace(
        agent_max_assessment_attempts=2,
        agent_assess_context_max_chars=60_000,
        agent_max_attempts_per_task=3,
    )
    monkeypatch.setattr(nodes, "get_config", lambda: cfg)
    monkeypatch.setattr(nodes, "get_llm", lambda _: llm)
    return nodes.assess_node(state), llm


def test_assess_accepts_task_and_stores_lean_envelope(monkeypatch):
    result, llm = _run_assess(
        monkeypatch,
        _assess_state(),
        [json.dumps(_accept_payload())],
    )
    envelope = result["attempts"][-1]["assessment"]

    assert llm.calls == 1
    assert envelope["status"] == "valid"
    assert envelope["output"]["accepted_chunk_ids"] == ["C1"]
    assert envelope["controller"]["decision"] == "accept"
    assert result["stop_reason"] == "sufficient"
    assert result["completion"] == {
        "task_id": "T1",
        "sufficient": True,
        "stop_reason": "sufficient",
    }
    assert "accepted_evidence" not in result
    assert "requirement_coverage" not in result


def test_assess_stop_records_insufficient_completion(monkeypatch):
    result, _ = _run_assess(
        monkeypatch,
        _assess_state(),
        [json.dumps(_stop_payload())],
    )

    assert result["completion"] == {
        "task_id": "T1",
        "sufficient": False,
        "stop_reason": "unsupported",
    }
    assert result["current_action"] == {}
    assert result["stop_reason"] == "unsupported"


def test_assess_returns_controller_approved_retry(monkeypatch):
    payload = _retry_payload()
    payload.update(
        accepted_chunk_ids=["C1"],
        retry_strategy="bridge_hint",
    )
    payload["next_action"]["query"] = "NVDA revenue dependency bridge"

    result, _ = _run_assess(
        monkeypatch,
        _assess_state(),
        [json.dumps(payload)],
    )

    assert result["current_action"] == payload["next_action"]
    assert "completion" not in result
    gain = result["attempts"][-1]["assessment"]["trace"]["evidence_gain"]
    assert gain["new_accepted_chunk_ids"] == ["C1"]


def test_assess_repairs_once_then_fails_open(monkeypatch):
    repaired, llm = _run_assess(
        monkeypatch,
        _assess_state(),
        [json.dumps(_accept_payload("UNKNOWN")), json.dumps(_accept_payload())],
    )
    assert llm.calls == 2
    assert repaired["attempts"][-1]["assessment"]["status"] == "repaired"

    failed, llm = _run_assess(
        monkeypatch,
        _assess_state(),
        ["{invalid", "{still invalid"],
    )
    assert llm.calls == 2
    assert failed["attempts"][-1]["assessment"]["status"] == "fail_open"
    assert failed["stop_reason"] == "assessment_error"


def test_assess_provider_error_fails_open_without_repair(monkeypatch):
    result, llm = _run_assess(
        monkeypatch,
        _assess_state(),
        [TimeoutError("provider unavailable")],
    )
    envelope = result["attempts"][-1]["assessment"]

    assert llm.calls == 1
    assert envelope["status"] == "fail_open"
    assert envelope["controller"]["reason"] == "provider_error"
    assert envelope["trace"]["error_codes"] == [
        "provider_error:TimeoutError"
    ]


def _build_task_worker_component_graph():
    from langgraph.graph import END, START, StateGraph
    from semigraph.agent.state import TaskWorkerState

    def route_after_execute(state):
        attempts = state.get("attempts") or []
        latest = attempts[-1] if attempts else {}
        if (
            latest.get("retrieval_status") == "ok"
            and latest.get("assessment") is None
        ):
            return "assess"
        return "end"

    def route_after_assess(state):
        return "execute" if state.get("current_action") else "end"

    workflow = StateGraph(TaskWorkerState)
    workflow.add_node("execute", nodes.execute_attempt_node)
    workflow.add_node("assess", nodes.assess_node)
    workflow.add_edge(START, "execute")
    workflow.add_conditional_edges(
        "execute",
        route_after_execute,
        {"assess": "assess", "end": END},
    )
    workflow.add_conditional_edges(
        "assess",
        route_after_assess,
        {"execute": "execute", "end": END},
    )
    return workflow.compile()


def _task_worker_state(query="NVDA FY2025 revenue") -> dict:
    action = {"tool": "graph", "query": query, "top_k_chunks": 5}
    task = _task()
    task.update(query=query, initial_action=action)
    return {
        "original_query": query,
        "task": task,
        "current_action": action,
        "attempts": [],
    }


def _patch_component(monkeypatch, llm, retrievers):
    cfg = SimpleNamespace(
        agent_max_technical_retries=0,
        agent_max_assessment_attempts=2,
        agent_assess_context_max_chars=60_000,
        agent_max_attempts_per_task=3,
        agent_max_synthesis_chunks=10,
    )
    monkeypatch.setattr(nodes, "get_config", lambda: cfg)
    monkeypatch.setattr(nodes, "get_llm", lambda _: llm)
    for tool, retriever in retrievers.items():
        monkeypatch.setitem(nodes.RETRIEVERS, tool, retriever)


def _sequenced_retriever(tool, outputs, calls):
    outputs = iter(outputs)

    def retrieve(**kwargs):
        calls.append((tool, kwargs["query"]))
        return {"chunks": next(outputs), "trace": {}}

    return retrieve


def test_task_worker_recovers_with_graph_hint(monkeypatch):
    retry = _retry_payload()
    accept = _accept_payload()
    llm = _FakeAssessLLM([json.dumps(retry), json.dumps(accept)])
    calls = []
    graph = _sequenced_retriever(
        "graph",
        [[], [{"chunk_id": "C1", "text": "evidence"}]],
        calls,
    )
    _patch_component(monkeypatch, llm, {"graph": graph})

    result = _build_task_worker_component_graph().invoke(
        _task_worker_state(), config={"recursion_limit": 8}
    )

    assert len(result["attempts"]) == 2
    assert [query for _, query in calls] == [
        "NVDA FY2025 revenue",
        "NVDA FY2025 revenue anchor",
    ]
    assert result["stop_reason"] == "sufficient"


def test_task_worker_uses_llm_selected_tool_switch(monkeypatch):
    retry = _retry_payload()
    retry.update(retry_strategy="switch_tool")
    retry["next_action"].update(
        tool="vector",
        query="NVDA FY2025 revenue filing narrative",
    )
    llm = _FakeAssessLLM([
        json.dumps(retry),
        json.dumps(_accept_payload()),
    ])
    calls = []
    retrievers = {
        "graph": _sequenced_retriever("graph", [[]], calls),
        "vector": _sequenced_retriever(
            "vector",
            [[{"chunk_id": "C1", "text": "filing evidence"}]],
            calls,
        ),
    }
    _patch_component(monkeypatch, llm, retrievers)

    result = _build_task_worker_component_graph().invoke(
        _task_worker_state(), config={"recursion_limit": 8}
    )

    assert [tool for tool, _ in calls] == ["graph", "vector"]
    assert result["stop_reason"] == "sufficient"


def test_task_worker_requires_second_attempt_gain_for_third(monkeypatch):
    first = _retry_payload()
    second = deepcopy(first)
    second["next_action"]["query"] = "NVDA FY2025 revenue bridge"
    llm = _FakeAssessLLM([json.dumps(first), json.dumps(second)])
    calls = []
    graph = _sequenced_retriever("graph", [[], []], calls)
    _patch_component(monkeypatch, llm, {"graph": graph})

    result = _build_task_worker_component_graph().invoke(
        _task_worker_state(), config={"recursion_limit": 8}
    )

    assert len(calls) == 2
    assert result["stop_reason"] == "no_evidence_gain"


def _execute_state(attempts=None) -> dict:
    return {
        "task": {"task_id": "T1"},
        "current_action": {
            "tool": "graph",
            "query": "NVDA FY2024 operating risk",
            "top_k_chunks": 5,
        },
        "attempts": attempts or [],
    }


def _patch_execute(monkeypatch, retriever, technical_retries=1):
    cfg = SimpleNamespace(agent_max_technical_retries=technical_retries)
    monkeypatch.setattr(nodes, "get_config", lambda: cfg)

    def contract_retriever(**kwargs):
        result = retriever(**kwargs)
        if isinstance(result, dict):
            return result
        return {"chunks": result, "trace": {}}

    monkeypatch.setitem(nodes.RETRIEVERS, "graph", contract_retriever)


def test_execute_appends_raw_attempt_and_preserves_trace(monkeypatch):
    chunk = {"chunk_id": "C1", "text": "evidence"}
    _patch_execute(
        monkeypatch,
        lambda **_: {
            "chunks": [chunk],
            "trace": {"profile": "phase_t", "returned_chunk_ids": ["C1"]},
        },
    )

    result = nodes.execute_attempt_node(_execute_state())
    attempt = result["attempts"][0]

    assert attempt["attempt_id"] == "T1-A1"
    assert attempt["chunks"][0] is chunk
    assert attempt["retrieval_trace"]["profile"] == "phase_t"
    assert attempt["assessment"] is None
    assert "evidence_pool" not in result
    assert "attempt_number" not in attempt


def test_execute_retry_appends_without_overwriting(monkeypatch):
    previous = _attempt("NVDA risk", chunks=["C1"])
    snapshot = deepcopy(previous)
    _patch_execute(monkeypatch, lambda **_: [{"chunk_id": "C2"}])

    result = nodes.execute_attempt_node(_execute_state([previous]))

    assert result["attempts"][0] == snapshot
    assert result["attempts"][1]["attempt_id"] == "T1-A2"


def test_transient_error_retries_inside_one_agent_attempt(monkeypatch):
    calls = 0

    def flaky(**_):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise TimeoutError("temporary")
        return [{"chunk_id": "C1"}]

    _patch_execute(monkeypatch, flaky)
    result = nodes.execute_attempt_node(_execute_state())

    statuses = [
        item["status"]
        for item in result["attempts"][0]["retrieval_trace"]["technical_tries"]
    ]
    assert calls == 2
    assert len(result["attempts"]) == 1
    assert statuses == ["error", "ok"]


@pytest.mark.parametrize(
    ("error", "expected_calls"),
    [(TimeoutError("unavailable"), 2), (ValueError("bug"), 1)],
)
def test_execute_records_terminal_tool_error(
    monkeypatch, error, expected_calls
):
    calls = 0

    def broken(**_):
        nonlocal calls
        calls += 1
        raise error

    _patch_execute(monkeypatch, broken)
    result = nodes.execute_attempt_node(_execute_state())
    attempt = result["attempts"][0]

    assert calls == expected_calls
    assert attempt["retrieval_status"] == "tool_error"
    assert attempt["chunks"] == []
    assert result["completion"] == {
        "task_id": "T1",
        "sufficient": False,
        "stop_reason": "tool_error",
    }
    assert result["stop_reason"] == "tool_error"


def test_zero_result_is_valid_attempt_for_assess(monkeypatch):
    _patch_execute(monkeypatch, lambda **_: [])

    result = nodes.execute_attempt_node(_execute_state())

    assert result["attempts"][0]["retrieval_status"] == "ok"
    assert result["attempts"][0]["chunks"] == []
    assert result["stop_reason"] is None


def test_synthesis_selector_prioritizes_validated_newer_and_fail_open_last():
    old_c1 = {"chunk_id": "C1", "text": "old C1"}
    new_c1 = {"chunk_id": "C1", "text": "new C1"}
    c2 = {"chunk_id": "C2", "text": "raw C2"}
    accepted_other_task = {"chunk_id": "C3", "text": "accepted C3"}
    fallback = {"chunk_id": "C4", "text": "fallback C4"}
    attempts = [
        {
            "task_id": "T1",
            "chunks": [old_c1],
            "assessment": {
                "status": "valid",
                "output": {"accepted_chunk_ids": ["C1"]},
            },
        },
        {
            "task_id": "T1",
            "chunks": [new_c1, c2],
            "assessment": {
                "status": "repaired",
                "output": {"accepted_chunk_ids": ["C1", "C2"]},
            },
        },
        {
            "task_id": "T1",
            "chunks": [fallback],
            "assessment": {"status": "fail_open", "output": None},
        },
        {
            "task_id": "T2",
            "chunks": [accepted_other_task],
            "assessment": {
                "status": "valid",
                "output": {"accepted_chunk_ids": ["C3"]},
            },
        },
    ]

    result = ledger.select_synthesis_chunks(attempts)

    assert result == [new_c1, c2, accepted_other_task, fallback]
    assert result[0] is new_c1
    assert result[-1] is fallback


def test_synthesis_selector_adds_bounded_raw_fallback_after_accepted():
    accepted = {"chunk_id": "C1", "text": "accepted"}
    rejected_raw = {"chunk_id": "C2", "text": "not accepted"}
    fail_open = {"chunk_id": "C3", "text": "fallback"}
    attempts = [
        {
            "task_id": "T1",
            "chunks": [accepted, rejected_raw],
            "assessment": {
                "status": "valid",
                "output": {"accepted_chunk_ids": ["C1"]},
            },
        },
        {
            "task_id": "T2",
            "chunks": [fail_open],
            "assessment": {"status": "fail_open", "output": None},
        },
    ]

    result = ledger.select_synthesis_chunks(attempts)

    assert result == [accepted, rejected_raw, fail_open]


def test_synthesis_selector_uses_lower_ranks_when_budget_has_room():
    chunks = [{"chunk_id": f"C{index}"} for index in range(1, 5)]
    attempts = [{
        "task_id": "T1",
        "chunks": chunks,
        "assessment": {
            "status": "valid",
            "output": {"accepted_chunk_ids": []},
        },
    }]

    result = ledger.select_synthesis_chunks(attempts, max_total=4)

    assert result == chunks


def test_synthesis_selector_allocates_per_task_then_global_fill():
    def assessed_attempt(task_id, chunk_ids):
        chunks = [{"chunk_id": chunk_id} for chunk_id in chunk_ids]
        return {
            "task_id": task_id,
            "chunks": chunks,
            "assessment": {
                "status": "valid",
                "output": {"accepted_chunk_ids": chunk_ids},
            },
        }

    attempts = [
        assessed_attempt("T1", [f"C{index}" for index in range(1, 8)]),
        assessed_attempt("T2", ["C1", "C8", "C9", "C10"]),
        assessed_attempt("T3", ["C11", "C12"]),
    ]

    result = ledger.select_synthesis_chunks(attempts)

    assert [chunk["chunk_id"] for chunk in result] == [
        "C1",
        "C2",
        "C3",
        "C8",
        "C9",
        "C11",
        "C12",
        "C4",
        "C10",
        "C5",
    ]
    assert len({chunk["chunk_id"] for chunk in result}) == 10


@pytest.mark.parametrize("max_per_task,max_total", [(0, 10), (3, 0)])
def test_synthesis_selector_requires_positive_limits(max_per_task, max_total):
    with pytest.raises(ValueError):
        ledger.select_synthesis_chunks([], max_per_task, max_total)


class _FakeSynthesisLLM:
    def __init__(self, output):
        self.output = output
        self.calls = []

    def invoke(self, messages):
        self.calls.append(messages)
        if isinstance(self.output, Exception):
            raise self.output
        return SimpleNamespace(content=self.output)


def _synthesis_state() -> dict:
    chunk = {
        "chunk_id": "C1",
        "text": "AMD relies on TSMC for wafer fabrication.",
        "ticker": "AMD",
    }
    return {
        "original_query": "How does AMD depend on TSMC?",
        "tasks": [_task()],
        "completed_tasks": [{
            "task_id": "T1",
            "sufficient": True,
            "stop_reason": "sufficient",
        }],
        "attempts": [{
            "task_id": "T1",
            "chunks": [chunk],
            "assessment": {
                "status": "valid",
                "output": {"accepted_chunk_ids": ["C1"]},
            },
        }],
    }


def test_synthesize_attempts_node_returns_grounded_citations(monkeypatch):
    llm = _FakeSynthesisLLM(
        "AMD relies on TSMC for wafer fabrication [1]. Invalid [9]."
    )
    monkeypatch.setattr(
        nodes,
        "get_config",
        lambda: SimpleNamespace(agent_max_synthesis_chunks=10),
    )
    monkeypatch.setattr(nodes, "get_llm", lambda _: llm)

    result = nodes.synthesize_attempts_node(_synthesis_state())

    assert len(llm.calls) == 1
    assert result["final_answer"] == (
        "AMD relies on TSMC for wafer fabrication [1]. Invalid."
    )
    assert result["citation_map"] == [{
        "citation_index": 1,
        "chunk_id": "C1",
        "text": "AMD relies on TSMC for wafer fabrication.",
        "ticker": "AMD",
    }]
    assert result["synthesis_trace"]["status"] == "ok"
    assert result["synthesis_trace"]["max_chunks"] == 10
    assert result["synthesis_trace"]["selected_chunk_ids_by_task"] == {
        "T1": ["C1"],
    }

    user_message = llm.calls[0][1]["content"]
    for label in (
        "Original Query:",
        "Tasks:",
        "Task Completions:",
        "Selected Evidence Chunks:",
    ):
        assert label in user_message
    assert "retrieval_trace" not in user_message
    assert "assessment" not in user_message


def test_synthesize_attempts_node_uses_configured_chunk_limit(monkeypatch):
    state = _synthesis_state()
    chunks = [
        {"chunk_id": f"C{index}", "text": f"Evidence {index}"}
        for index in range(1, 5)
    ]
    state["attempts"][0]["chunks"] = chunks
    state["attempts"][0]["assessment"]["output"]["accepted_chunk_ids"] = [
        chunk["chunk_id"] for chunk in chunks
    ]
    llm = _FakeSynthesisLLM("Grounded answer [1] [2].")
    monkeypatch.setattr(
        nodes,
        "get_config",
        lambda: SimpleNamespace(agent_max_synthesis_chunks=2),
    )
    monkeypatch.setattr(nodes, "get_llm", lambda _: llm)

    result = nodes.synthesize_attempts_node(state)

    assert result["synthesis_trace"]["max_chunks"] == 2
    assert result["synthesis_trace"]["selected_chunk_ids_by_task"] == {
        "T1": ["C1", "C2"],
    }
    user_message = llm.calls[0][1]["content"]
    assert "chunk_id=C2" in user_message
    assert "chunk_id=C3" not in user_message


def test_synthesize_attempts_node_skips_llm_without_evidence(monkeypatch):
    def unexpected_llm(_):
        pytest.fail("No-evidence synthesis must not create an LLM")

    monkeypatch.setattr(nodes, "get_llm", unexpected_llm)

    result = nodes.synthesize_attempts_node({
        "original_query": "Unsupported question",
        "tasks": [],
        "completed_tasks": [],
        "attempts": [],
    })

    assert result["citation_map"] == []
    assert result["synthesis_trace"]["status"] == "no_evidence"
    assert result["synthesis_trace"]["llm_calls"] == 0


def test_synthesize_attempts_node_records_provider_error(monkeypatch):
    llm = _FakeSynthesisLLM(TimeoutError("provider unavailable"))
    monkeypatch.setattr(
        nodes,
        "get_config",
        lambda: SimpleNamespace(agent_max_synthesis_chunks=10),
    )
    monkeypatch.setattr(nodes, "get_llm", lambda _: llm)

    result = nodes.synthesize_attempts_node(_synthesis_state())

    assert len(llm.calls) == 1
    assert result["citation_map"] == []
    assert result["synthesis_trace"]["status"] == "provider_error"
    assert result["synthesis_trace"]["error_type"] == "TimeoutError"


def test_synthesis_trace_groups_selected_ids_by_task(monkeypatch):
    state = _synthesis_state()
    state["tasks"].append({"task_id": "T2"})
    state["completed_tasks"].append({
        "task_id": "T2",
        "sufficient": False,
        "stop_reason": "assessment_error",
    })
    state["attempts"].append({
        "task_id": "T2",
        "chunks": [
            {"chunk_id": "C1", "text": "shared evidence"},
            {"chunk_id": "C2", "text": "fallback evidence"},
        ],
        "assessment": {"status": "fail_open", "output": None},
    })
    llm = _FakeSynthesisLLM("Grounded answer [1] [2].")
    monkeypatch.setattr(
        nodes,
        "get_config",
        lambda: SimpleNamespace(agent_max_synthesis_chunks=10),
    )
    monkeypatch.setattr(nodes, "get_llm", lambda _: llm)

    result = nodes.synthesize_attempts_node(state)

    assert result["synthesis_trace"]["selected_chunk_ids_by_task"] == {
        "T1": ["C1"],
        "T2": ["C1", "C2"],
    }



if __name__ == "__main__":
    attempts_mock = _attempt("NVDA revenue", chunks=["C1"])
    print("Mock attempt:", json.dumps(attempts_mock, indent=2))
