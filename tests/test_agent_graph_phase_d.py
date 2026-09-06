import json
import threading
from types import SimpleNamespace

import pytest

import semigraph.agent.nodes as nodes
from semigraph.agent.graph import build_agent
from semigraph.agent.prompts import ASSESS_SYSTEM_PROMPT
from semigraph.agent.trace_events import AgentTraceEmitter
from semigraph.config import Config


class _FakeResponse:
    def __init__(self, content: str):
        self.content = content


def _config(top_k=5):
    return SimpleNamespace(
        tickers=[],
        informative_rel_types=["discloses"],
        financial_metric_registry={
            "reported": (),
            "derived": (),
            "snapshot": (),
        },
        agent_max_attempts_per_task=3,
        agent_max_planned_tasks=10,
        agent_max_num_ontology=8,
        agent_max_parallel_tasks=5,
        agent_max_assessment_attempts=2,
        agent_max_technical_retries=0,
        agent_max_synthesis_chunks=10,
        agent_assess_context_max_chars=60_000,
        agent_top_k_chunks=top_k,
    )


def _plan(query: str = "first query") -> str:
    return json.dumps({
        "tasks": [{
            "query": query,
            "requirement": {"description": "Required evidence"},
        }],
    })


def _retry(query: str = "focused retry query") -> str:
    return json.dumps({
        "accepted_chunk_ids": [],
        "requirement_covered": False,
        "decision": "retry",
        "retry_query": query,
    })


def _accept() -> str:
    return json.dumps({
        "accepted_chunk_ids": ["C1"],
        "requirement_covered": True,
        "decision": "accept",
        "retry_query": None,
    })


class _HarnessLLM:
    def __init__(self, plan: str, assessments: list[str]):
        self.plan = plan
        self.assessments = iter(assessments)
        self.system_prompts = []

    def invoke(self, messages):
        system = messages[0]["content"]
        self.system_prompts.append(system)
        if system.startswith("You are PlanRoute for SemiGraph"):
            return _FakeResponse(self.plan)
        if system.startswith(ASSESS_SYSTEM_PROMPT):
            return _FakeResponse(next(self.assessments))
        if system == nodes.SYNTHESIZE_ATTEMPTS_SYSTEM_PROMPT:
            return _FakeResponse("Grounded answer [1]. Invalid [99].")
        raise AssertionError(f"Unexpected prompt: {system}")


def _chunk():
    return {
        "chunk_id": "C1",
        "ticker": "AMD",
        "section": "Item_1",
        "text": "Grounded evidence.",
    }


def test_production_graph_contains_parallel_task_harness_nodes():
    assert set(build_agent(tool="graph", cfg=_config()).get_graph().nodes) == {
        "__start__",
        "plan_route",
        "task_worker",
        "collector",
        "synthesize",
        "__end__",
    }


@pytest.mark.parametrize("value", [0, 6])
def test_parallel_task_limit_must_match_plan_capacity(tmp_path, value):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        f"agent_harness:\n  max_parallel_tasks: {value}\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="max_parallel_tasks must be 1..5"):
        Config(config_path)


@pytest.mark.parametrize("value", [0, -1])
def test_synthesis_limit_must_be_positive(tmp_path, value):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        f"agent_harness:\n  max_synthesis_chunks: {value}\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="max_synthesis_chunks must be positive"):
        Config(config_path)


@pytest.mark.parametrize("value", [0, 101])
def test_agent_retrieval_limit_must_be_valid(tmp_path, value):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        f"agent_harness:\n  top_k_chunks: {value}\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="top_k_chunks must be 1..100"):
        Config(config_path)


def test_synthesis_trace_counts_unique_selected_chunks():
    events = []
    emitter = AgentTraceEmitter(events.append)
    emitter.synthesis_finished({
        "synthesis_trace": {
            "status": "ok",
            "selected_chunk_ids_by_task": {
                "T1": ["C1", "C2"],
                "T2": ["C2", "C3"],
            },
        },
        "citation_map": [{"chunk_id": "C1"}],
    })
    assert events[0]["details"] == {
        "selected_evidence_count": 3,
        "citation_count": 1,
    }


def test_build_agent_uses_configured_parallel_task_limit():
    graph = build_agent(
        tool="graph",
        cfg=SimpleNamespace(agent_max_parallel_tasks=3),
    )
    assert graph.config["max_concurrency"] == 3


