"""Exercise real Deep Agents tool/subagent loops without a paid LLM or Neo4j."""

import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

pytest.importorskip("deepagents")

from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage

from semigraph.agents import nodes
from semigraph.agents.prompts import SYNTHESIZE_ATTEMPTS_SYSTEM_PROMPT
from semigraph.deepagents import agent as implementation
from semigraph.deepagents import Deepagent


class ScriptedModel(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self


def call(name, **args):
    return AIMessage(content="", tool_calls=[{
        "name": name, "args": args, "id": f"call-{name}", "type": "tool_call",
    }])


@pytest.fixture(autouse=True)
def disable_external_tracing(monkeypatch):
    monkeypatch.setenv("LANGSMITH_TRACING", "false")
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "false")


@pytest.fixture
def cfg():
    return SimpleNamespace(
        agent_max_planned_tasks=2,
        agent_max_attempts_per_task=2,
        agent_max_synthesis_chunks=3,
        agent_max_parallel_tasks=2,
        agent_top_k_chunks=4,
        llm_json_mode=False,
    )


@pytest.fixture
def chunks():
    return [
        {"chunk_id": "C1", "text": "Company discloses product A.", "score": 0.8},
        {"chunk_id": "C2", "text": "Company discloses product B.", "score": 0.7},
    ]


def setup_search(monkeypatch, chunks, responses):
    model = ScriptedModel(responses=responses)
    monkeypatch.setattr(implementation, "get_llm", lambda cfg: model)
    retriever = Mock(return_value=chunks)
    monkeypatch.setattr(implementation, "retrieve_vector", retriever)
    return retriever


def test_retrieve_only_runs_real_tool_loop_and_never_synthesizes(monkeypatch, cfg, chunks):
    retriever = setup_search(monkeypatch, chunks, [
        call("write_todos", todos=[{"content": "Find product evidence", "status": "in_progress"}]),
        call("search_vector", query="Company products"),
        call("EvidenceSelection", chunk_ids=["C2", "C1", "C2"]),
    ])
    synthesize = Mock(side_effect=AssertionError("Must not synthesize"))
    monkeypatch.setattr(implementation, "synthesize_node", synthesize)

    result = Deepagent("What products?", "vector", False, cfg=cfg)

    assert result["chunks"] == [chunks[1], chunks[0]]
    assert result["final_answer"] == ""
    assert result["answer_latency_ms"] == 0
    assert result["answer_error"] is None
    assert result["synthesis_trace"] is None
    retriever.assert_called_once_with(
        query="Company products", top_k_chunks=cfg.agent_top_k_chunks, cfg=cfg,
    )
    synthesize.assert_not_called()
    assert result["retrieval_trace"]["searches"][0]["chunk_ids"] == ["C1", "C2"]
    json.dumps(result)  # The evaluator can persist the complete result.


def test_full_answer_reuses_agents_synthesis_prompt_and_selected_chunks(monkeypatch, cfg, chunks):
    setup_search(monkeypatch, chunks, [
        call("search_vector", query="Company products"),
        call("EvidenceSelection", chunk_ids=["C2"]),
    ])
    synthesis_llm = Mock()
    synthesis_llm.invoke.return_value = AIMessage(content=json.dumps({
        "parts": [{
            "requested_part": "Products",
            "supported_facts": [{"claim": "Product B", "evidence_ids": ["C2"]}],
            "missing_information": None,
            "answer": "Company discloses product B.",
        }],
        "final_answer": "Company discloses product B.",
    }))
    monkeypatch.setattr(nodes, "get_llm", lambda cfg: synthesis_llm)

    result = Deepagent("What products?", cfg=cfg)

    assert result["chunks"] == [chunks[1]]
    assert result["final_answer"] == "Company discloses product B. [C2]"
    assert result["synthesis_trace"]["cited_chunk_ids"] == ["C2"]
    assert result["answer_latency_ms"] >= 0
    synthesis_llm.invoke.assert_called_once()
    messages = synthesis_llm.invoke.call_args.args[0]
    assert messages[0]["content"] == SYNTHESIZE_ATTEMPTS_SYSTEM_PROMPT
    assert json.loads(messages[1]["content"])["selected_evidence"] == [chunks[1]]


def test_subagent_can_search_and_parent_can_select_its_chunks(monkeypatch, cfg, chunks):
    retriever = setup_search(monkeypatch, chunks, [
        call("task", description="Find Company products and return chunk IDs.",
             subagent_type="general-purpose"),
        call("search_vector", query="Company products"),
        AIMessage(content="C1: Company discloses product A."),
        call("EvidenceSelection", chunk_ids=["C1"]),
    ])

    result = Deepagent("What products?", FullAnswer=False, cfg=cfg)

    assert result["chunks"] == [chunks[0]]
    retriever.assert_called_once()
    assert result["retrieval_trace"]["searches"][0]["status"] == "ok"


def test_parallel_tool_calls_collect_both_results(monkeypatch, cfg, chunks):
    searches = AIMessage(content="", tool_calls=[
        {"name": "search_vector", "args": {"query": query}, "id": query, "type": "tool_call"}
        for query in ("A", "B")
    ])
    retriever = setup_search(monkeypatch, chunks, [
        searches, call("EvidenceSelection", chunk_ids=["C2", "C1"]),
    ])
    retriever.side_effect = lambda **kwargs: [chunks[0 if kwargs["query"] == "A" else 1]]
    result = Deepagent("Compare products", FullAnswer=False, cfg=cfg)
    assert result["chunks"] == [chunks[1], chunks[0]]
    assert {search["query"] for search in result["retrieval_trace"]["searches"]} == {"A", "B"}


