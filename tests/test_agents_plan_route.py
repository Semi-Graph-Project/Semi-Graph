import json
import os
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

import semigraph.agents.graph as agent_graph
import semigraph.agents.contracts as contracts
import semigraph.agents.nodes as nodes
import semigraph.agents.prompts as prompts
from semigraph.agents.contracts import PlanRouteOutput


RUN_LIVE_LLM_TESTS = os.getenv("RUN_LIVE_LLM_TESTS") == "1"
requires_live_llm = pytest.mark.skipif(
    not RUN_LIVE_LLM_TESTS,
    reason="set RUN_LIVE_LLM_TESTS=1 to call the real LLM",
)


def _valid_plan_payload() -> dict:
    return {
        "tasks": [{
            "query": "What risks did NVIDIA disclose?",
            "requirement": "Evidence of NVIDIA discloses risks.",
        }],
    }


def _config() -> SimpleNamespace:
    return SimpleNamespace(
        informative_rel_types=("discloses",),
        agent_max_planned_tasks=3,
        agent_max_num_ontology=8,
        agent_max_synthesis_chunks=10,
    )


class _FakeLLM:
    def __init__(self, content: str):
        self.content = content
        self.calls = []

    def invoke(self, messages):
        self.calls.append(messages)
        return SimpleNamespace(content=self.content)


class _SequenceFakeLLM:
    def __init__(self, contents: list[str]):
        self.contents = iter(contents)
        self.calls = []

    def invoke(self, messages):
        self.calls.append(messages)
        return SimpleNamespace(content=next(self.contents))


def test_plan_route_contract_uses_flat_requirement():
    payload = _valid_plan_payload()

    plan = PlanRouteOutput.model_validate(payload)

    assert plan.tasks[0].requirement == payload["tasks"][0]["requirement"]

    payload["tasks"][0]["requirement"] = {
        "description": "Evidence of NVIDIA discloses risks.",
    }
    with pytest.raises(ValidationError):
        PlanRouteOutput.model_validate(payload)


def test_retrieval_action_uses_config_top_k_by_default(monkeypatch):
    monkeypatch.setattr(
        contracts,
        "get_config",
        lambda: SimpleNamespace(agent_top_k_chunks=17),
    )

    action = contracts.RetrievalAction(
        tool=contracts.ToolName.graph,
        query="What risks did NVIDIA disclose?",
    )

    assert action.top_k_chunks == 17


def test_prompt_contains_flat_requirement_schema(monkeypatch):
    monkeypatch.setattr(
        prompts,
        "RELATIONSHIP_CATALOG",
        {"discloses": {"description": "Reports filing facts."}},
    )

    prompt = prompts.build_ontology_planroute_prompt(
        informative_relations=["discloses"],
        max_planned_tasks=3,
    )

    assert '"query": "self-contained Graph retrieval query"' in prompt
    assert (
        '"requirement": "evidence need to verify from supplied documents"'
        in prompt
    )
    assert '"requirement": {' not in prompt


def test_plan_route_node_parses_valid_response(monkeypatch):
    payload = _valid_plan_payload()
    llm = _FakeLLM(json.dumps(payload))
    monkeypatch.setattr(nodes, "get_llm", lambda cfg: llm)
    monkeypatch.setattr(
        prompts,
        "RELATIONSHIP_CATALOG",
        {"discloses": {"description": "Reports filing facts."}},
    )

    result = nodes.plan_route_node(
        {"original_query": "What risks did NVIDIA disclose?"},
        tool="graph",
        cfg=_config(),
    )

    assert len(llm.calls) == 1
    assert result == payload


def test_plan_route_node_retries_with_validation_error(monkeypatch):
    invalid_payload = _valid_plan_payload()
    invalid_payload["tasks"][0]["requirement"] = {
        "description": "Evidence of NVIDIA discloses risks.",
    }
    valid_payload = _valid_plan_payload()
    llm = _SequenceFakeLLM([
        json.dumps(invalid_payload),
        json.dumps(valid_payload),
    ])
    monkeypatch.setattr(nodes, "get_llm", lambda cfg: llm)

    result = nodes.plan_route_node(
        {"original_query": "What risks did NVIDIA disclose?"},
        tool="graph",
        cfg=_config(),
    )

    assert result == valid_payload
    assert len(llm.calls) == 2
    retry_prompt = llm.calls[1][1]["content"]
    assert "Validation error:" in retry_prompt
    assert "requirement" in retry_prompt


