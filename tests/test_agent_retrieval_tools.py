from types import SimpleNamespace

import semigraph.agent.tools as agent_tools
from semigraph.config import Config


def _config() -> SimpleNamespace:
    return SimpleNamespace(
        agent_retrieval={
            "vector": {
                "candidate_pool_k": 100,
                "final_rerank": "cohere",
            },
            "graph": {
                "top_k_entities": 20,
                "top_k_triples": 10,
                "damping": 0.5,
                "use_expansion": False,
                "seed_mode": "triple",
                "rerank_mode": "legacy",
                "candidate_pool_k": 100,
                "final_rerank": "cohere",
                "ppr_seed_weight_mode": "uniform",
                "ppr_graph_mode": "entity_chunk",
                "triple_filter": "llm",
            },
        }
    )


def test_default_config_contains_phase_t_agent_profile():
    profiles = Config().agent_retrieval

    assert profiles["vector"] == {
        "candidate_pool_k": 100,
        "final_rerank": "cohere",
    }
    assert profiles["graph"] == {
        "top_k_entities": 20,
        "top_k_triples": 10,
        "damping": 0.5,
        "use_expansion": False,
        "seed_mode": "triple",
        "rerank_mode": "legacy",
        "candidate_pool_k": 100,
        "final_rerank": "cohere",
        "ppr_seed_weight_mode": "uniform",
        "ppr_graph_mode": "entity_chunk",
        "triple_filter": "llm",
    }


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
    assert captured["final_rerank"] == "cohere"
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
    assert captured["top_k_triples"] == 10
    assert captured["damping"] == 0.5
    assert captured["use_expansion"] is False
    assert captured["seed_mode"] == "triple"
    assert captured["rerank_mode"] == "legacy"
    assert captured["candidate_pool_k"] == 100
    assert captured["final_rerank"] == "cohere"
    assert captured["ppr_seed_weight_mode"] == "uniform"
    assert captured["ppr_graph_mode"] == "entity_chunk"
    assert captured["graph_triple_filter"] == "llm"
    assert result["trace"]["seed_count"] == 1
    assert result["trace"]["triple_filter"]["reason"] == "llm_selection"
    assert result["trace"]["returned_chunk_ids"] == ["graph-1"]
