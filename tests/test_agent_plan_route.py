import json
from copy import deepcopy
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

import semigraph.agent.nodes as nodes
from semigraph.agent.contracts import EvidenceRequirement, PlanRouteOutput, PlannedTask, RetrievalAction, ToolName
from semigraph.agent.tools import DEFAULT_TOP_K
# from semigraph.agent


def _valid_plan_payload() -> dict:
    return {
        "tasks": [{
            "task_id": "T1",
            "query": "How is AMD dependent on TSMC?",
            "requirements": [{
                "requirement_id": "T1-R1",
                "description": "Evidence of AMD's foundry dependency on TSMC.",
            }],
            "initial_action": {
                "tool": "graph",
                "query": "AMD TSMC foundry dependency",
                "top_k_chunks": DEFAULT_TOP_K,
            },
        }],
    }


def test_plan_route_output_accepts_one_graph_task():
    plan = PlanRouteOutput.model_validate(_valid_plan_payload())

    assert plan.tasks[0].initial_action.tool == ToolName.graph
    assert plan.tasks[0].initial_action.top_k_chunks == DEFAULT_TOP_K
    assert set(plan.model_dump(mode="json")["tasks"][0]["initial_action"]) == {
        "tool",
        "query",
        "top_k_chunks",
    }


def test_retrieval_action_uses_existing_default_top_k():
    payload = _valid_plan_payload()
    del payload["tasks"][0]["initial_action"]["top_k_chunks"]

    plan = PlanRouteOutput.model_validate(payload)

    assert plan.tasks[0].initial_action.top_k_chunks == DEFAULT_TOP_K


@pytest.mark.parametrize("task_count", [0, 4])
def test_plan_route_output_rejects_invalid_task_count(task_count):
    payload = _valid_plan_payload()
    payload["tasks"] = [
        deepcopy(payload["tasks"][0])
        for _ in range(task_count)
    ]
    for index, task in enumerate(payload["tasks"], start=1):
        task["task_id"] = f"T{index}"
        task["requirements"][0]["requirement_id"] = f"T{index}-R1"

    with pytest.raises(ValidationError):
        PlanRouteOutput.model_validate(payload)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("tool", "hybrid"),
        ("tool", "unknown"),
        ("tool", 123),
        ("query", "   "),
        ("query", 123),
        ("top_k_chunks", 0),
        ("top_k_chunks", -1),
        ("top_k_chunks", "5"),
    ],
)
def test_retrieval_action_rejects_invalid_fields(field, value):
    payload = _valid_plan_payload()
    payload["tasks"][0]["initial_action"][field] = value

    with pytest.raises(ValidationError):
        PlanRouteOutput.model_validate(payload)


@pytest.mark.parametrize(
    ("container", "field"),
    [
        ("task", "task_id"),
        ("task", "query"),
        ("requirement", "requirement_id"),
        ("requirement", "description"),
    ],
)
def test_plan_route_output_rejects_blank_text(container, field):
    payload = _valid_plan_payload()
    target = payload["tasks"][0]
    if container == "requirement":
        target = target["requirements"][0]
    target[field] = "   "

    with pytest.raises(ValidationError):
        PlanRouteOutput.model_validate(payload)


def test_plan_route_output_rejects_extra_fields():
    payload = _valid_plan_payload()
    payload["tasks"][0]["unexpected"] = True

    with pytest.raises(ValidationError):
        PlanRouteOutput.model_validate(payload)


def test_plan_route_output_requires_at_least_one_requirement():
    payload = _valid_plan_payload()
    payload["tasks"][0]["requirements"] = []

    with pytest.raises(ValidationError):
        PlanRouteOutput.model_validate(payload)


def test_plan_route_output_rejects_duplicate_task_ids():
    payload = _valid_plan_payload()
    duplicate = deepcopy(payload["tasks"][0])
    duplicate["requirements"][0]["requirement_id"] = "T2-R1"
    payload["tasks"].append(duplicate)

    with pytest.raises(ValidationError, match="Duplicate task_id found: T1"):
        PlanRouteOutput.model_validate(payload)


def test_plan_route_output_rejects_duplicate_requirement_ids_across_tasks():
    payload = _valid_plan_payload()
    second_task = deepcopy(payload["tasks"][0])
    second_task["task_id"] = "T2"
    payload["tasks"].append(second_task)

    with pytest.raises(ValidationError, match="Duplicate requirement_id found: T1-R1"):
        PlanRouteOutput.model_validate(payload)


