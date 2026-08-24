"""Unit tests for evidence-grounded graph repair helpers."""
from __future__ import annotations

from semigraph.offline.graph_repair import (
    EntityRef,
    GraphRepairStats,
    RepairChunk,
    _evidence_in_text,
    _validate_llm_relationships,
)


def _chunk() -> RepairChunk:
    return RepairChunk(
        chunk_id="KLAC_2024_Item_1_0001",
        ticker="KLAC",
        fiscal_year="2024",
        filing_type="10-K",
        section="Item_1",
        text=(
            "KLA develops and manufactures process control products. "
            "The company competes with Applied Materials in some markets."
        ),
        entities=[
            EntityRef(eid="node-1", name="kla", type="ORG"),
            EntityRef(eid="node-2", name="process control products", type="PRODUCT"),
            EntityRef(eid="node-3", name="applied materials", type="COMP"),
        ],
        candidate_eids=frozenset({"node-2"}),
    )


def test_graph_repair_stats_serializes_all_fields_without_sharing_dicts():
    stats = GraphRepairStats(
        ticker="NVDA",
        fiscal_year="2026",
        filing_type="10K",
        relationships_created=2,
        created_by_rel={"PRODUCES": 2},
    )

    payload = stats.as_dict()

    assert payload["relationships_created"] == 2
    assert payload["created_by_rel"] == {"PRODUCES": 2}
    payload["created_by_rel"]["PRODUCES"] = 0
    assert stats.created_by_rel == {"PRODUCES": 2}


def test_evidence_sentence_must_be_present_in_chunk_text():
    assert _evidence_in_text(
        "KLA develops and manufactures process control products.",
        _chunk().text,
    )
    assert not _evidence_in_text(
        "KLA sells products that are not named here.",
        _chunk().text,
    )


def test_validate_llm_relationships_accepts_evidence_backed_candidate_edge():
    rows, rejected, proposed = _validate_llm_relationships(
        _chunk(),
        {
            "relationships": [
                {
                    "source_id": "E1",
                    "target_id": "E2",
                    "type": "PRODUCES",
                    "evidence_sentence": "KLA develops and manufactures process control products.",
                    "confidence": 0.82,
                }
            ]
        },
        method="llm_evidence_graph_repair_v1",
        run_id="run1",
        created_at="2026-07-03T00:00:00+00:00",
    )

    assert proposed == 1
    assert rejected == {}
    assert len(rows) == 1
    assert rows[0]["source"] == "kla"
    assert rows[0]["target"] == "process control products"
    assert rows[0]["rel_type"] == "PRODUCES"
    assert rows[0]["properties"]["repair_method"] == "llm_evidence_graph_repair_v1"
    assert rows[0]["properties"]["evidence_sentence"] == (
        "KLA develops and manufactures process control products."
    )


def test_validate_llm_relationships_rejects_weak_or_incompatible_edges():
    rows, rejected, proposed = _validate_llm_relationships(
        _chunk(),
        {
            "relationships": [
                {
                    "source_id": "E1",
                    "target_id": "E3",
                    "type": "COMPETES_WITH",
                    "evidence_sentence": "The company competes with Applied Materials in some markets.",
                },
                {
                    "source_id": "E2",
                    "target_id": "E1",
                    "type": "PRODUCES",
                    "evidence_sentence": "KLA develops and manufactures process control products.",
                },
                {
                    "source_id": "E2",
                    "target_id": "E3",
                    "type": "PRODUCES",
                    "evidence_sentence": "KLA develops and manufactures process control products.",
                },
                {
                    "source_id": "E1",
                    "target_id": "E2",
                    "type": "PRODUCES",
                    "evidence_sentence": "This sentence is not in the chunk.",
                },
            ]
        },
        method="llm_evidence_graph_repair_v1",
        run_id="run1",
        created_at="2026-07-03T00:00:00+00:00",
    )

    assert proposed == 4
    assert len(rows) == 1
    assert rows[0]["source"] == "kla"
    assert rows[0]["target"] == "process control products"
    assert rows[0]["properties"]["repair_direction_corrected"] is True
    assert rejected == {
        "no_candidate_endpoint": 1,
        "incompatible_relationship_type": 1,
        "evidence_not_found_in_chunk": 1,
    }
