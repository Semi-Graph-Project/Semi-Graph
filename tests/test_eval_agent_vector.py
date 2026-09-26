from types import SimpleNamespace

import pytest

from eval_scripts import eval_agent
from eval_scripts import evaluate
import semigraph.agent.graph as agent_graph
import semigraph.agent.nodes as agent_nodes


class _FakeResponse:
    def __init__(self, content):
        self.content = content


class _FakeLLM:
    DEFAULT_FINAL_ANSWER = "Grounded evaluation answer [C1]"
    DEFAULT_ANSWER = (
        '{"parts":[{"requested_part":"Question?",'
        '"supported_facts":[{"claim":"Grounded fact",'
        '"evidence_ids":["C1"]}],"missing_information":null,'
        f'"answer":"{DEFAULT_FINAL_ANSWER}"}}],'
        f'"final_answer":"{DEFAULT_FINAL_ANSWER}"}}'
    )

    def __init__(self, responses=None):
        self.messages = []
        self.responses = list(responses or [])

    def invoke(self, messages):
        self.messages.append(messages)
        response = self.responses.pop(0) if self.responses else self.DEFAULT_ANSWER
        if isinstance(response, Exception):
            raise response
        return _FakeResponse(response)


def test_eval_synthesize_uses_assess_selected_chunks(monkeypatch):
    llm = _FakeLLM()
    monkeypatch.setattr(
        eval_agent,
        "get_config",
        lambda: SimpleNamespace(
            agent_max_synthesis_chunks=10, eval_answer_audit_enabled=True,
        ),
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

    assert result["final_answer"] == _FakeLLM.DEFAULT_FINAL_ANSWER
    assert result["synthesis_trace"]["selected_chunk_ids"] == ["C1"]
    assert result["synthesis_trace"]["status"] == "ok"
    assert result["synthesis_trace"]["max_chunks"] == 10
    assert result["synthesis_trace"]["llm_calls"] == 2
    assert result["synthesis_trace"]["citation_status"] == "valid"
    assert result["synthesis_trace"]["cited_chunk_ids"] == ["C1"]
    assert result["synthesis_trace"]["parts"][0]["requested_part"] == "Question?"
    assert len(llm.messages) == 2
    assert "chunk_id=C1" in llm.messages[0][1]["content"]
    system_prompt = llm.messages[0][0]["content"]
    assert "preserve question" in system_prompt
    assert "Return exactly one JSON object" in system_prompt
    assert "Include every requested part exactly once" in system_prompt
    assert "scan all supplied chunks" in system_prompt
    assert "sufficient" in system_prompt and "premises" in system_prompt
    assert "Do not invent a missing premise" in system_prompt
    assert "exact chunk_id in square brackets" in system_prompt
    assert 'exactly "Do not Answer"' in system_prompt
    assert "do not round intermediate values" in system_prompt
    assert "denominator" in system_prompt and "formula" in system_prompt
    assert "Keep every supported subfact" in system_prompt
    assert "Never choose" in system_prompt and "silently" in system_prompt
    assert "1,500" in system_prompt
    assert "final evidence auditor" in llm.messages[1][0]["content"]
    assert "Draft Answer" in llm.messages[1][1]["content"]
    assert _FakeLLM.DEFAULT_ANSWER in llm.messages[1][1]["content"]


def test_answer_audit_runs_when_draft_call_fails():
    llm = _FakeLLM([
        TimeoutError("draft failed"),
        "Audited answer [C1]",
    ])

    answer = eval_agent.generate_final_answer(
        llm,
        "Question?",
        [{"chunk_id": "C1", "text": "Evidence"}],
        audit_enabled=True,
    )

    assert answer == "Audited answer [C1]"
    assert len(llm.messages) == 2
    assert "Draft unavailable" in llm.messages[1][1]["content"]


def test_valid_draft_is_fallback_when_audit_call_fails():
    draft = "Supported part [C1]. The evidence does not contain the remaining detail."
    llm = _FakeLLM([draft, TimeoutError("audit failed")])

    answer = eval_agent.generate_final_answer(
        llm,
        "Question?",
        [{"chunk_id": "C1", "text": "Evidence"}],
        audit_enabled=True,
    )

    assert answer == draft


def test_answer_generation_never_returns_blank():
    llm = _FakeLLM(["", "   "])

    answer = eval_agent.generate_final_answer(
        llm,
        "Question?",
        [{"chunk_id": "C1", "text": "Evidence"}],
        audit_enabled=True,
    )

    assert answer == eval_agent.GENERATION_ERROR_ANSWER


def test_all_full_answer_modes_share_the_same_generator():
    assert evaluate.generate_final_answer is eval_agent.generate_final_answer


def test_structured_synthesis_returns_only_final_answer():
    llm = _FakeLLM()

    answer = eval_agent.generate_final_answer(
        llm,
        "Question?",
        [{"chunk_id": "C1", "text": "Evidence"}],
        audit_enabled=False,
    )

    assert answer == _FakeLLM.DEFAULT_FINAL_ANSWER
    assert len(llm.messages) == 1


def test_structured_synthesis_records_parts_and_citation_diagnostics():
    llm = _FakeLLM()
    trace = {}

    answer = eval_agent.generate_final_answer(
        llm,
        "Question?",
        [{"chunk_id": "C1", "text": "Evidence"}],
        audit_enabled=False,
        synthesis_trace=trace,
    )

    assert answer == _FakeLLM.DEFAULT_FINAL_ANSWER
    assert trace["output_format"] == "structured_json"
    assert trace["parts"][0]["supported_facts"][0]["evidence_ids"] == ["C1"]
    assert trace["cited_chunk_ids"] == ["C1"]
    assert trace["invalid_citation_ids"] == []
    assert trace["citation_status"] == "valid"


def test_synthesis_trace_flags_unknown_and_missing_citations():
    unknown_trace = {}
    unknown_llm = _FakeLLM([
        '{"parts":[],"final_answer":"Claim [C9]"}',
    ])
    eval_agent.generate_final_answer(
        unknown_llm,
        "Question?",
        [{"chunk_id": "C1", "text": "Evidence"}],
        audit_enabled=False,
        synthesis_trace=unknown_trace,
    )

    missing_trace = {}
    missing_llm = _FakeLLM([
        '{"parts":[],"final_answer":"Claim without citation"}',
    ])
    eval_agent.generate_final_answer(
        missing_llm,
        "Question?",
        [{"chunk_id": "C1", "text": "Evidence"}],
        audit_enabled=False,
        synthesis_trace=missing_trace,
    )

    assert unknown_trace["invalid_citation_ids"] == ["C9"]
    assert unknown_trace["citation_status"] == "invalid"
    assert missing_trace["citation_status"] == "missing"


@pytest.mark.parametrize("audit_enabled,expected_calls", [(True, 2), (False, 1)])
def test_answer_audit_switch_is_read_from_config(monkeypatch, audit_enabled, expected_calls):
    monkeypatch.setattr(eval_agent, "get_config", lambda: SimpleNamespace(
        eval_answer_audit_enabled=audit_enabled,
    ))
    llm = _FakeLLM(["Draft answer [C1]", "Audited answer [C1]"])
    answer = eval_agent.generate_final_answer(
        llm, "Question?", [{"chunk_id": "C1", "text": "Evidence"}],
    )
    assert len(llm.messages) == expected_calls
    assert answer == ("Audited answer [C1]" if audit_enabled else "Draft answer [C1]")


@pytest.mark.parametrize("draft", ["", TimeoutError("draft failed")])
def test_disabled_audit_does_not_make_second_call_when_draft_fails(draft):
    llm = _FakeLLM([draft, "Audit must not run"])
    answer = eval_agent.generate_final_answer(
        llm, "Question?", [{"chunk_id": "C1", "text": "Evidence"}],
        audit_enabled=False,
    )
    assert answer == eval_agent.GENERATION_ERROR_ANSWER
    assert len(llm.messages) == 1


def test_answer_without_evidence_skips_both_calls():
    llm = _FakeLLM()
    assert eval_agent.generate_final_answer(llm, "Question?", []) == eval_agent.DO_NOT_ANSWER
    assert llm.messages == []


def test_eval_synthesize_trace_reports_one_call_without_audit(monkeypatch):
    monkeypatch.setattr(eval_agent, "get_config", lambda: SimpleNamespace(
        agent_max_synthesis_chunks=10, eval_answer_audit_enabled=False,
    ))
    llm = _FakeLLM()
    monkeypatch.setattr(eval_agent, "get_llm", lambda cfg: llm)
    result = eval_agent.eval_synthesize_node({
        "original_query": "Question?",
        "attempts": [{
            "task_id": "T1",
            "chunks": [{"chunk_id": "C1", "text": "Evidence"}],
            "assessment": {"status": "valid", "output": {"accepted_chunk_ids": ["C1"]}},
        }],
    })
    assert result["synthesis_trace"]["llm_calls"] == 1
    assert result["synthesis_trace"]["answer_audit_enabled"] is False
    assert result["final_answer"] == _FakeLLM.DEFAULT_FINAL_ANSWER
    assert len(llm.messages) == 1


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

    assert result["final_answer"] == "Do not Answer"
    assert result["synthesis_trace"]["status"] == "no_evidence"


def test_vector_eval_graph_uses_production_builder(monkeypatch):
    cfg = SimpleNamespace(
        neo4j_uri="",
        controlled_neo4j_uri="bolt://neo4j-controlled:7687",
        agent_retrieval={"vector": {}},
        agent_top_k_chunks=5,
    )
    captured = {}
    graph = object()

    def fake_build_agent(**kwargs):
        captured.update(kwargs)
        return graph

    monkeypatch.setattr(eval_agent, "get_config", lambda: cfg)
    monkeypatch.setattr(eval_agent, "build_agent", fake_build_agent)

    result = eval_agent.build_vector_eval_graph()

    assert result is graph
    assert captured["tool"] == "vector"
    assert "top_k" not in captured
    assert callable(captured["synthesis"])
    assert cfg.neo4j_uri == cfg.controlled_neo4j_uri
    assert cfg.agent_retrieval["vector"]["vector_index"] == (
        eval_agent.VECTOR_INDEX
    )


def test_agent_vector_search_accepts_eval_vector_index(monkeypatch):
    captured = {}

    def fake_trace_vector_search(**kwargs):
        captured.update(kwargs)
        chunks = [{"chunk_id": "C1", "text": "evidence"}]
        return {
            "candidate_pool_k": kwargs["candidate_pool_k"],
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
    cfg = SimpleNamespace(
        agent_max_parallel_tasks=2,
        agent_max_synthesis_chunks=10,
        eval_answer_audit_enabled=True,
        agent_top_k_chunks=5,
        neo4j_uri="",
        controlled_neo4j_uri="bolt://neo4j-controlled:7687",
        agent_retrieval={"vector": {}},
    )
    monkeypatch.setattr(eval_agent, "get_config", lambda: cfg)
    monkeypatch.setattr(agent_graph, "get_config", lambda: cfg)
    monkeypatch.setattr(
        eval_agent,
        "get_llm",
        lambda _cfg: _FakeLLM(),
    )

    task = {
        "task_id": "T1",
        "query": "Find Intel product evidence",
        "requirement": {
            "requirement_id": "T1-R1",
            "description": "Intel product evidence",
        },
        "initial_action": {
            "tool": "graph",
            "query": "Intel products",
            "top_k_chunks": 99,
        },
    }

    def plan_route(_state, tool, cfg=None):
        selected_task = {
            **task,
            "initial_action": {
                **task["initial_action"],
                "tool": tool,
                "top_k_chunks": cfg.agent_top_k_chunks,
            },
        }
        return {"tasks": [selected_task]}

    def execute(state, cfg=None):
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

    def assess(state, tool, cfg=None):
        attempt = {
            **state["attempts"][-1],
            "assessment": {
                "status": "valid",
                "output": {
                    "accepted_chunk_ids": ["C1"],
                    "requirement_covered": True,
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

    monkeypatch.setattr(agent_nodes, "plan_route_node", plan_route)
    monkeypatch.setattr(agent_nodes, "execute_attempt_node", execute)
    monkeypatch.setattr(agent_nodes, "assess_node", assess)

    result = eval_agent.build_vector_eval_graph().invoke({
        "original_query": "What did Intel report?",
    })

    assert result["attempts"][0]["action"]["tool"] == "vector"
    assert result["final_answer"] == _FakeLLM.DEFAULT_FINAL_ANSWER
    assert result["synthesis_trace"]["selected_chunk_ids"] == ["C1"]
