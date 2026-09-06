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
)
from semigraph.agent.prompts import build_plan_route_system_prompt
from semigraph.config import get_config


def _valid_plan_payload() -> dict:
    return {
        "tasks": [{
            "query": "How is AMD dependent on TSMC?",
            "requirement": {
                "description": "Evidence of AMD's foundry dependency on TSMC.",
            },
        }],
    }


def test_plan_route_output_accepts_one_task_with_one_requirement():
    plan = PlanRouteOutput.model_validate(_valid_plan_payload())

    assert plan.tasks[0].query == "How is AMD dependent on TSMC?"
    assert "initial_action" not in type(plan.tasks[0]).model_fields
    assert "requirements" not in type(plan.tasks[0]).model_fields
    assert "task_id" not in type(plan.tasks[0]).model_fields
    assert "requirement_id" not in type(plan.tasks[0].requirement).model_fields


def test_retrieval_action_uses_existing_default_top_k():
    action = RetrievalAction(tool="graph", query="AMD TSMC")
    assert action.top_k_chunks == DEFAULT_TOP_K


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


def test_plan_route_output_rejects_empty_tasks():
    payload = _valid_plan_payload()
    payload["tasks"] = []

    with pytest.raises(ValidationError):
        PlanRouteOutput.model_validate(payload)


def test_plan_route_normalization_uses_configured_task_limit():
    payload = _valid_plan_payload()
    task = payload["tasks"][0]
    payload["tasks"] = [deepcopy(task) for _ in range(4)]
    for index, planned_task in enumerate(payload["tasks"]):
        planned_task["query"] = f"Task {index}"

    plan = PlanRouteOutput.model_validate(payload)
    tasks = nodes._normalize_plan_tasks(
        plan,
        max_tasks=3,
        tool="graph",
        cfg=SimpleNamespace(agent_top_k_chunks=7),
    )

    assert len(plan.tasks) == 4
    assert [task["query"] for task in tasks] == [
        "Task 0", "Task 1", "Task 2"
    ]
    assert all(task["initial_action"]["tool"] == "graph" for task in tasks)
    assert all(task["initial_action"]["top_k_chunks"] == 7 for task in tasks)


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
    payload = {
        "tool": "graph",
        "query": "AMD TSMC",
        "top_k_chunks": 5,
    }
    payload[field] = value

    with pytest.raises(ValidationError):
        RetrievalAction.model_validate(payload)


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
        target = target["requirement"]
    target[field] = "   "

    with pytest.raises(ValidationError):
        PlanRouteOutput.model_validate(payload)


def test_plan_route_output_rejects_extra_fields():
    payload = _valid_plan_payload()
    payload["tasks"][0]["unexpected"] = True

    with pytest.raises(ValidationError):
        PlanRouteOutput.model_validate(payload)


def test_plan_route_output_requires_one_requirement_object():
    payload = _valid_plan_payload()
    del payload["tasks"][0]["requirement"]

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
        target = target["requirement"]
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


def _patch_plan_route_dependencies(monkeypatch, responses, top_k=5):
    llm = _FakePlanRouteLLM(responses)
    runtime_cfg = get_config()
    monkeypatch.setattr(
        nodes,
        "get_config",
        lambda: SimpleNamespace(
            agent_max_planned_tasks=runtime_cfg.agent_max_planned_tasks,
            agent_max_num_ontology=runtime_cfg.agent_max_num_ontology,
            agent_top_k_chunks=top_k,
        ),
    )
    monkeypatch.setattr(nodes, "get_llm", lambda cfg: llm)
    return llm


