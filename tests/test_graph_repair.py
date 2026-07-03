"""Unit tests for deterministic graph repair row construction."""
from __future__ import annotations

from semigraph.offline.graph_repair import (
    _build_filer_anchor_rows,
    _build_item_1a_risk_bridge_rows,
)


def test_build_filer_anchor_rows_maps_entity_types_to_conservative_edges():
    rows = _build_filer_anchor_rows(
        [
            {
                "source_chunk": "KLAC_2024_Item_1_0001",
                "section": "Item_1",
                "target": "process control products",
                "target_type": "PRODUCT",
            },
            {
                "source_chunk": "KLAC_2024_Item_1A_0002",
                "section": "Item_1A",
                "target": "export controls",
                "target_type": "RISK_FACTOR",
            },
            {
                "source_chunk": "KLAC_2024_Item_1_0003",
                "section": "Item_1",
                "target": "kla",
                "target_type": "ORG",
            },
        ],
        filer_name="kla",
        ticker="KLAC",
        fiscal_year="2024",
        filing_type="10K",
        method="deterministic_graph_repair_v1",
        run_id="run1",
        created_at="2026-07-03T00:00:00+00:00",
    )

    assert [(row["rel_type"], row["target"]) for row in rows] == [
        ("PRODUCES", "process control products"),
        ("FACES", "export controls"),
    ]
    assert rows[0]["source"] == "kla"
    assert rows[0]["source_type"] == "ORG"
    assert rows[0]["properties"]["repair_rule"] == "filer_anchor"
    assert rows[0]["properties"]["source_chunk"] == "KLAC_2024_Item_1_0001"


def test_build_item_1a_risk_bridge_rows_links_risk_to_impacted_targets():
    rows = _build_item_1a_risk_bridge_rows(
        [
            {
                "source_chunk": "ENTG_2024_Item_1A_0001",
                "section": "Item_1A",
                "source": "supply chain disruption",
                "source_type": "RISK_FACTOR",
                "target": "revenue",
                "target_type": "FIN_METRIC",
            },
            {
                "source_chunk": "ENTG_2024_Item_1A_0001",
                "section": "Item_1A",
                "source": "supply chain disruption",
                "source_type": "RISK_FACTOR",
                "target": "taiwan",
                "target_type": "GPE",
            },
        ],
        ticker="ENTG",
        fiscal_year="2024",
        filing_type="10K",
        method="deterministic_graph_repair_v1",
        run_id="run1",
        created_at="2026-07-03T00:00:00+00:00",
    )

    assert len(rows) == 1
    assert rows[0]["source"] == "supply chain disruption"
    assert rows[0]["rel_type"] == "NEGATIVELY_IMPACTS"
    assert rows[0]["target"] == "revenue"
    assert rows[0]["properties"]["repair_rule"] == "item_1a_risk_bridge"
