import pytest

import semigraph.online.graph_search as graph_search_module


def test_entity_chunk_mode_returns_direct_ppr_chunks_without_mapping(monkeypatch):
    seeds = [{
        "name": "intel",
        "type": "COMP",
        "similarity": 0.9,
        "specificity": 1.0,
    }]
    passage_chunks = [
        {"chunk_id": "chunk-1", "score": 0.90},
        {"chunk_id": "chunk-2", "score": 0.80},
        {"chunk_id": "chunk-3", "score": 0.70},
    ]
    calls: dict = {}

    monkeypatch.setattr(
        graph_search_module,
        "_select_seeds",
        lambda *args, **kwargs: (seeds, {"mode": "none", "applied": False}),
    )

    def fake_run_passage_ppr(received_seeds, **kwargs):
        calls["seeds"] = received_seeds
        calls.update(kwargs)
        return {
            "chunks": passage_chunks,
            "ppr_entities": [{"name": "intel", "type": "COMP", "score": 0.4}],
            "projection": {"node_count": 12, "relationship_count": 24},
            "seeds": seeds,
        }

    monkeypatch.setattr(
        graph_search_module,
        "run_passage_ppr",
        fake_run_passage_ppr,
    )

    def mapping_must_not_run(*args, **kwargs):
        raise AssertionError("entity_chunk mode must not map entities back to chunks")

    monkeypatch.setattr(graph_search_module, "run_ppr", mapping_must_not_run)
    monkeypatch.setattr(graph_search_module, "_cluster_aliases", mapping_must_not_run)
    monkeypatch.setattr(graph_search_module, "_collapse_clusters", mapping_must_not_run)
    monkeypatch.setattr(graph_search_module, "_map_chunks", mapping_must_not_run)

    trace = graph_search_module.trace_graph_search(
        "Intel operating income",
        top_k_chunks=2,
        top_k_entities=7,
        damping=0.5,
        use_expansion=False,
        candidate_pool_k=3,
        ppr_seed_weight_mode="similarity_specificity",
        ppr_graph_mode="entity_chunk",
    )

    assert calls["seeds"] == seeds
    assert calls["top_k_chunks"] == 3
    assert calls["top_k_entities"] == 7
    assert calls["damping"] == 0.5
    assert calls["seed_weight_mode"] == "similarity_specificity"
    assert trace["chunks"] == passage_chunks[:2]
    assert trace["chunk_candidates"] == passage_chunks
    assert trace["ppr_entities"] == [
        {"name": "intel", "type": "COMP", "score": 0.4},
    ]
    assert trace["projection"] == {"node_count": 12, "relationship_count": 24}
    assert trace["direct_chunk_ppr"] is True


def test_llm_triple_filter_selects_candidates_before_seed_conversion(monkeypatch):
    candidates = [
        {"candidate_id": 0, "head": "AMD", "relation": "SUPPLIES", "tail": "TSMC"},
        {"candidate_id": 1, "head": "AMD", "relation": "USES", "tail": "HBM"},
    ]
    selected = [candidates[1]]
    filter_trace = {
        "selected_candidate_ids": [1],
        "fallback": False,
        "reason": "llm_selection",
    }

    monkeypatch.setattr(
        graph_search_module,
        "query_to_triple_candidates",
        lambda *args, **kwargs: candidates,
    )
    monkeypatch.setattr(
        graph_search_module,
        "filter_triple_candidates",
        lambda query, received, **kwargs: (selected, filter_trace),
    )
    monkeypatch.setattr(
        graph_search_module,
        "triple_candidates_to_seeds",
        lambda received: [{"name": "HBM", "type": "COMP"}],
    )

    seeds, trace = graph_search_module._select_seeds(
        "AMD memory",
        seed_mode="triple",
        top_k_triples=8,
        triple_filter_mode="llm",
    )

    assert seeds == [{"name": "HBM", "type": "COMP"}]
    assert trace["mode"] == "llm"
    assert trace["applied"] is True
    assert trace["selected_candidate_ids"] == [1]


def test_chunk_only_selects_vector_chunks_without_triple_filter(monkeypatch):
    expected = [{"chunk_id": "chunk-1", "similarity": 0.9, "specificity": 1.0}]
    captured = {}

    def fake_chunk_seeds(query, **kwargs):
        captured["query"] = query
        captured.update(kwargs)
        return expected

    def triple_filter_must_not_run(*args, **kwargs):
        raise AssertionError("chunk_only must not call the LLM triple filter")

    monkeypatch.setattr(graph_search_module, "query_to_chunk_seeds", fake_chunk_seeds)
    monkeypatch.setattr(
        graph_search_module,
        "filter_triple_candidates",
        triple_filter_must_not_run,
    )

    seeds, trace = graph_search_module._select_seeds(
        "AMD revenue",
        seed_mode="chunk_only",
        top_k_triples=20,
        top_k_chunk_seeds=4,
        chunk_seed_vector_index="gold_chunk_embedding",
        triple_filter_mode="llm",
        cfg="cfg-sentinel",
    )

    assert seeds == expected
    assert captured == {
        "query": "AMD revenue",
        "top_k": 4,
        "vector_index": "gold_chunk_embedding",
        "cfg": "cfg-sentinel",
    }
    assert trace == {
        "mode": "none",
        "applied": False,
        "reason": "chunk_only_mode",
    }


def test_chunk_only_requires_entity_chunk_projection():
    with pytest.raises(
        ValueError,
        match="chunk_only seed mode requires ppr_graph_mode='entity_chunk'",
    ):
        graph_search_module.trace_graph_search(
            "AMD revenue",
            seed_mode="chunk_only",
            ppr_graph_mode="entity_only",
            use_expansion=False,
        )
