import json
import threading
from types import SimpleNamespace

import pytest

import semigraph.agent.graph as agent_graph
import semigraph.agent.nodes as nodes
from semigraph.agent.graph import build_agent
from semigraph.config import Config


class _FakeResponse:
    def __init__(self, content: str):
        self.content = content


def _config():
    return SimpleNamespace(
        tickers=[],
        financial_metric_registry={},
        agent_max_attempts_per_task=3,
        agent_max_assessment_attempts=2,
        agent_max_technical_retries=0,
        agent_assess_context_max_chars=60_000,
    )


def _plan(
    tool: str,
    query: str,
    requirement_ids: tuple[str, ...] = ("R1",),
) -> str:
    return json.dumps({
        "tasks": [{
            "task_id": "T1",
            "query": "Find the required evidence",
            "requirements": [
                {
                    "requirement_id": requirement_id,
                    "description": f"Evidence for {requirement_id}",
                }
                for requirement_id in requirement_ids
            ],
            "initial_action": {
                "tool": tool,
                "query": query,
                "top_k_chunks": 5,
            },
        }],
    })


def _retry(tool: str, strategy: str, query: str) -> str:
    return json.dumps({
        "accepted_chunk_ids": [],
        "covered_requirement_ids": [],
        "decision": "retry",
        "retry_strategy": strategy,
        "next_action": {
            "tool": tool,
            "query": query,
            "top_k_chunks": 99,
        },
    })


def _accept(requirement_ids: tuple[str, ...] = ("T1-R1",)) -> str:
    return json.dumps({
        "accepted_chunk_ids": ["C1"],
        "covered_requirement_ids": list(requirement_ids),
        "decision": "accept",
        "retry_strategy": None,
        "next_action": None,
    })


class _HarnessLLM:
    def __init__(self, plan: str, assessments: list[str]):
        self.plan = plan
        self.assessments = iter(assessments)
        self.system_prompts = []

    def invoke(self, messages):
        system = messages[0]["content"]
        self.system_prompts.append(system)
        if system.startswith(nodes.PLAN_ROUTE_SYSTEM_PROMPT):
            return _FakeResponse(self.plan)
        if system.startswith(nodes.ASSESS_SYSTEM_PROMPT):
            return _FakeResponse(next(self.assessments))
        if system == nodes.SYNTHESIZE_ATTEMPTS_SYSTEM_PROMPT:
            return _FakeResponse("Grounded answer [1]. Invalid citation [99].")
        raise AssertionError(f"Unexpected prompt: {system}")


def _chunk():
    return {
        "chunk_id": "C1",
        "ticker": "AMD",
        "section": "Item_1",
        "text": "Grounded evidence.",
    }


def test_production_graph_contains_parallel_task_harness_nodes():
    assert set(build_agent().get_graph().nodes) == {
        "__start__",
        "plan_route",
        "dispatcher",
        "task_worker",
        "collector",
        "synthesize",
        "__end__",
    }


def test_default_parallel_task_limit_is_two():
    assert Config().agent_max_parallel_tasks == 2


@pytest.mark.parametrize("value", [0, 6])
def test_parallel_task_limit_must_match_plan_capacity(tmp_path, value):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        f"agent_harness:\n  max_parallel_tasks: {value}\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="max_parallel_tasks must be 1..5"):
        Config(config_path)


def test_build_agent_uses_configured_parallel_task_limit(monkeypatch):
    monkeypatch.setattr(
        agent_graph,
        "get_config",
        lambda: SimpleNamespace(agent_max_parallel_tasks=3),
    )

    graph = agent_graph.build_agent()

    assert graph.config["max_concurrency"] == 3


def test_tasks_run_in_parallel_and_collector_restores_plan_order(monkeypatch):
    barrier = threading.Barrier(2)
    synthesis_calls = []

    tasks = [
        {
            "task_id": task_id,
            "query": f"Query {task_id}",
            "requirements": [{
                "requirement_id": f"{task_id}-R1",
                "description": f"Evidence for {task_id}",
            }],
            "initial_action": {
                "tool": "graph",
                "query": f"Query {task_id}",
                "top_k_chunks": 5,
            },
        }
        for task_id in ("T1", "T2")
    ]

    def plan_route(_state):
        return {
            "tasks": tasks,
            "current_task_index": 0,
            "current_action": tasks[0]["initial_action"],
        }

    def execute(state):
        task = state["tasks"][0]
        barrier.wait(timeout=3)
        attempt = {
            "attempt_id": f'{task["task_id"]}-A1',
            "task_id": task["task_id"],
            "action": state["current_action"],
            "retrieval_status": "ok",
            "chunks": [{
                "chunk_id": f'{task["task_id"]}-C1',
                "text": "Evidence",
            }],
            "retrieval_trace": {},
            "assessment": None,
        }
        return {"attempts": [attempt]}

    def assess(state):
        task_id = state["tasks"][0]["task_id"]
        attempts = list(state["attempts"])
        attempts[-1] = {
            **attempts[-1],
            "assessment": {"status": "valid", "output": {}},
        }
        return {
            "attempts": attempts,
            "completed_tasks": [{
                "task_id": task_id,
                "sufficient": True,
                "stop_reason": "sufficient",
            }],
            "current_action": {},
            "stop_reason": "sufficient",
        }

    def synthesize(state):
        synthesis_calls.append(state)
        return {"final_answer": "done"}

    monkeypatch.setattr(nodes, "plan_route_node", plan_route)
    monkeypatch.setattr(nodes, "execute_attempt_node", execute)
    monkeypatch.setattr(nodes, "assess_node", assess)
    monkeypatch.setattr(nodes, "synthesize_attempts_node", synthesize)

    result = build_agent().invoke(
        {"original_query": "Question?"},
        config={"max_concurrency": 2},
    )

    assert [item["task_id"] for item in result["attempts"]] == ["T1", "T2"]
    assert [item["task_id"] for item in result["completed_tasks"]] == [
        "T1",
        "T2",
    ]
    assert result["final_answer"] == "done"
    assert len(synthesis_calls) == 1