def _warning_test_config():
    return SimpleNamespace(
        tickers=["AMD", "NVDA"],
        financial_metric_registry={
            "reported": frozenset({"revenue"}),
            "derived": frozenset({"gross_margin"}),
            "snapshot": frozenset(),
        },
    )


def test_collect_plan_warnings_returns_empty_when_anchors_are_preserved():
    original_query = "Compare AMD revenue in FY2025 with NVDA in Q4."
    payload = _valid_plan_payload()
    payload["tasks"][0]["query"] = original_query
    payload["tasks"][0]["requirements"][0]["description"] = (
        "Evidence for AMD and NVDA revenue in FY2025 and Q4."
    )
    payload["tasks"][0]["initial_action"]["query"] = original_query
    plan = PlanRouteOutput.model_validate(payload)

    assert nodes._collect_plan_warnings(
        original_query,
        plan,
        _warning_test_config(),
    ) == []


def test_collect_plan_warnings_reports_only_missing_explicit_anchors():
    original_query = "Compare AMD gross margin in FY2025 with NVDA in Q4."
    payload = _valid_plan_payload()
    payload["tasks"][0]["query"] = "Compare AMD performance."
    payload["tasks"][0]["requirements"][0]["description"] = "Evidence about AMD."
    payload["tasks"][0]["initial_action"]["query"] = "AMD performance"
    plan = PlanRouteOutput.model_validate(payload)

    warnings = nodes._collect_plan_warnings(
        original_query,
        plan,
        _warning_test_config(),
    )

    assert warnings == [
        {
            "code": "missing_explicit_anchor",
            "anchor_type": "ticker",
            "value": "NVDA",
        },
        {
            "code": "missing_explicit_anchor",
            "anchor_type": "period",
            "value": "FY2025",
        },
        {
            "code": "missing_explicit_anchor",
            "anchor_type": "period",
            "value": "Q4",
        },
        {
            "code": "missing_explicit_anchor",
            "anchor_type": "metric",
            "value": "gross_margin",
        },
    ]


def test_collect_plan_warnings_normalizes_case_and_separators():
    original_query = "Compare amd GROSS MARGIN in FY 2025."
    payload = _valid_plan_payload()
    payload["tasks"][0]["query"] = "Compare AMD gross_margin in 2025."
    payload["tasks"][0]["requirements"][0]["description"] = "Required evidence."
    payload["tasks"][0]["initial_action"]["query"] = "AMD gross-margin 2025"
    plan = PlanRouteOutput.model_validate(payload)

    assert nodes._collect_plan_warnings(
        original_query,
        plan,
        _warning_test_config(),
    ) == []


class _FakePlanRouteLLM:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    def invoke(self, messages):
        self.calls.append(messages)
        response = next(self.responses)
        if isinstance(response, Exception):
            raise response
        return SimpleNamespace(content=response)


def _patch_plan_route_dependencies(monkeypatch, responses):
    llm = _FakePlanRouteLLM(responses)
    monkeypatch.setattr(nodes, "get_config", _warning_test_config)
    monkeypatch.setattr(nodes, "get_llm", lambda cfg: llm)
    return llm


def test_plan_route_node_valid_plan_uses_one_llm_call(monkeypatch):
    llm = _patch_plan_route_dependencies(
        monkeypatch,
        [json.dumps(_valid_plan_payload())],
    )

    result = nodes.plan_route_node({"original_query": "How is AMD dependent on TSMC?"})

    assert len(llm.calls) == 1
    assert result["current_task_index"] == 0
    assert result["current_action"] == result["tasks"][0]["initial_action"]
    assert result["plan_trace"]["status"] == "ok"
    assert result["plan_trace"]["llm_calls"] == 1
    assert result["plan_trace"]["attempts"] == [
        {"attempt": 1, "status": "valid", "errors": []},
    ]
    assert result["plan_trace"]["latency_sec"] >= 0
    assert "original_query" not in result


def test_plan_route_node_repairs_once_then_accepts_valid_plan(monkeypatch):
    llm = _patch_plan_route_dependencies(
        monkeypatch,
        ["invalid-json", json.dumps(_valid_plan_payload())],
    )

    result = nodes.plan_route_node({"original_query": "How is AMD dependent on TSMC?"})

    assert len(llm.calls) == 2
    assert result["plan_trace"]["status"] == "repaired"
    assert result["plan_trace"]["llm_calls"] == 2
    assert [attempt["status"] for attempt in result["plan_trace"]["attempts"]] == [
        "invalid",
        "valid",
    ]
    assert "invalid-json" in llm.calls[1][1]["content"]


