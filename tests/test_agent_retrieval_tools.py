from types import SimpleNamespace

import semigraph.agent.tools as agent_tools
from semigraph.agent.contracts import ToolName
from semigraph.agent.retry_policy import TOOL_RETRY_PROFILES


def _config() -> SimpleNamespace:
    return SimpleNamespace(
        agent_retrieval={
            "vector": {
                "candidate_pool_k": 100,
                "final_rerank": "none",
            },
            "graph": {
                "top_k_entities": 20,
                "top_k_triples": 5,
                "top_k_chunk_seeds": 5,
                "chunk_seed_vector_index": "chunk_embedding",
                "damping": 0.5,
                "use_expansion": False,
                "seed_mode": "triple",
                "rerank_mode": "legacy",
                "candidate_pool_k": 100,
                "final_rerank": "none",
                "ppr_seed_weight_mode": "uniform",
                "ppr_graph_mode": "entity_chunk",
                "triple_filter": "none",
            },
        }
    )


def test_agent_vector_search_uses_phase_t_profile(monkeypatch):
    captured = {}

    def fake_trace_vector_search(**kwargs):
        captured.update(kwargs)
        chunks = [{"chunk_id": "vector-1", "text": "evidence"}]
        return {
            "candidate_pool_k": kwargs["candidate_pool_k"],
            "final_rerank": kwargs["final_rerank"],
            "raw_chunk_candidates": chunks,
            "reranked_chunks": chunks,
            "reranker_trace": {"status": "ok"},
            "chunks": chunks,
        }

    monkeypatch.setattr(agent_tools, "trace_vector_search", fake_trace_vector_search)

    result = agent_tools.agent_vector_search("AMD strategy", 5, _config())

    assert captured["top_k_chunks"] == 5
    assert captured["candidate_pool_k"] == 100
    assert captured["final_rerank"] == "none"
    assert result["chunks"][0]["chunk_id"] == "vector-1"
    assert result["trace"]["profile"] == "phase_t"
    assert result["trace"]["reranker"]["status"] == "ok"


def test_agent_graph_search_uses_phase_t_profile(monkeypatch):
    captured = {}

    def fake_trace_graph_search(**kwargs):
        captured.update(kwargs)
        chunks = [{"chunk_id": "graph-1", "text": "evidence"}]
        return {
            **kwargs,
            "effective_query": kwargs["query"],
            "seeds": [{"name": "amd", "type": "Company", "similarity": 0.9}],
            "triple_filter_trace": {
                "reason": "llm_selection",
                "fallback": False,
                "attempts": 1,
                "selected_candidate_ids": [0],
                "rejected_candidate_ids": [1],
                "candidates_after_filter": [{
                    "candidate_id": 0,
                    "head": "amd",
                    "relation": "DEPENDS_ON",
                    "tail": "tsmc",
                    "similarity": 0.9,
                }],
            },
            "ppr_entities": [{"name": "amd", "type": "Company", "score": 1.0}],
            "projection": {"node_count": 10, "relationship_count": 20},
            "raw_chunk_candidates": chunks,
            "reranked_chunks": chunks,
            "reranker_trace": {"status": "ok"},
            "chunks": chunks,
            "abort_reason": None,
        }

    monkeypatch.setattr(agent_tools, "trace_graph_search", fake_trace_graph_search)

    result = agent_tools.agent_graph_search("AMD TSMC dependency", 5, _config())

    assert captured["top_k_entities"] == 20
    assert captured["top_k_triples"] == 5
    assert captured["top_k_chunk_seeds"] == 5
    assert captured["chunk_seed_vector_index"] == "chunk_embedding"
    assert captured["damping"] == 0.5
    assert captured["use_expansion"] is False
    assert captured["seed_mode"] == "triple"
    assert captured["rerank_mode"] == "legacy"
    assert captured["candidate_pool_k"] == 100
    assert captured["final_rerank"] == "none"
    assert captured["ppr_seed_weight_mode"] == "uniform"
    assert captured["ppr_graph_mode"] == "entity_chunk"
    assert captured["graph_triple_filter"] == "none"
    assert result["trace"]["seed_count"] == 1
    assert result["trace"]["triple_filter"]["reason"] == "llm_selection"
    assert result["trace"]["returned_chunk_ids"] == ["graph-1"]


def test_agent_financial_search_passes_query_only_and_compacts_trace(monkeypatch):
    captured = {}
    chunks = [{"chunk_id": "fin-1", "metric": "revenue", "value": "100"}]

    def fake_financial_search(**kwargs):
        captured.update(kwargs)
        return {
            "chunks": chunks,
            "trace": {
                "retriever": "financial",
                "profile": "postgresql_typed_v1",
                "query_spec": {
                    "tickers": ["NVDA"],
                    "metrics": ["revenue"],
                    "operation": "lookup",
                },
                "template_id": "periodic.lookup.latest.v1",
                "bound_params": {
                    "tickers": ["NVDA"],
                    "metrics": ["revenue"],
                },
                "returned_count": 1,
                "latency_sec": 0.12,
                "missing_count": 0,
            },
        }

    monkeypatch.setattr(agent_tools, "financial_search", fake_financial_search)

    result = agent_tools.agent_financial_search("NVDA revenue", 5, "cfg")

    assert captured == {
        "query": "NVDA revenue",
        "top_k_chunks": 5,
        "cfg": "cfg",
    }
    assert result["chunks"] == chunks
    assert result["trace"]["parameters"] == {
        "top_k_chunks": 5,
        "template_id": "periodic.lookup.latest.v1",
        "bound_params": {
            "tickers": ["NVDA"],
            "metrics": ["revenue"],
        },
    }
    assert result["trace"]["backend_latency_sec"] == 0.12
    assert result["trace"]["returned_chunk_ids"] == ["fin-1"]


def test_agent_tool_registries_have_one_consistent_tool_set():
    expected_tools = {tool.value for tool in ToolName}

    assert set(agent_tools.RETRIEVERS) == expected_tools
    assert set(TOOL_RETRY_PROFILES) == set(ToolName)
    assert all(callable(retriever) for retriever in agent_tools.RETRIEVERS.values())


def test_agent_news_search_returns_chunks_and_trace(monkeypatch):
    chunks = [{"chunk_id": "news-1", "text": "headline"}]
    monkeypatch.setattr(agent_tools, "news_search", lambda **_: chunks)

    result = agent_tools.agent_news_search("NVDA latest news", 5, "cfg")

    assert result["chunks"] == chunks
    assert result["trace"] == {
        "retriever": "news",
        "profile": "finnhub_news_v1",
        "returned_chunk_ids": ["news-1"],
    }
