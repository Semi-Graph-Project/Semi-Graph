from types import SimpleNamespace

import semigraph.agents.tools as agent_tools


def test_retrieve_vector_uses_agent_profile(monkeypatch):
    calls = []
    cfg = SimpleNamespace(
        agent_retrieval={
            "vector": {
                "candidate_pool_k": 50,
                "vector_index": "gold_chunk_embedding",
            }
        }
    )
    monkeypatch.setattr(
        agent_tools,
        "vector_search",
        lambda **kwargs: calls.append(kwargs) or [{"chunk_id": "c1"}],
    )

    result = agent_tools.retrieve_vector(
        query="NVIDIA risks",
        top_k_chunks=5,
        cfg=cfg,
    )

    assert result == [{"chunk_id": "c1"}]
    assert calls == [{
        "query": "NVIDIA risks",
        "top_k_chunks": 5,
        "candidate_pool_k": 50,
        "vector_index": "gold_chunk_embedding",
        "cfg": cfg,
    }]


def test_retrieve_graph_uses_agent_profile(monkeypatch):
    calls = []
    cfg = SimpleNamespace(
        agent_retrieval={
            "graph": {
                "top_k_entities": 20,
                "top_k_triples": 5,
                "top_k_chunk_seeds": 5,
                "chunk_seed_vector_index": "gold_chunk_embedding",
                "damping": 0.3,
                "use_expansion": False,
                "seed_mode": "triple",
                "candidate_pool_k": 50,
                "ppr_seed_weight_mode": "similarity_specificity",
                "triple_filter": "none",
            }
        }
    )
    monkeypatch.setattr(
        agent_tools,
        "graph_search",
        lambda **kwargs: calls.append(kwargs) or [{"chunk_id": "g1"}],
    )

    result = agent_tools.retrieve_graph(
        query="NVIDIA suppliers",
        top_k_chunks=5,
        cfg=cfg,
    )

    assert result == [{"chunk_id": "g1"}]
    assert calls[0]["chunk_seed_vector_index"] == "gold_chunk_embedding"
    assert calls[0]["candidate_pool_k"] == 50
    assert calls[0]["top_k_chunks"] == 5
    assert calls[0]["cfg"] is cfg
