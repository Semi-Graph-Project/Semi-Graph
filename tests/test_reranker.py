from types import SimpleNamespace

import pytest

from semigraph.online import vector_search as vector_search_module
from semigraph.online.rerank import company_rerank, fiscal_year_rerank


def _cfg():
    return SimpleNamespace(
        tickers=["INTC", "NVDA"],
        graph_repair_filer_aliases={"INTC": "Intel", "NVDA": "NVIDIA"},
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
