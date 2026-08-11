from eval_scripts import eval_agent
from types import SimpleNamespace


class _FakeResponse:
    content = "Grounded evaluation answer"


class _FakeLLM:
    def __init__(self):
        self.messages = []

    def invoke(self, messages):
        self.messages.append(messages)
        return _FakeResponse()


def test_eval_synthesize_uses_assess_selected_chunks(monkeypatch):
    llm = _FakeLLM()
    monkeypatch.setattr(
        eval_agent,
        "get_config",
        lambda: SimpleNamespace(agent_max_synthesis_chunks=10),
    )
    monkeypatch.setattr(eval_agent, "get_llm", lambda _cfg: llm)

    result = eval_agent.eval_synthesize_node({
        "original_query": "What did Intel report?",
        "attempts": [{
            "task_id": "T1",
            "chunks": [{"chunk_id": "C1", "text": "Evidence"}],
            "assessment": {
                "status": "valid",
                "output": {"accepted_chunk_ids": ["C1"]},
            },
        }],
    })

    assert result["final_answer"] == "Grounded evaluation answer"
    assert result["synthesis_trace"]["selected_chunk_ids"] == ["C1"]
    assert result["synthesis_trace"]["status"] == "ok"
    assert result["synthesis_trace"]["max_chunks"] == 10
    assert "chunk_id=C1" in llm.messages[0][1]["content"]


def test_eval_synthesize_returns_exact_no_evidence_answer(monkeypatch):
    monkeypatch.setattr(
        eval_agent,
        "get_llm",
        lambda _cfg: (_ for _ in ()).throw(
            AssertionError("LLM must not be called without evidence")
        ),
    )

    result = eval_agent.eval_synthesize_node({
        "original_query": "Question?",
        "attempts": [],
    })

    assert result["final_answer"] == "Do not answers"
    assert result["synthesis_trace"]["status"] == "no_evidence"


def test_vector_eval_graph_has_production_fanout_fanin_flow(monkeypatch):
    monkeypatch.setattr(
        eval_agent,
        "get_config",
        lambda: SimpleNamespace(
            agent_max_parallel_tasks=2,
            agent_max_synthesis_chunks=10,
            neo4j_uri="",
            agent_retrieval={"vector": {}},
        ),
    )

    graph = eval_agent.build_vector_eval_graph(top_k=5)

    assert set(graph.get_graph().nodes) == {
        "__start__",
        "plan_route",
        "task_worker",
        "collector",
        "eval_synthesize",
        "__end__",
    }


def test_agent_vector_search_accepts_eval_vector_index(monkeypatch):
    captured = {}

    def fake_trace_vector_search(**kwargs):
        captured.update(kwargs)
        chunks = [{"chunk_id": "C1", "text": "evidence"}]
        return {
            "candidate_pool_k": kwargs["candidate_pool_k"],
            "final_rerank": kwargs["final_rerank"],
            "raw_chunk_candidates": chunks,
            "reranked_chunks": chunks,
            "reranker_trace": {},
            "chunks": chunks,
        }

    import semigraph.agent.tools as agent_tools

    monkeypatch.setattr(agent_tools, "trace_vector_search", fake_trace_vector_search)
    cfg = type("Config", (), {
        "agent_retrieval": {
            "vector": {
                "candidate_pool_k": 100,
                "final_rerank": "none",
                "vector_index": "gold_chunk_embedding",
            }
        }
    })()

    result = agent_tools.agent_vector_search("AMD strategy", 5, cfg)

    assert captured["vector_index"] == "gold_chunk_embedding"
    assert result["trace"]["parameters"]["vector_index"] == (
        "gold_chunk_embedding"
    )


def test_vector_eval_graph_runs_plan_execute_assess_and_eval_synthesis(monkeypatch):
    monkeypatch.setattr(
        eval_agent,
        "get_config",
        lambda: SimpleNamespace(
            agent_max_parallel_tasks=2,
            agent_max_synthesis_chunks=10,
            neo4j_uri="",
            agent_retrieval={"vector": {}},
        ),
    )
    monkeypatch.setattr(
        eval_agent,
        "get_llm",
        lambda _cfg: _FakeLLM(),
    )

    task = {
        "task_id": "T1",
        "query": "Find Intel product evidence",
        "requirements": [{
            "requirement_id": "T1-R1",
            "description": "Intel product evidence",
        }],
        "initial_action": {
            "tool": "graph",
            "query": "Intel products",
            "top_k_chunks": 99,
        },
    }

    def plan_route(_state):
        return {"tasks": [task]}

    def execute(state):
        attempt = {
            "attempt_id": "T1-A1",
            "task_id": "T1",
            "action": dict(state["current_action"]),
            "retrieval_status": "ok",
            "chunks": [{"chunk_id": "C1", "text": "Intel evidence"}],
            "retrieval_trace": {},
            "assessment": None,
        }
        return {
            "attempts": [attempt],
            "current_action": dict(state["current_action"]),
        }

    def assess(state):
        attempt = {
            **state["attempts"][-1],
            "assessment": {
                "status": "valid",
                "output": {
                    "accepted_chunk_ids": ["C1"],
                    "covered_requirement_ids": ["T1-R1"],
                },
            },
        }
        return {
            "attempts": [attempt],
            "completion": {
                "task_id": "T1",
                "sufficient": True,
                "stop_reason": "sufficient",
            },
            "current_action": {},
            "stop_reason": "sufficient",
        }

    monkeypatch.setattr(eval_agent.agent_nodes, "plan_route_node", plan_route)
    monkeypatch.setattr(eval_agent.agent_nodes, "execute_attempt_node", execute)
    monkeypatch.setattr(eval_agent.agent_nodes, "assess_node", assess)

    result = eval_agent.build_vector_eval_graph().invoke({
        "original_query": "What did Intel report?",
    })

    assert result["attempts"][0]["action"]["tool"] == "vector"
    assert result["final_answer"] == "Grounded evaluation answer"
    assert result["synthesis_trace"]["selected_chunk_ids"] == ["C1"]
