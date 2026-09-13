from types import SimpleNamespace

import pytest

import semigraph.agents.graph as agent_graph


def _state():
    return {
        "original_query": "What risks did NVIDIA disclose?",
        "task": {
            "query": "What risks did NVIDIA disclose?",
            "requirement": "Evidence of risks disclosed by NVIDIA.",
        },
    }


def test_run_agent_uses_configured_max_concurrency(monkeypatch):
    state = {"original_query": "What risks did NVIDIA disclose?"}
    cfg = SimpleNamespace(agent_max_parallel_tasks=4)
    calls = []

    class FakeGraph:
        def invoke(self, graph_state, config):
            calls.append({"state": graph_state, "config": config})
            return {"tasks": []}

    monkeypatch.setattr(
        agent_graph,
        "build_agent",
        lambda tool, cfg, generate_answer: FakeGraph(),
    )

    result = agent_graph.run_agent(state, tool="graph", cfg=cfg)

    assert result == {"tasks": []}
    assert calls == [{
        "state": state,
        "config": {"max_concurrency": 4},
    }]


def test_build_agent_fans_out_every_task(monkeypatch):
    tasks = [
        {"query": "Query 1", "requirement": "Requirement 1"},
        {"query": "Query 2", "requirement": "Requirement 2"},
        {"query": "Query 3", "requirement": "Requirement 3"},
    ]
    worker_calls = []
    cfg = SimpleNamespace(
        agent_max_parallel_tasks=2,
        agent_max_synthesis_chunks=3,
        agent_top_k_chunks=5,
    )

    def fake_plan_route(state, tool, cfg):
        return {"tasks": tasks}

    class FakeWorker:
        def invoke(self, state):
            worker_calls.append(state)
            return {
                "task_index": state["task_index"],
                "task": state["task"],
                "accepted_chunks": [{
                    "chunk_id": f"c{state['task_index']}",
                    "text": "Evidence",
                }],
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

    result = agent_graph.run_agent(
        {"original_query": "Original question"},
        tool="graph",
        cfg=cfg,
    )

    assert {call["task"]["query"] for call in worker_calls} == {
        "Query 1",
        "Query 2",
        "Query 3",
    }
    assert all(call["original_query"] == "Original question" for call in worker_calls)
    assert {item["task"]["query"] for item in result["worker_results"]} == {
        "Query 1",
        "Query 2",
        "Query 3",
    }
    assert result["synthesis_input"]["original_query"] == "Original question"
    assert {
        chunk["chunk_id"]
        for chunk in result["synthesis_input"]["accepted_chunks"]
    } == {"c0", "c1", "c2"}
    assert result["final_answer"] == "Answer"


def test_build_agent_can_stop_after_collecting_chunks(monkeypatch):
    cfg = SimpleNamespace(
        agent_max_parallel_tasks=1,
        agent_max_synthesis_chunks=1,
        agent_top_k_chunks=5,
    )

    monkeypatch.setattr(
        agent_graph,
        "plan_route_node",
        lambda state, tool, cfg: {
            "tasks": [{"query": "Query", "requirement": "Requirement"}]
        },
    )

    class FakeWorker:
        def invoke(self, state):
            return {
                **state,
                "accepted_chunks": [{"chunk_id": "c1", "text": "Evidence"}],
            }

    monkeypatch.setattr(
        agent_graph,
        "build_task_worker",
        lambda tool, cfg: FakeWorker(),
    )
    monkeypatch.setattr(
        agent_graph,
        "synthesize_node",
        lambda state, cfg: pytest.fail("Synthesize must not run"),
    )

    result = agent_graph.run_agent(
        {"original_query": "Original question"},
        tool="vector",
        cfg=cfg,
        generate_answer=False,
    )

    assert result["synthesis_input"]["accepted_chunks"] == [
        {"chunk_id": "c1", "text": "Evidence"}
    ]
    assert "final_answer" not in result


def test_run_task_worker_invokes_worker(monkeypatch):
    state = _state()
    cfg = SimpleNamespace(
        agent_max_attempts_per_task=3,
        agent_top_k_chunks=5,
    )
    calls = []

    class FakeWorker:
        def invoke(self, worker_state):
            calls.append(worker_state)
            return {"assessment": {"is_covered": True}}

    monkeypatch.setattr(
        agent_graph,
        "build_task_worker",
        lambda tool, cfg: FakeWorker(),
    )

    result = agent_graph.run_task_worker(state, tool="vector", cfg=cfg)

    assert calls == [state]
    assert result == {"assessment": {"is_covered": True}}


def test_task_worker_retries_then_stops_when_covered(monkeypatch):
    execute_calls = []
    assess_calls = []

    def fake_execute(state, tool, top_k_chunks, cfg):
        execute_calls.append(state)
        return {"chunks": [], "current_query": state["task"]["query"]}

    def fake_assess(state, cfg):
        assess_calls.append(state)
        is_covered = len(assess_calls) == 2
        assessment = {
            "accepted_chunk_ids": ["c1"] if is_covered else [],
            "is_covered": is_covered,
            "retry_query": None if is_covered else "Retry query",
            "retry_strategy": None if is_covered else "focus_missing",
        }
        return {
            "assessment": assessment,
            "attempts": [*state.get("attempts", []), {"query": "query"}],
        }

    monkeypatch.setattr(agent_graph, "execute_node", fake_execute)
    monkeypatch.setattr(agent_graph, "assess_node", fake_assess)

    cfg = SimpleNamespace(
        agent_max_attempts_per_task=3,
        agent_top_k_chunks=5,
    )
    result = agent_graph.build_task_worker(tool="graph", cfg=cfg).invoke(_state())

    assert len(execute_calls) == 2
    assert len(assess_calls) == 2
    assert result["assessment"]["is_covered"] is True


def test_task_worker_stops_when_retry_query_is_repeated(monkeypatch):
    execute_calls = []

    def fake_execute(state, tool, top_k_chunks, cfg):
        execute_calls.append(state)
        return {"chunks": [], "current_query": state["task"]["query"]}

    def fake_assess(state, cfg):
        return {
            "assessment": {
                "accepted_chunk_ids": [],
                "is_covered": False,
                "retry_query": state["current_query"],
                "retry_strategy": "focus_missing",
            },
            "attempts": [{"query": state["current_query"]}],
            "stop_reason": "repeated_retry_query",
        }

    monkeypatch.setattr(agent_graph, "execute_node", fake_execute)
    monkeypatch.setattr(agent_graph, "assess_node", fake_assess)

    cfg = SimpleNamespace(
        agent_max_attempts_per_task=3,
        agent_top_k_chunks=5,
    )
    result = agent_graph.build_task_worker(tool="vector", cfg=cfg).invoke(_state())

    assert len(execute_calls) == 1
    assert result["stop_reason"] == "repeated_retry_query"


@pytest.mark.parametrize("max_attempts", [1, 3])
def test_task_worker_stops_at_configured_max_attempts(monkeypatch, max_attempts):
    execute_calls = []

    def fake_execute(state, tool, top_k_chunks, cfg):
        execute_calls.append(state)
        return {"chunks": [], "current_query": state["task"]["query"]}

    def fake_assess(state, cfg):
        return {
            "assessment": {
                "accepted_chunk_ids": [],
                "is_covered": False,
                "retry_query": "Retry query",
                "retry_strategy": "focus_missing",
            },
            "attempts": [*state.get("attempts", []), {"query": "query"}],
        }

    monkeypatch.setattr(agent_graph, "execute_node", fake_execute)
    monkeypatch.setattr(agent_graph, "assess_node", fake_assess)

    cfg = SimpleNamespace(
        agent_max_attempts_per_task=max_attempts,
        agent_top_k_chunks=5,
    )
    result = agent_graph.build_task_worker(tool="graph", cfg=cfg).invoke(_state())

    assert len(execute_calls) == max_attempts
    assert len(result["attempts"]) == max_attempts
    assert result["assessment"]["is_covered"] is False
