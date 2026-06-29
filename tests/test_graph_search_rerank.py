from semigraph.online.graph_search import (
    _rerank_chunks_by_query_intent,
    _section_boosts_for_query,
)


def test_section_boosts_detect_risk_query():
    boosts = _section_boosts_for_query("How exposed is AMD to TSMC supply risk?")

    assert boosts["Item_1A"] > boosts.get("Item_1", 1.0)


def test_rerank_promotes_risk_factor_chunk_over_business_chunk():
    chunks = [
        {
            "chunk_id": "AMD_2026_Item_1_0010",
            "text": "AMD works with TSMC manufacturing partners.",
            "ticker": "AMD",
            "fiscal_year": "2026",
            "section": "Item_1",
            "score": 1.0,
        },
        {
            "chunk_id": "AMD_2026_Item_1A_0008",
            "text": "AMD depends on third-party foundries and faces supply risk.",
            "ticker": "AMD",
            "fiscal_year": "2026",
            "section": "Item_1A",
            "score": 0.9,
        },
    ]

    ranked = _rerank_chunks_by_query_intent(
        "How exposed is AMD to TSMC supply risk?",
        chunks,
    )

    assert ranked[0]["chunk_id"] == "AMD_2026_Item_1A_0008"


def test_rerank_promotes_business_chunk_for_product_query():
    chunks = [
        {
            "chunk_id": "AMD_2026_Item_1A_0008",
            "text": "AMD faces supplier risk.",
            "ticker": "AMD",
            "fiscal_year": "2026",
            "section": "Item_1A",
            "score": 1.0,
        },
        {
            "chunk_id": "AMD_2026_Item_1_0003",
            "text": "AMD offers Instinct AI accelerator products.",
            "ticker": "AMD",
            "fiscal_year": "2026",
            "section": "Item_1",
            "score": 0.9,
        },
    ]

    ranked = _rerank_chunks_by_query_intent(
        "What AI accelerator product line does AMD offer?",
        chunks,
    )

    assert ranked[0]["chunk_id"] == "AMD_2026_Item_1_0003"


def test_rerank_promotes_chunk_with_answer_bearing_terms():
    chunks = [
        {
            "chunk_id": "AMD_2026_Item_1_0007",
            "text": "AMD offers a broad portfolio of client and server products.",
            "ticker": "AMD",
            "fiscal_year": "2026",
            "section": "Item_1",
            "score": 1.0,
        },
        {
            "chunk_id": "AMD_2026_Item_1_0003",
            "text": "AMD Instinct accelerators target AI and high performance computing.",
            "ticker": "AMD",
            "fiscal_year": "2026",
            "section": "Item_1",
            "score": 0.9,
        },
    ]

    ranked = _rerank_chunks_by_query_intent(
        "What AI accelerator product line does AMD offer? AMD Instinct",
        chunks,
    )

    assert ranked[0]["chunk_id"] == "AMD_2026_Item_1_0003"


def test_rerank_keeps_deterministic_order_when_no_intent_matches():
    chunks = [
        {
            "chunk_id": "b",
            "text": "Second.",
            "ticker": "NVDA",
            "fiscal_year": "2025",
            "section": "Item_1",
            "score": 1.0,
        },
        {
            "chunk_id": "a",
            "text": "First.",
            "ticker": "AMD",
            "fiscal_year": "2025",
            "section": "Item_1A",
            "score": 1.0,
        },
    ]

    ranked = _rerank_chunks_by_query_intent("semiconductor", chunks)

    assert [chunk["chunk_id"] for chunk in ranked] == ["b", "a"]
