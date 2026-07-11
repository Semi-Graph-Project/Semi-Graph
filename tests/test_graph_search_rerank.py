from semigraph.online.graph_search import (
    MetadataRerankParams,
    _collapse_clusters,
    _rerank_chunks,
    _section_boosts_for_query,
)


# def test_section_boosts_detect_risk_query():
#     boosts = _section_boosts_for_query("How exposed is AMD to TSMC supply risk?")

#     assert boosts["Item_1A"] > boosts.get("Item_1", 1.0)


# def test_rerank_promotes_risk_factor_chunk_over_business_chunk():
#     chunks = [
#         {
#             "chunk_id": "AMD_2026_Item_1_0010",
#             "text": "AMD works with TSMC manufacturing partners.",
#             "ticker": "AMD",
#             "fiscal_year": "2026",
#             "section": "Item_1",
#             "score": 1.0,
#         },
#         {
#             "chunk_id": "AMD_2026_Item_1A_0008",
#             "text": "AMD depends on third-party foundries and faces supply risk.",
#             "ticker": "AMD",
#             "fiscal_year": "2026",
#             "section": "Item_1A",
#             "score": 0.9,
#         },
#     ]

#     ranked = _rerank_chunks(
#         "How exposed is AMD to TSMC supply risk?",
#         chunks,
#     )

#     assert ranked[0]["chunk_id"] == "AMD_2026_Item_1A_0008"


# def test_rerank_promotes_business_chunk_for_product_query():
#     chunks = [
#         {
#             "chunk_id": "AMD_2026_Item_1A_0008",
#             "text": "AMD faces supplier risk.",
#             "ticker": "AMD",
#             "fiscal_year": "2026",
#             "section": "Item_1A",
#             "score": 1.0,
#         },
#         {
#             "chunk_id": "AMD_2026_Item_1_0003",
#             "text": "AMD offers Instinct AI accelerator products.",
#             "ticker": "AMD",
#             "fiscal_year": "2026",
#             "section": "Item_1",
#             "score": 0.9,
#         },
#     ]

#     ranked = _rerank_chunks(
#         "What AI accelerator product line does AMD offer?",
#         chunks,
#     )

#     assert ranked[0]["chunk_id"] == "AMD_2026_Item_1_0003"


# def test_rerank_promotes_chunk_with_answer_bearing_terms():
#     chunks = [
#         {
#             "chunk_id": "AMD_2026_Item_1_0007",
#             "text": "AMD offers a broad portfolio of client and server products.",
#             "ticker": "AMD",
#             "fiscal_year": "2026",
#             "section": "Item_1",
#             "score": 1.0,
#         },
#         {
#             "chunk_id": "AMD_2026_Item_1_0003",
#             "text": "AMD Instinct accelerators target AI and high performance computing.",
#             "ticker": "AMD",
#             "fiscal_year": "2026",
#             "section": "Item_1",
#             "score": 0.9,
#         },
#     ]

#     ranked = _rerank_chunks(
#         "What AI accelerator product line does AMD offer? AMD Instinct",
#         chunks,
#     )

#     assert ranked[0]["chunk_id"] == "AMD_2026_Item_1_0003"


# def test_rerank_keeps_deterministic_order_when_no_intent_matches():
#     chunks = [
#         {
#             "chunk_id": "b",
#             "text": "Second.",
#             "ticker": "NVDA",
#             "fiscal_year": "2025",
#             "section": "Item_1",
#             "score": 1.0,
#         },
#         {
#             "chunk_id": "a",
#             "text": "First.",
#             "ticker": "AMD",
#             "fiscal_year": "2025",
#             "section": "Item_1A",
#             "score": 1.0,
#         },
#     ]

#     ranked = _rerank_chunks("semiconductor", chunks)

#     assert [chunk["chunk_id"] for chunk in ranked] == ["b", "a"]


def test_risk_chunk():
    chunks = [
        {
            "chunk_id": "A",
            "text": "AMD works with TSMC manufacturing partners.",
            "ticker": "AMD",
            "fiscal_year": "2025",
            "section": "Item_1",
            "score": 1.0,
        },
        {
            "chunk_id": "B",
            "text": "AMD depends on third-party foundries and faces supply risk",
            "ticker": "AMD",
            "fiscal_year": "2025",
            "section": "Item_1A",
            "score": 0.9,
        }
    ]

    ranked = _rerank_chunks(
        "How exposed is AMD to TSMC supply risk?",
        chunks,
        rerank_mode="metadata"
    )

    assert ranked[0]["chunk_id"] == "B"

def test_lexical_chunk():
    chunks = [
        {
            "chunk_id": "A",
            "text": "AMD has broad product portfolio",
            "ticker": "AMD",
            "fiscal_year": "2025",
            "section": "Item_1",
            "score": 1.0,
        },
        {
            "chunk_id": "B",
            "text": "AMD Instinct accelerators target AI workloads",
            "ticker": "AMD",
            "fiscal_year": "2025",
            "section": "Item_1",
            "score": 0.9,
        }
    ]

    ranked = _rerank_chunks(
        "What AI accelerators product line does AMD offer?",
        chunks,
        rerank_mode="metadata",
        metadata_rerank_params=MetadataRerankParams(
            lexical_match_weight=0.15,
            lexical_boost_cap=0.65,
        ),
    )

    assert ranked[0]["chunk_id"] == "B" 


def test_broad_chunk_penalty():
    chunks = [
        {
            "chunk_id": "A",
            "text": "Moreover, we may not adequately assess the risks of new business initiatives... Acquisitions, joint ventures and other investments involve significant challenges",
            "ticker": "AMD",
            "fiscal_year": "2025",
            "section": "Item_1",
            "score": 2.2602,
        },
        {
            "chunk_id": "B",
            "text": "We are subject to U.S. laws and regulations, including the Export Administration Regulations (EAR)... which restrict the export of certain products and technologies to certain countries, including China..",
            "ticker": "AMD",
            "fiscal_year": "2025",
            "section": "Item_1A",
            "score": 2.1847,
        }
    ]

    ranked = _rerank_chunks(
        "US export controls on AI chips to China",
        chunks,
        rerank_mode="metadata"
    )

    assert ranked[0]["chunk_id"] == "B"


def test_collapse_clusters_uses_max_for_duplicate_entity_names():
    ppr_entities = [
        {"name": "amd", "type": "ORG", "score": 1.2},
        {"name": "advanced micro devices", "type": "ORG", "score": 0.5},
        {"name": "amd", "type": "COMP", "score": 0.3},
        {"name": "nvidia", "type": "ORG", "score": 0.7},
    ]
    cluster_map = {
        "amd": ["amd", "advanced micro devices", "amd"],
        "advanced micro devices": ["amd", "advanced micro devices"],
        "nvidia": ["nvidia"],
    }

    collapsed = _collapse_clusters(ppr_entities, cluster_map)

    assert collapsed[0]["aliases"] == ["amd", "advanced micro devices", "amd"]
    assert collapsed[0]["score"] == 1.7
    assert collapsed[1]["aliases"] == ["nvidia"]
    assert collapsed[1]["score"] == 0.7