def test_tasks_run_in_parallel_and_collector_restores_plan_order(monkeypatch):
    lock = threading.Lock()
    first_wave_ready = threading.Event()
    running = 0
    max_running = 0
    started_tasks = []
    synthesis_calls = []
    tasks = [
        {
            "task_id": task_id,
            "query": f"Query {task_id}",
            "requirement": {
                "requirement_id": f"{task_id}-R1",
                "description": f"Evidence for {task_id}",
            },
            "initial_action": {
                "tool": "graph",
                "query": f"Query {task_id}",
                "top_k_chunks": 5,
            },
        }
        for task_id in ("T1", "T2", "T3")
    ]

    def plan_route(_state, tool, cfg=None):
        return {"tasks": tasks}

    def execute(state, cfg=None):
        nonlocal running, max_running
        task = state["task"]
        with lock:
            running += 1
            max_running = max(max_running, running)
            started_tasks.append(task["task_id"])
            wait_for_first_wave = len(started_tasks) <= 2
            if running == 2:
                first_wave_ready.set()
        if wait_for_first_wave:
            assert first_wave_ready.wait(timeout=3)
        with lock:
            running -= 1
        return {"attempts": [{
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
        }]}

    def assess(state, tool, cfg=None):
        task_id = state["task"]["task_id"]
        attempts = list(state["attempts"])
        attempts[-1] = {
            **attempts[-1],
            "assessment": {"status": "valid", "output": {}},
        }
        return {
            "attempts": attempts,
            "completion": {
                "task_id": task_id,
                "sufficient": True,
                "stop_reason": "sufficient",
            },
            "current_action": {},
            "stop_reason": "sufficient",
        }

    def synthesize(state, cfg=None):
        synthesis_calls.append(state)
        return {"final_answer": "done"}

    monkeypatch.setattr(nodes, "plan_route_node", plan_route)
    monkeypatch.setattr(nodes, "execute_attempt_node", execute)
    monkeypatch.setattr(nodes, "assess_node", assess)
    monkeypatch.setattr(nodes, "synthesize_attempts_node", synthesize)

    result = build_agent(tool="graph", cfg=_config()).invoke(
        {"original_query": "Question?"},
        config={"max_concurrency": 2},
    )

    assert set(started_tasks) == {"T1", "T2", "T3"}
    assert max_running == 2
    assert [item["task_id"] for item in result["attempts"]] == [
        "T1", "T2", "T3"
    ]
    assert len(synthesis_calls) == 1


@pytest.mark.parametrize("tool", ["graph", "vector"])
def test_selected_tool_controls_initial_action_and_retry(monkeypatch, tool):
    llm = _HarnessLLM(_plan("initial query"), [_retry(), _accept()])
    calls = []
    results = iter([[], [_chunk()]])

    def retriever(query, top_k_chunks, cfg):
        calls.append((query, top_k_chunks))
        return {"chunks": next(results), "trace": {"status": "ok"}}

    monkeypatch.setattr(nodes, "get_llm", lambda _: llm)
    monkeypatch.setitem(nodes.RETRIEVERS, tool, retriever)

    result = build_agent(tool=tool, cfg=_config(top_k=7)).invoke({
        "original_query": "Question?",
    })

    assert calls == [("initial query", 7), ("focused retry query", 7)]
    assert {attempt["action"]["tool"] for attempt in result["attempts"]} == {
        tool
    }
    assert result["tasks"][0]["requirement"]["requirement_id"] == "T1-R1"
    assert result["completed_tasks"][0]["sufficient"] is True
    assert result["final_answer"] == "Grounded answer [1]. Invalid."
    assess_prompts = [
        prompt
        for prompt in llm.system_prompts
        if prompt.startswith(ASSESS_SYSTEM_PROMPT)
    ]
    assert all(f"fixed to `{tool}`" in prompt for prompt in assess_prompts)


def test_retry_trace_contains_only_fixed_tool_and_query(monkeypatch):
    llm = _HarnessLLM(_plan(), [_retry(), _accept()])
    events = []
    results = iter([[], [_chunk()]])
    monkeypatch.setattr(nodes, "get_llm", lambda _: llm)
    monkeypatch.setitem(
        nodes.RETRIEVERS,
        "graph",
        lambda **_: {"chunks": next(results), "trace": {}},
    )
    build_agent(
        tool="graph",
        cfg=_config(),
        trace_callback=events.append,
    ).invoke({"original_query": "Question?"})

    retry = next(event for event in events if event["stage"] == "retry")
    assert retry["details"] == {
        "tool": "graph",
        "retry_query": "focused retry query",
    }


def test_build_agent_rejects_invalid_tool():
    with pytest.raises(ValueError, match="Unsupported Tool"):
        build_agent(tool="hybrid", cfg=_config())