def test_plan_route_node_stops_after_two_invalid_responses(monkeypatch):
    raw_responses = ["first-invalid-secret", "second-invalid-secret"]
    llm = _patch_plan_route_dependencies(monkeypatch, raw_responses)

    result = nodes.plan_route_node({"original_query": "How is AMD dependent on TSMC?"})

    assert len(llm.calls) == 2
    assert result["tasks"] == []
    assert result["current_action"] == {}
    assert result["stop_reason"] == "plan_error"
    assert result["plan_trace"]["fallback_source"] == (
        "validation_failed_after_repair"
    )
    assert result["plan_trace"]["llm_calls"] == 2
    assert not any(raw in str(result["plan_trace"]) for raw in raw_responses)


def test_plan_route_node_empty_query_does_not_call_llm(monkeypatch):
    def fail_if_called():
        raise AssertionError("get_config must not be called for an empty query")

    monkeypatch.setattr(nodes, "get_config", fail_if_called)

    result = nodes.plan_route_node({"original_query": "   "})

    assert result["tasks"] == []
    assert result["current_action"] == {}
    assert result["stop_reason"] == "plan_error"
    assert result["plan_trace"]["fallback_source"] == "empty_query"
    assert result["plan_trace"]["llm_calls"] == 0


def test_plan_route_node_provider_error_is_terminal(monkeypatch):
    llm = _patch_plan_route_dependencies(
        monkeypatch,
        [RuntimeError("provider unavailable")],
    )

    result = nodes.plan_route_node({"original_query": "How is AMD dependent on TSMC?"})

    assert len(llm.calls) == 1
    assert result["tasks"] == []
    assert result["current_action"] == {}
    assert result["stop_reason"] == "plan_error"
    assert result["plan_trace"]["fallback_source"] == "provider_error"
    assert result["plan_trace"]["attempts"] == [
        {"attempt": 1, "status": "provider_error", "errors": ["RuntimeError"]},
    ]

from semigraph.agent.contracts import ToolName
from semigraph.agent.prompts import (
    PLAN_ROUTE_SYSTEM_PROMPT,
    build_financial_capability_summary,
)
from semigraph.agent.tools import DEFAULT_TOP_K
from semigraph.config import get_config


def test_plan_route_prompt_keeps_connected_graph_chain_in_one_task():
    prompt = PLAN_ROUTE_SYSTEM_PROMPT

    assert "connected multi-hop relationship chain" in prompt
    assert "ONE `graph` task" in prompt
    assert "evidence requirements" in prompt
    assert '"requirements"' in prompt


def test_plan_route_prompt_matches_contract_and_registry():
    prompt = PLAN_ROUTE_SYSTEM_PROMPT

    for tool in ToolName:
        assert f"`{tool.value}`" in prompt

    assert "Never produce `hybrid`" in prompt
    assert f'"top_k_chunks": {DEFAULT_TOP_K}' in prompt

    capability_summary = build_financial_capability_summary(get_config())
    assert capability_summary in prompt


def test_plan_route_prompt_keeps_connected_graph_chain_in_one_task():
    prompt = PLAN_ROUTE_SYSTEM_PROMPT.lower()

    assert "connected multi-hop relationship chain" in prompt
    assert "one `graph` task" in prompt
    assert "evidence requirements" in prompt
    assert "individual hops or claims" in prompt



"""
sys:1: DeprecationWarning: builtin type swigvarlink has no __module__ attribute

"""

def test_plan_route_prompt_matches_contract_and_registry():
    prompt = PLAN_ROUTE_SYSTEM_PROMPT.lower()

    expected_tools = {"graph", "vector", "financial", "news"}
    assert {tool.value for tool in ToolName} == expected_tools

    for tool in ToolName:
        assert f"`{tool.value}`" in prompt

    assert "never produce `hybrid`" in prompt
    
    expected_fields = (
        set(PlannedTask.model_fields)
        | set(EvidenceRequirement.model_fields)
        | set(RetrievalAction.model_fields)
    )
    for field in expected_fields:
        assert f'"{field}"' in prompt

    assert '"top_k_chunks"' in prompt
    assert str(DEFAULT_TOP_K) in prompt

    capability_summary = build_financial_capability_summary(get_config()).lower()
    assert capability_summary in prompt


if __name__ == "__main__":
    capability_summary = build_financial_capability_summary(get_config())
    print(" Capability Summary:")
    print(capability_summary)

    print("typed = ", type(capability_summary))


    # print(set(PlannedTask.model_fields) | set(EvidenceRequirement.model_fields) | set(RetrievalAction.model_fields))