def test_plan_route_node_valid_plan_uses_one_llm_call(monkeypatch):
    llm = _patch_plan_route_dependencies(
        monkeypatch,
        [json.dumps(_valid_plan_payload())],
        top_k=7,
    )

    result = nodes.plan_route_node(
        {"original_query": "How is AMD dependent on TSMC?"},
        tool="graph",
    )

    assert len(llm.calls) == 1
    assert "current_task_index" not in result
    assert "current_action" not in result
    assert result["tasks"][0]["task_id"] == "T1"
    task = result["tasks"][0]
    assert task["requirement"]["requirement_id"] == "T1-R1"
    assert task["initial_action"] == {
        "tool": "graph",
        "query": task["query"],
        "top_k_chunks": 7,
    }
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
    _patch_plan_route_dependencies(monkeypatch, [json.dumps(payload)])

    result = nodes.plan_route_node(
        {"original_query": task_query},
        tool="vector",
    )

    assert result["tasks"][0]["initial_action"] == {
        "tool": "vector",
        "query": task_query,
        "top_k_chunks": 5,
    }


def test_plan_route_node_preserves_one_requirement_per_task(
    monkeypatch,
):
    payload = _valid_plan_payload()
    payload["tasks"].append({
        "query": "What capacity constraints does TSMC disclose?",
        "requirement": {
            "description": "TSMC capacity constraint evidence.",
        },
    })
    _patch_plan_route_dependencies(monkeypatch, [json.dumps(payload)])

    result = nodes.plan_route_node({
        "original_query": "How is AMD dependent on TSMC?",
    }, tool="graph")

    assert [task["query"] for task in result["tasks"]] == [
        "How is AMD dependent on TSMC?",
        "What capacity constraints does TSMC disclose?",
    ]
    assert [task["task_id"] for task in result["tasks"]] == ["T1", "T2"]
    assert [
        task["requirement"]["requirement_id"]
        for task in result["tasks"]
    ] == ["T1-R1", "T2-R1"]
    assert [task["initial_action"]["query"] for task in result["tasks"]] == [
        task["query"] for task in result["tasks"]
    ]
    assert result["plan_trace"]["normalization"] == {
        "input_tasks": 2,
        "output_tasks": 2,
    }


def test_plan_route_node_repairs_once_then_accepts_valid_plan(monkeypatch):
    llm = _patch_plan_route_dependencies(
        monkeypatch,
        ["invalid-json", json.dumps(_valid_plan_payload())],
    )

    result = nodes.plan_route_node(
        {"original_query": "How is AMD dependent on TSMC?"},
        tool="graph",
    )

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

    result = nodes.plan_route_node(
        {"original_query": "How is AMD dependent on TSMC?"},
        tool="graph",
    )

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

    result = nodes.plan_route_node(
        {"original_query": "   "}, tool="graph"
    )

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

    result = nodes.plan_route_node(
        {"original_query": "How is AMD dependent on TSMC?"},
        tool="graph",
    )

    assert len(llm.calls) == 1
    assert result["tasks"] == []
    assert "current_action" not in result
    assert result["stop_reason"] == "plan_error"
    assert result["plan_trace"]["fallback_source"] == "provider_error"
    assert result["plan_trace"]["attempts"] == [
        {"attempt": 1, "status": "provider_error", "errors": ["RuntimeError"]},
    ]

def test_plan_route_prompt_keeps_connected_graph_chain_in_one_task():
    prompt = build_plan_route_system_prompt(get_config(), "graph").lower()

    assert "connected multi-hop chain" in prompt
    assert "fixed `graph`" in prompt
    assert "one task must contain exactly one" in prompt
    assert "independently retrievable requirement" in prompt


def test_plan_route_prompt_matches_contract_and_registry():
    prompt = build_plan_route_system_prompt(get_config(), "vector").lower()

    assert "fixed `vector`" in prompt
    assert "choose a tool" in prompt
    assert "hybrid" not in prompt

    expected_fields = (
        set(PlannedTask.model_fields)
        | set(EvidenceRequirement.model_fields)
    )
    for field in expected_fields:
        assert f'"{field}"' in prompt

    assert '"task_id"' not in prompt
    assert '"requirement_id"' not in prompt
    assert '"initial_action"' not in prompt
    assert '"top_k_chunks"' not in prompt
    assert '"tool"' not in prompt