def test_full_agent_can_switch_tools_and_uses_four_node_state(monkeypatch):
    connected_requirements = ("T1-R1",)
    llm = _HarnessLLM(
        _plan("graph", "first graph query", connected_requirements),
        [
            _retry("vector", "switch_tool", "focused vector query"),
            _accept(connected_requirements),
        ],
    )
    calls = []

    def graph_retriever(query, top_k_chunks, cfg):
        calls.append(("graph", query, top_k_chunks))
        return {"chunks": [], "trace": {"status": "ok"}}

    def vector_retriever(query, top_k_chunks, cfg):
        calls.append(("vector", query, top_k_chunks))
        return {"chunks": [_chunk()], "trace": {"status": "ok"}}

    monkeypatch.setattr(nodes, "get_config", _config)
    monkeypatch.setattr(nodes, "get_llm", lambda _: llm)
    monkeypatch.setitem(nodes.RETRIEVERS, "graph", graph_retriever)
    monkeypatch.setitem(nodes.RETRIEVERS, "vector", vector_retriever)

    result = build_agent().invoke({"original_query": "Question?"})

    assert len(result["tasks"]) == 1
    assert len(result["tasks"][0]["requirements"]) == 1
    assert result["tasks"][0]["initial_action"]["tool"] == "graph"
    assert calls == [
        ("graph", "Find the required evidence", 5),
        ("vector", "focused vector query", 99),
    ]
    assert [attempt["action"]["tool"] for attempt in result["attempts"]] == [
        "graph",
        "vector",
    ]
    assert result["completed_tasks"] == [{
        "task_id": "T1",
        "sufficient": True,
        "stop_reason": "sufficient",
    }]
    assert result["final_answer"] == "Grounded answer [1]. Invalid citation."
    assert result["citation_map"][0]["chunk_id"] == "C1"
    assert "reflection_history" not in result
    assert "observation_history" not in result


@pytest.mark.parametrize(
    ("locked_tool", "planner_tool", "strategy"),
    [
        ("graph", "vector", "bridge_hint"),
        ("vector", "graph", "focus_missing"),
    ],
)
def test_locked_ablation_controls_initial_retry_and_top_k(
    monkeypatch,
    locked_tool,
    planner_tool,
    strategy,
):
    llm = _HarnessLLM(
        _plan(planner_tool, "initial query"),
        [_retry(locked_tool, strategy, "retry query"), _accept()],
    )
    calls = []
    results = iter([[], [_chunk()]])

    def locked_retriever(query, top_k_chunks, cfg):
        calls.append((locked_tool, query, top_k_chunks))
        return {"chunks": next(results), "trace": {"status": "ok"}}

    def forbidden_retriever(**kwargs):
        raise AssertionError("Locked ablation called another Tool")

    monkeypatch.setattr(nodes, "get_config", _config)
    monkeypatch.setattr(nodes, "get_llm", lambda _: llm)
    monkeypatch.setitem(nodes.RETRIEVERS, locked_tool, locked_retriever)
    monkeypatch.setitem(nodes.RETRIEVERS, planner_tool, forbidden_retriever)

    result = build_agent(locked_tool=locked_tool, top_k=7).invoke({
        "original_query": "Question?",
    })

    initial_query = (
        "Find the required evidence"
        if locked_tool == "graph"
        else "initial query"
    )
    assert calls == [
        (locked_tool, initial_query, 7),
        (locked_tool, "retry query", 7),
    ]
    assert {
        attempt["action"]["tool"] for attempt in result["attempts"]
    } == {locked_tool}
    assert {
        attempt["action"]["top_k_chunks"] for attempt in result["attempts"]
    } == {7}
    assert all(
        f'must remain "{locked_tool}"' in prompt
        for prompt in llm.system_prompts
        if prompt.startswith(nodes.ASSESS_SYSTEM_PROMPT)
    )
    assert result["stop_reason"] == "sufficient"


def test_locked_ablation_repairs_cross_tool_retry(monkeypatch):
    llm = _HarnessLLM(
        _plan("graph", "initial query"),
        [
            _retry("vector", "switch_tool", "wrong tool query"),
            _retry("graph", "anchor_enrichment", "grounded graph retry"),
            _accept(),
        ],
    )
    results = iter([[], [_chunk()]])

    monkeypatch.setattr(nodes, "get_config", _config)
    monkeypatch.setattr(nodes, "get_llm", lambda _: llm)
    monkeypatch.setitem(
        nodes.RETRIEVERS,
        "graph",
        lambda **_: {"chunks": next(results), "trace": {}},
    )
    monkeypatch.setitem(
        nodes.RETRIEVERS,
        "vector",
        lambda **_: (_ for _ in ()).throw(
            AssertionError("Cross-tool retry escaped the Graph lock")
        ),
    )

    result = build_agent(locked_tool="graph", top_k=5).invoke({
        "original_query": "Question?",
    })

    assert [attempt["action"]["tool"] for attempt in result["attempts"]] == [
        "graph",
        "graph",
    ]
    assert result["attempts"][0]["assessment"]["status"] == "repaired"
    assert "locked_tool_mismatch" in result["attempts"][0]["assessment"]["trace"][
        "error_codes"
    ]


def test_build_agent_rejects_invalid_evaluation_policy():
    with pytest.raises(ValueError, match="Unsupported locked tool"):
        build_agent(locked_tool="financial")

    with pytest.raises(ValueError, match="top_k must be positive"):
        build_agent(top_k=0)