def test_plan_route_node_raises_when_retry_is_invalid(monkeypatch):
    invalid_payload = _valid_plan_payload()
    invalid_payload["tasks"][0]["requirement"] = {
        "description": "Evidence of NVIDIA discloses risks.",
    }
    llm = _SequenceFakeLLM([
        json.dumps(invalid_payload),
        json.dumps(invalid_payload),
    ])
    monkeypatch.setattr(nodes, "get_llm", lambda cfg: llm)

    with pytest.raises(
        ValueError,
        match="Failed to validate plan route response after retry",
    ):
        nodes.plan_route_node(
            {"original_query": "What risks did NVIDIA disclose?"},
            tool="graph",
            cfg=_config(),
        )

    assert len(llm.calls) == 2


def test_build_agent_runs_plan_route(monkeypatch):
    payload = _valid_plan_payload()
    calls = []
    worker_calls = []
    cfg = _config()

    def fake_plan_route(state, tool, cfg):
        calls.append({"state": state, "tool": tool, "cfg": cfg})
        return payload

    class FakeWorker:
        def invoke(self, state):
            worker_calls.append(state)
            return {
                "task_index": state["task_index"],
                "task": state["task"],
                "accepted_chunks": [],
            }

    monkeypatch.setattr(agent_graph, "plan_route_node", fake_plan_route)
    monkeypatch.setattr(
        agent_graph,
        "build_task_worker",
        lambda tool, cfg: FakeWorker(),
    )
    monkeypatch.setattr(
        agent_graph,
        "synthesize_node",
        lambda state, cfg: {"final_answer": "Answer"},
    )

    result = agent_graph.build_agent(
        tool=agent_graph.ToolName.GRAPH,
        cfg=cfg,
    ).invoke({"original_query": "What risks did NVIDIA disclose?"})

    assert len(calls) == 1
    assert calls[0]["tool"] == "graph"
    assert calls[0]["cfg"] is cfg
    assert result["tasks"] == payload["tasks"]
    assert worker_calls == [{
        "original_query": "What risks did NVIDIA disclose?",
        "task_index": 0,
        "task": payload["tasks"][0],
    }]
    assert result["worker_results"] == [{
        "task_index": 0,
        "task": payload["tasks"][0],
        "accepted_chunks": [],
    }]
    assert result["final_answer"] == "Answer"


@requires_live_llm
@pytest.mark.parametrize(
    ("question", "expected_relations"),
    [
        pytest.param(
            "What outlook did NVIDIA provide for next quarter's revenue?",
            ("guides on", "guided on", "guidance on"),
            id="guides_on",
        ),
        pytest.param(
            "Which outside companies was NVIDIA reliant upon for chip "
            "manufacturing during fiscal year 2024?",
            ("depends on", "depended on", "depending on", "dependency on"),
            id="depends_on",
        ),
        pytest.param(
            "Which companies provided critical components to NVIDIA during "
            "fiscal year 2024?",
            ("supplies", "supplied", "supplying"),
            id="supplies",
        ),
        pytest.param(
            "Which companies were NVIDIA's rivals in the data center GPU "
            "market during fiscal year 2024?",
            (
                "competes with",
                "competed with",
                "competing with",
                "competition with",
            ),
            id="competes_with",
        ),
        pytest.param(
            "Which business risks threatened Micron during fiscal year 2024?",
            ("faces", "faced", "facing"),
            id="faces",
        ),
    ],
)
def test_plan_route_maps_expected_relation(question, expected_relations):
    result = nodes.plan_route_node(
        {"original_query": question},
        tool="graph",
    )

    output_text = " ".join(
        str(task[field])
        for task in result["tasks"]
        for field in ("query", "requirement")
    ).lower().replace("_", " ")

    assert any(
        relation in output_text for relation in expected_relations
    ), result["tasks"]


@requires_live_llm
@pytest.mark.parametrize(
    ("question", "expected_min_tasks"),
    [
        pytest.param(
            "Which external companies did NVIDIA rely on for chip "
            "manufacturing during fiscal year 2024, and which companies did "
            "NVIDIA compete with in the data center GPU market during the "
            "same period?",
            2,
            id="dependency_and_competition",
        ),
        pytest.param(
            "What outlook did NVIDIA provide for next quarter's revenue, and "
            "which business risks threatened Micron during fiscal year 2024?",
            2,
            id="guidance_and_risk",
        ),
    ],
)
def test_plan_route_splits_expected_number_of_tasks(
    question,
    expected_min_tasks,
):
    result = nodes.plan_route_node(
        {"original_query": question},
        tool="graph",
    )

    assert len(result["tasks"]) >= expected_min_tasks, result["tasks"]
