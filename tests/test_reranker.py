from types import SimpleNamespace

import pytest

from semigraph.config import Config
from semigraph.online import rerank as rerank_module
from semigraph.online import vector_search as vector_search_module
from semigraph.online.rerank import company_rerank, fiscal_year_rerank


def _cfg(rerank_mode="company+fiscal_year"):
    return SimpleNamespace(
        tickers=["INTC", "NVDA"],
        graph_repair_filer_aliases={"INTC": "Intel", "NVDA": "NVIDIA"},
        agent_retrieval={"vector": {"rerank_mode": rerank_mode}},
    )


def test_company_rerank_boosts_matching_company():
    chunks = [
        {"chunk_id": "INTC_001", "score": 0.9},
        {"chunk_id": "NVDA_001", "score": 0.8},
    ]

    ranked = company_rerank("NVIDIA main business", chunks, cfg=_cfg())

    assert [chunk["chunk_id"] for chunk in ranked] == ["NVDA_001", "INTC_001"]
    assert ranked[0]["score"] == 1.0


def test_fiscal_year_rerank_boosts_matching_year():
    chunks = [
        {"chunk_id": "NVDA_2023", "fiscal_year": 2023, "score": 0.9},
        {"chunk_id": "NVDA_2024", "fiscal_year": "2024", "score": 0.8},
    ]

    ranked = fiscal_year_rerank("NVIDIA revenue in 2024", chunks)

    assert [chunk["chunk_id"] for chunk in ranked] == ["NVDA_2024", "NVDA_2023"]
    assert ranked[0]["score"] == pytest.approx(0.92)


def test_cross_encoder_rerank_sorts_by_score(monkeypatch):
    calls = {}

    def fake_predict(pairs):
        calls["pairs"] = pairs
        return [0.2, 0.9, 0.5]

    monkeypatch.setattr(rerank_module, "predict_cross_encoder_scores", fake_predict)

    chunks = [
        {"chunk_id": "chunk_a", "text": "first passage"},
        {"chunk_id": "chunk_b", "text": "second passage"},
        {"chunk_id": "chunk_c", "text": "third passage"},
    ]

    ranked = rerank_module.cross_encoder_rerank("test query", chunks)

    assert [chunk["chunk_id"] for chunk in ranked] == [
        "chunk_b",
        "chunk_c",
        "chunk_a",
    ]
    assert calls["pairs"] == [
        ("test query", "first passage"),
        ("test query", "second passage"),
        ("test query", "third passage"),
    ]


def test_cross_encoder_rerank_empty_chunks_skips_model_loading(monkeypatch):
    def fail_if_called(*args, **kwargs):
        pytest.fail("Model loading must be skipped when chunks is empty")

    monkeypatch.setattr(
        rerank_module,
        "predict_cross_encoder_scores",
        fail_if_called,
    )

    assert rerank_module.cross_encoder_rerank("test query", []) == []


@pytest.mark.parametrize(
    "chunk",
    [
        {"chunk_id": "missing_text"},
        {"chunk_id": "none_text", "text": None},
        {"chunk_id": "numeric_text", "text": 123},
    ],
)
def test_cross_encoder_rerank_rejects_invalid_text_before_loading_model(
    monkeypatch,
    chunk,
):
    def fail_if_called(*args, **kwargs):
        pytest.fail("Model loading must happen after chunk validation")

    monkeypatch.setattr(
        rerank_module,
        "predict_cross_encoder_scores",
        fail_if_called,
    )

    with pytest.raises(ValueError, match=r"chunks\[0\]\['text'\] must be a string"):
        rerank_module.cross_encoder_rerank("test query", [chunk])


@pytest.mark.parametrize("scores", [[0.9], [0.9, 0.5, 0.1]])
def test_cross_encoder_rerank_rejects_score_count_mismatch(monkeypatch, scores):
    monkeypatch.setattr(
        rerank_module,
        "predict_cross_encoder_scores",
        lambda pairs: scores,
    )
    chunks = [
        {"chunk_id": "chunk_a", "text": "first passage"},
        {"chunk_id": "chunk_b", "text": "second passage"},
    ]

    with pytest.raises(
        ValueError,
        match=rf"returned {len(scores)} scores for {len(chunks)} chunks",
    ):
        rerank_module.cross_encoder_rerank("test query", chunks)


