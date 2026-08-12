import json
import subprocess
import sys
from copy import deepcopy
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

import semigraph.agent.nodes as nodes
from semigraph.agent.contracts import (
    DEFAULT_TOP_K,
    EvidenceRequirement,
    PlannedTask,
    PlanRouteOutput,
    RetrievalAction,
    ToolName,
)
from semigraph.agent.prompts import (
    build_financial_capability_summary,
    build_plan_route_system_prompt,
)
from semigraph.config import get_config


def _valid_plan_payload() -> dict:
    return {
        "tasks": [{
            "query": "How is AMD dependent on TSMC?",
            "requirements": [{
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
    assert "task_id" not in type(plan.tasks[0]).model_fields
    assert (
        "requirement_id"
        not in type(plan.tasks[0].requirements[0]).model_fields
    )
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


def test_contract_import_does_not_load_online_modules():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; import semigraph.agent.contracts; "
                "assert not any(name.startswith('semigraph.online.') "
                "for name in sys.modules)"
            ),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("task_count", [0, 6])
def test_plan_route_output_rejects_invalid_task_count(task_count):
    payload = _valid_plan_payload()
    payload["tasks"] = [
        deepcopy(payload["tasks"][0])
        for _ in range(task_count)
    ]

    with pytest.raises(ValidationError):
        PlanRouteOutput.model_validate(payload)


def test_plan_route_output_rejects_more_than_five_evidence_needs():
    payload = _valid_plan_payload()
    requirement = payload["tasks"][0]["requirements"][0]
    payload["tasks"][0]["requirements"] = [
        deepcopy(requirement)
        for _ in range(6)
    ]

    with pytest.raises(ValidationError, match="at most 5 evidence needs"):
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
        ("task", "query"),
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


@pytest.mark.parametrize(
    ("container", "field", "value"),
    [
        ("task", "task_id", "T1"),
        ("requirement", "requirement_id", "T1-R1"),
    ],
)
def test_plan_route_output_rejects_model_supplied_ids(container, field, value):
    payload = _valid_plan_payload()
    target = payload["tasks"][0]
    if container == "requirement":
        target = target["requirements"][0]
    target[field] = value

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        PlanRouteOutput.model_validate(payload)


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
    monkeypatch.setattr(
        nodes,
        "get_config",
        lambda: SimpleNamespace(financial_metric_registry={
            "reported": (),
            "derived": (),
            "snapshot": (),
        }),
    )
    monkeypatch.setattr(nodes, "get_llm", lambda cfg: llm)
    return llm


def test_plan_route_node_valid_plan_uses_one_llm_call(monkeypatch):
    llm = _patch_plan_route_dependencies(
        monkeypatch,
        [json.dumps(_valid_plan_payload())],
    )

    result = nodes.plan_route_node({"original_query": "How is AMD dependent on TSMC?"})

    assert len(llm.calls) == 1
    assert "current_task_index" not in result
    assert "current_action" not in result
    assert result["tasks"][0]["task_id"] == "T1"
    assert result["tasks"][0]["requirements"][0]["requirement_id"] == (
        "T1-R1"
    )
    assert result["plan_trace"]["status"] == "ok"
    assert result["plan_trace"]["llm_calls"] == 1
    assert result["plan_trace"]["attempts"] == [
        {"attempt": 1, "status": "valid", "errors": []},
    ]
    assert result["plan_trace"]["latency_sec"] >= 0
    assert "original_query" not in result


def test_plan_route_node_keeps_model_query_for_single_task(monkeypatch):
    payload = _valid_plan_payload()
    task_query = payload["tasks"][0]["query"]
    payload["tasks"][0]["initial_action"]["query"] = "AMD TSMC keywords"
    _patch_plan_route_dependencies(monkeypatch, [json.dumps(payload)])

    result = nodes.plan_route_node({"original_query": task_query})

    assert result["tasks"][0]["initial_action"]["query"] == "AMD TSMC keywords"


def test_plan_route_node_splits_multi_requirement_task_deterministically(
    monkeypatch,
):
    payload = _valid_plan_payload()
    payload["tasks"][0]["requirements"].append({
        "description": "Evidence of TSMC capacity constraints.",
    })
    _patch_plan_route_dependencies(monkeypatch, [json.dumps(payload)])

    result = nodes.plan_route_node({
        "original_query": "How is AMD dependent on TSMC?",
    })

    assert [task["query"] for task in result["tasks"]] == [
        "Evidence of AMD's foundry dependency on TSMC.",
        "Evidence of TSMC capacity constraints.",
    ]
    assert [len(task["requirements"]) for task in result["tasks"]] == [1, 1]
    assert [task["task_id"] for task in result["tasks"]] == ["T1", "T2"]
    assert [
        task["requirements"][0]["requirement_id"]
        for task in result["tasks"]
    ] == ["T1-R1", "T2-R1"]
    assert [task["initial_action"]["query"] for task in result["tasks"]] == [
        task["query"] for task in result["tasks"]
    ]
    assert result["plan_trace"]["normalization"] == {
        "input_tasks": 1,
        "input_requirements": 2,
        "output_tasks": 2,
    }


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
    assert "current_action" not in result
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
    assert "current_action" not in result
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
    assert "current_action" not in result
    assert result["stop_reason"] == "plan_error"
    assert result["plan_trace"]["fallback_source"] == "provider_error"
    assert result["plan_trace"]["attempts"] == [
        {"attempt": 1, "status": "provider_error", "errors": ["RuntimeError"]},
    ]

def test_plan_route_prompt_keeps_connected_graph_chain_in_one_task():
    prompt = build_plan_route_system_prompt(get_config()).lower()

    assert "connected multi-hop relationship chain" in prompt
    assert "one `graph` task" in prompt
    assert "evidence requirement" in prompt
    assert "all linked hops" in prompt
    assert "every independently retrievable fact" in prompt
    assert "multiple evidence requirements" in prompt
    assert "do not collapse" in prompt
    assert "copy the complete `task.query` exactly" not in prompt


def test_plan_route_prompt_matches_contract_and_registry():
    prompt = build_plan_route_system_prompt(get_config()).lower()

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

    assert '"task_id"' not in prompt
    assert '"requirement_id"' not in prompt
    assert '"top_k_chunks"' in prompt
    assert str(DEFAULT_TOP_K) in prompt

    capability_summary = build_financial_capability_summary(get_config()).lower()
    assert capability_summary in prompt
