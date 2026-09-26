from types import SimpleNamespace

import semigraph.online.graph_search as graph_search_module


def test_returns_direct_ppr_chunks(monkeypatch):
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

    trace = graph_search_module.trace_graph_search(
        "Intel operating income",
        top_k_chunks=2,
        top_k_entities=7,
        damping=0.5,
        use_expansion=False,
        candidate_pool_k=3,
        ppr_seed_weight_mode="similarity_specificity",
        cfg=SimpleNamespace(
            agent_retrieval={"graph": {"rerank_mode": "company+fiscal_year"}},
        ),
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


def test_embedding_triple_seed_trace_keeps_the_top_k_candidates(monkeypatch):
    candidates = [
        {
            "candidate_id": 0,
            "head": "Intel",
            "relation": "PRODUCES",
            "tail": "Xeon",
            "similarity": 0.91,
        },
        {
            "candidate_id": 1,
            "head": "Intel",
            "relation": "OPERATES",
            "tail": "Foundry",
            "similarity": 0.87,
        },
    ]

    monkeypatch.setattr(
        graph_search_module,
        "query_to_triple_candidates",
        lambda *args, **kwargs: candidates,
    )
    monkeypatch.setattr(
        graph_search_module,
        "triple_candidates_to_seeds",
        lambda received: [{"name": received[0]["head"]}],
    )

    seeds, trace = graph_search_module._select_seeds(
        "Intel products",
        seed_mode="triple",
        top_k_triples=2,
        triple_filter_mode="none",
    )

    assert seeds == [{"name": "Intel"}]
    assert trace["candidates_before_filter"] == candidates
    assert trace["candidates_after_filter"] == candidates
    assert trace["selected_candidate_ids"] == [0, 1]


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


def test_company_and_fiscal_year_rerank_smoke_runs_through_graph_pipeline(monkeypatch):
    seeds = [{"name": "nvidia", "type": "ORG", "similarity": 0.9}]

    monkeypatch.setattr(
        graph_search_module,
        "_select_seeds",
        lambda *args, **kwargs: (seeds, {"mode": "none", "applied": False}),
    )
    monkeypatch.setattr(
        graph_search_module,
        "run_passage_ppr",
        lambda *args, **kwargs: {
            "chunks": [
                {
                    "chunk_id": "INTC_2024_Item_1_0001",
                    "fiscal_year": 2024,
                    "score": 1.0,
                },
                {
                    "chunk_id": "NVDA_2025_Item_1_0001",
                    "fiscal_year": "2025",
                    "score": 0.9,
                },
            ],
            "ppr_entities": [],
            "projection": {},
            "seeds": seeds,
        },
    )

    trace = graph_search_module.trace_graph_search(
        "Nvidia Main Business 2025",
        top_k_chunks=1,
        use_expansion=False,
        candidate_pool_k=2,
        cfg=SimpleNamespace(
            graph_repair_filer_aliases={"NVDA": "nvidia", "INTC": "intel"},
        ),
    )

    assert trace["chunks"][0]["chunk_id"] == "NVDA_2025_Item_1_0001"
    assert trace["chunks"][0]["score"] == 0.9 * 1.25 * 1.15
    assert trace["reranker_trace"]["mode"] == "company+fiscal_year"


def test_cross_encoder_reranks_ppr_candidates_from_graph_config(monkeypatch):
    seeds = [{"name": "nvidia", "type": "ORG", "similarity": 0.9}]
    candidates = [
        {"chunk_id": "chunk_a", "text": "first passage", "score": 0.9},
        {"chunk_id": "chunk_b", "text": "second passage", "score": 0.7},
    ]
    calls = {}
    events = []
    cfg = SimpleNamespace(
        agent_retrieval={
            "graph": {"rerank_mode": "cross_encoder"},
            "vector": {"rerank_mode": "company+fiscal_year"},
        },
    )
    monkeypatch.setattr(
        graph_search_module,
        "expand_query",
        lambda *args, **kwargs: "expanded query for seeds",
    )
    monkeypatch.setattr(
        graph_search_module,
        "_select_seeds",
        lambda *args, **kwargs: (seeds, {"mode": "none", "applied": False}),
    )
    monkeypatch.setattr(
        graph_search_module,
        "run_passage_ppr",
        lambda *args, **kwargs: {
            "chunks": candidates,
            "ppr_entities": [],
            "projection": {},
            "seeds": seeds,
        },
    )

    def fake_cross_encoder(query, chunks):
        calls["query"] = query
        calls["chunks"] = chunks
        return [chunks[1], chunks[0]]

    monkeypatch.setattr(graph_search_module, "cross_encoder_rerank", fake_cross_encoder)
    trace = graph_search_module.trace_graph_search(
        "original query",
        top_k_chunks=1,
        candidate_pool_k=2,
        cfg=cfg,
        trace_callback=events.append,
    )

    assert calls == {"query": "original query", "chunks": candidates}
    assert trace["effective_query"] == "expanded query for seeds"
    assert trace["raw_chunk_candidates"] == candidates
    assert trace["reranked_chunks"] == [candidates[1], candidates[0]]
    assert trace["chunks"] == [candidates[1]]
    assert trace["rerank_mode"] == "cross_encoder"
    assert trace["metadata_rerank"] == "none"
    assert trace["reranker_trace"] == {
        "mode": "cross_encoder",
        "status": "complete",
        "candidate_count": 2,
        "returned_count": 1,
    }
    rerank_events = [event for event in events if event["stage"] == "reranking"]
    assert [event["status"] for event in rerank_events] == ["running", "complete"]
    assert all(event["details"]["mode"] == "cross_encoder" for event in rerank_events)

    chunks = graph_search_module.graph_search(
        "original query",
        top_k_chunks=1,
        candidate_pool_k=2,
        cfg=cfg,
    )
    assert chunks == [candidates[1]]


def test_cross_encoder_graph_with_no_seeds_does_not_rerank(monkeypatch):
    monkeypatch.setattr(
        graph_search_module,
        "_select_seeds",
        lambda *args, **kwargs: ([], {"mode": "none", "applied": False}),
    )

    def fail_if_called(*args, **kwargs):
        raise AssertionError("Reranker must not run when no seeds are found")

    monkeypatch.setattr(graph_search_module, "cross_encoder_rerank", fail_if_called)
    trace = graph_search_module.trace_graph_search(
        "original query",
        use_expansion=False,
        cfg=SimpleNamespace(
            agent_retrieval={"graph": {"rerank_mode": "cross_encoder"}},
        ),
    )

    assert trace["chunks"] == []
    assert trace["abort_reason"] == "no_seeds"
    assert trace["reranker_trace"] == {"mode": "cross_encoder", "status": "not_run"}
