from types import SimpleNamespace

import pytest

import semigraph.online.graph_search as graph_search_module
import semigraph.online.rerank as rerank_module
import semigraph.online.vector_search as vector_search_module


def _config():
    return SimpleNamespace(
        openrouter_api_key="test-key",
        reranker_model="cohere/rerank-4-fast",
        reranker_provider="openrouter",
        reranker_base_url="https://example.test/v1",
        reranker_timeout_seconds=1,
        reranker_max_retries=0,
    )


def _chunks(count=2):
    return [
        {"chunk_id": f"chunk-{index}", "text": f"text-{index}"}
        for index in range(count)
    ]


def test_rerank_maps_response_index_to_original_chunk(monkeypatch):
    seen = {}

    def fake_request(payload, cfg):
        seen["payload"] = payload
        return {
            "model": "rerank-v4.0-fast",
            "results": [
                {"index": 1, "relevance_score": 0.95},
                {"index": 0, "relevance_score": 0.20},
            ],
        }

    monkeypatch.setattr(rerank_module, "_request_with_retry", fake_request)

    ranked, trace = rerank_module.rerank_chunks(
        "query",
        _chunks(),
        top_n=2,
        cfg=_config(),
        fail_open=False,
    )

    assert [chunk["chunk_id"] for chunk in ranked] == ["chunk-1", "chunk-0"]
    assert ranked[0]["original_rank"] == 2
    assert ranked[0]["rerank_score"] == 0.95
    assert seen["payload"]["documents"] == ["text-0", "text-1"]
    assert seen["payload"]["top_n"] == 2
    assert trace["status"] == "ok"


def test_rerank_invalid_indexes_fail_open(monkeypatch):
    monkeypatch.setattr(
        rerank_module,
        "_request_with_retry",
        lambda payload, cfg: {"results": [{"index": 99, "relevance_score": 1.0}]},
    )

    ranked, trace = rerank_module.rerank_chunks(
        "query",
        _chunks(),
        top_n=2,
        cfg=_config(),
    )

    assert [chunk["chunk_id"] for chunk in ranked] == ["chunk-0", "chunk-1"]
    assert trace["status"] == "fallback"
    assert trace["error_type"] == "RuntimeError"


def test_rerank_timeout_fails_open_without_mutating_input(monkeypatch):
    original = _chunks()

    def fail_request(payload, cfg):
        raise TimeoutError("timeout")

    monkeypatch.setattr(rerank_module, "_request_with_retry", fail_request)

    ranked, trace = rerank_module.rerank_chunks(
        "query",
        original,
        top_n=1,
        cfg=_config(),
    )

    assert ranked == [original[0]]
    assert ranked[0] is not original[0]
    assert trace["status"] == "fallback"
    assert trace["error_type"] == "TimeoutError"


def test_rerank_empty_input_is_skipped():
    ranked, trace = rerank_module.rerank_chunks(
        "query",
        [],
        top_n=5,
        cfg=_config(),
    )

    assert ranked == []
    assert trace["status"] == "skipped"


def test_vector_sends_only_top_20_candidates_to_reranker(monkeypatch):
    candidates = _chunks(100)
    calls = {}

    monkeypatch.setattr(
        vector_search_module,
        "_retrieve_chunks",
        lambda query, top_k_chunks, cfg: candidates[:top_k_chunks],
    )

    def fake_rerank(query, chunks, top_n, cfg, fail_open):
        calls["count"] = len(chunks)
        return chunks[:top_n], {"status": "ok", "candidate_count": len(chunks)}

    monkeypatch.setattr(vector_search_module, "rerank_chunks", fake_rerank)

    trace = vector_search_module.trace_vector_search(
        "query",
        top_k_chunks=5,
        candidate_pool_k=100,
        final_rerank="cohere",
        cfg=_config(),
    )

    assert len(trace["raw_chunk_candidates"]) == 100
    assert calls["count"] == 20
    assert len(trace["chunks"]) == 5
    assert trace["reranker_trace"]["enabled"] is True


@pytest.mark.parametrize("ppr_graph_mode", ["entity_only", "entity_chunk"])
def test_graph_sends_candidates_to_reranker(monkeypatch, ppr_graph_mode):
    candidates = _chunks(3)
    calls = {}

    monkeypatch.setattr(
        graph_search_module,
        "_select_seed_entities",
        lambda *args, **kwargs: ([{"name": "seed"}], {}),
    )
    def fake_rerank(query, chunks, top_n, cfg, fail_open):
        calls["count"] = len(chunks)
        return chunks[:top_n], {
            "status": "ok",
            "candidate_count": len(chunks),
        }

    monkeypatch.setattr(graph_search_module, "rerank_chunks", fake_rerank)

    if ppr_graph_mode == "entity_chunk":
        monkeypatch.setattr(
            graph_search_module,
            "run_passage_ppr",
            lambda seeds, **kwargs: {
                "chunks": candidates,
                "ppr_entities": [],
                "projection": {},
            },
        )
    else:
        monkeypatch.setattr(
            graph_search_module,
            "run_ppr",
            lambda seeds, **kwargs: [{"name": "entity", "score": 1.0}],
        )
        monkeypatch.setattr(
            graph_search_module,
            "_cluster_aliases",
            lambda *args, **kwargs: {"entity": ["entity"]},
        )
        monkeypatch.setattr(
            graph_search_module,
            "_collapse_clusters",
            lambda *args, **kwargs: [{"aliases": ["entity"], "score": 1.0}],
        )
        monkeypatch.setattr(
            graph_search_module,
            "_map_chunks",
            lambda *args, **kwargs: candidates,
        )

    trace = graph_search_module.trace_graph_search(
        "query",
        top_k_chunks=2,
        candidate_pool_k=3,
        use_expansion=False,
        final_rerank="cohere",
        ppr_graph_mode=ppr_graph_mode,
    )

    assert calls["count"] == 3
    assert trace["raw_chunk_candidates"] == candidates
    assert trace["reranker_trace"]["enabled"] is True
    assert len(trace["chunks"]) == 2