@pytest.mark.parametrize("invalid_score", [float("nan"), float("inf"), -float("inf")])
def test_cross_encoder_rerank_rejects_non_finite_scores(
    monkeypatch,
    invalid_score,
):
    monkeypatch.setattr(
        rerank_module,
        "predict_cross_encoder_scores",
        lambda pairs: [0.9, invalid_score],
    )
    chunks = [
        {"chunk_id": "chunk_a", "text": "first passage"},
        {"chunk_id": "chunk_b", "text": "second passage"},
    ]

    with pytest.raises(ValueError, match="returned a non-finite score"):
        rerank_module.cross_encoder_rerank("test query", chunks)


def test_vector_applies_company_and_fiscal_year_rerank(monkeypatch):
    candidates = [
        {"chunk_id": "INTC_001", "fiscal_year": 2023, "score": 0.9},
        {"chunk_id": "NVDA_001", "fiscal_year": 2024, "score": 0.7},
    ]
    monkeypatch.setattr(
        vector_search_module,
        "_retrieve_chunks",
        lambda *args, **kwargs: candidates,
    )

    trace = vector_search_module.trace_vector_search(
        "NVIDIA main business in 2024",
        top_k_chunks=1,
        candidate_pool_k=2,
        cfg=_cfg(),
    )

    assert trace["chunks"][0]["chunk_id"] == "NVDA_001"
    assert trace["chunks"][0]["score"] == pytest.approx(0.7 * 1.25 * 1.15)
    assert trace["reranker_trace"]["mode"] == "company+fiscal_year"


def test_vector_can_use_cross_encoder_rerank(monkeypatch):
    candidates = [
        {"chunk_id": "chunk_a", "text": "first passage", "score": 0.9},
        {"chunk_id": "chunk_b", "text": "second passage", "score": 0.7},
    ]
    calls = {}

    monkeypatch.setattr(
        vector_search_module,
        "_retrieve_chunks",
        lambda *args, **kwargs: candidates,
    )

    def fake_cross_encoder_rerank(query, chunks):
        calls["query"] = query
        calls["chunks"] = chunks
        return [chunks[1], chunks[0]]

    monkeypatch.setattr(
        vector_search_module,
        "cross_encoder_rerank",
        fake_cross_encoder_rerank,
    )

    trace = vector_search_module.trace_vector_search(
        "test query",
        top_k_chunks=1,
        candidate_pool_k=2,
        cfg=_cfg(rerank_mode="cross_encoder"),
    )

    assert calls == {"query": "test query", "chunks": candidates}
    assert trace["chunks"] == [candidates[1]]
    assert trace["reranked_chunks"] == [candidates[1], candidates[0]]
    assert trace["reranker_trace"]["mode"] == "cross_encoder"


def test_vector_search_uses_cross_encoder_mode_from_config(monkeypatch):
    candidates = [
        {"chunk_id": "chunk_a", "text": "first passage", "score": 0.9},
        {"chunk_id": "chunk_b", "text": "second passage", "score": 0.7},
    ]
    monkeypatch.setattr(
        vector_search_module,
        "_retrieve_chunks",
        lambda *args, **kwargs: candidates,
    )
    monkeypatch.setattr(
        vector_search_module,
        "cross_encoder_rerank",
        lambda query, chunks: [chunks[1], chunks[0]],
    )

    chunks = vector_search_module.vector_search(
        "test query",
        top_k_chunks=1,
        candidate_pool_k=2,
        cfg=_cfg(rerank_mode="cross_encoder"),
    )

    assert chunks == [candidates[1]]


@pytest.mark.parametrize("retriever", ["vector", "graph"])
def test_config_rejects_unknown_rerank_mode(tmp_path, retriever):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "agent_retrieval:\n"
        f"  {retriever}:\n"
        "    rerank_mode: unknown\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match=rf"agent_retrieval\.{retriever}\.rerank_mode must be one of",
    ):
        Config(config_path)