def test_selection_cannot_invent_evidence(monkeypatch, cfg, chunks):
    setup_search(monkeypatch, chunks, [
        call("search_vector", query="Company products"),
        call("EvidenceSelection", chunk_ids=["invented-id"]),
    ])
    synthesize = Mock(side_effect=AssertionError("No valid selected evidence"))
    monkeypatch.setattr(implementation, "synthesize_node", synthesize)
    result = Deepagent("What products?", FullAnswer=True, cfg=cfg)
    assert result["chunks"] == []
    assert result["final_answer"] == "Do not Answer"
    assert result["retrieval_trace"]["rejected_chunk_ids"] == ["invented-id"]
    synthesize.assert_not_called()


def test_invalid_ids_do_not_discard_valid_evidence_or_use_the_cap(monkeypatch, cfg, chunks):
    cfg.agent_max_synthesis_chunks = 1
    setup_search(monkeypatch, chunks, [
        call("search_vector", query="Company products"),
        call("EvidenceSelection", chunk_ids=["invented-id", "C2", "C2", "C1"]),
    ])
    result = Deepagent("What products?", FullAnswer=False, cfg=cfg)
    assert result["chunks"] == [chunks[1]]
    assert result["retrieval_trace"]["selected_chunk_ids"] == ["C2"]
    assert result["retrieval_trace"]["rejected_chunk_ids"] == ["invented-id"]


def test_evidence_cap_preserves_agent_ranking(monkeypatch, cfg, chunks):
    cfg.agent_max_synthesis_chunks = 1
    setup_search(monkeypatch, chunks, [
        call("search_vector", query="Company products"),
        call("EvidenceSelection", chunk_ids=["C2", "C1"]),
    ])
    result = Deepagent("What products?", FullAnswer=False, cfg=cfg)
    assert result["chunks"] == [chunks[1]]


def test_empty_search_returns_no_answer_without_synthesis(monkeypatch, cfg):
    setup_search(monkeypatch, [], [
        call("search_vector", query="Company products"),
        call("EvidenceSelection", chunk_ids=[]),
    ])
    synthesize = Mock(side_effect=AssertionError("No evidence to synthesize"))
    monkeypatch.setattr(implementation, "synthesize_node", synthesize)
    result = Deepagent("What products?", cfg=cfg)
    assert result["chunks"] == []
    assert result["final_answer"] == "Do not Answer"
    assert result["synthesis_trace"]["llm_calls"] == 0
    synthesize.assert_not_called()


def test_agent_must_actually_search(monkeypatch, cfg):
    retriever = setup_search(monkeypatch, [], [call("EvidenceSelection", chunk_ids=[])])
    with pytest.raises(RuntimeError, match="without a successful Vector search"):
        Deepagent("What products?", FullAnswer=False, cfg=cfg)
    retriever.assert_not_called()


def test_search_budget_is_enforced(monkeypatch, cfg, chunks):
    cfg.agent_max_planned_tasks = 1
    cfg.agent_max_attempts_per_task = 1
    retriever = setup_search(monkeypatch, chunks, [
        call("search_vector", query="First search"),
        call("search_vector", query="Second search"),
        call("EvidenceSelection", chunk_ids=["C1"]),
    ])
    result = Deepagent("What products?", FullAnswer=False, cfg=cfg)
    retriever.assert_called_once()
    assert result["chunks"] == [chunks[0]]


def test_retrieved_evidence_does_not_leak_between_runs(monkeypatch, cfg, chunks):
    setup_search(monkeypatch, chunks, [
        call("search_vector", query="First query"),
        call("EvidenceSelection", chunk_ids=["C1"]),
    ])
    Deepagent("First query", FullAnswer=False, cfg=cfg)
    setup_search(monkeypatch, [], [
        call("search_vector", query="Unrelated query"),
        call("EvidenceSelection", chunk_ids=["C1"]),
    ])
    result = Deepagent("Unrelated query", FullAnswer=False, cfg=cfg)
    assert result["chunks"] == []
    assert result["retrieval_trace"]["rejected_chunk_ids"] == ["C1"]


def test_retrieval_error_is_not_reported_as_a_successful_empty_result(monkeypatch, cfg):
    retriever = setup_search(monkeypatch, [], [
        call("search_vector", query="Company products"),
        call("EvidenceSelection", chunk_ids=[]),
    ])
    retriever.side_effect = RuntimeError("Database unavailable")
    with pytest.raises(RuntimeError):
        Deepagent("What products?", FullAnswer=False, cfg=cfg)


@pytest.mark.parametrize("query, tool", [("", "vector"), ("Question", "financial")])
def test_invalid_input_fails_before_model_call(monkeypatch, cfg, query, tool):
    llm = Mock(side_effect=AssertionError("Invalid input must not call an LLM"))
    monkeypatch.setattr(implementation, "get_llm", llm)
    with pytest.raises(ValueError):
        Deepagent(query, tool, cfg=cfg)
    llm.assert_not_called()
