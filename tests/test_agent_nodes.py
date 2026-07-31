from types import SimpleNamespace

import semigraph.agent.nodes as nodes
from semigraph.agent.prompts import build_financial_capability_summary


def _financial_chunk(**overrides):
    chunk = {
        "chunk_id": "fin-29-1",
        "text": "NVDA revenue raw financial text",
        "ticker": "NVDA",
        "fiscal_year": 2024,
        "fiscal_quarter": None,
        "frequency": "annual",
        "section": "Financial_revenue",
        "score": 1.0,
        "metric": "revenue",
        "value": "60922000000",
        "unit": "usd",
        "period_end": "2024-01-28",
        "observed_at": None,
        "status": "ok",
        "source_kind": "reported",
        "provenance": {
            "fact_id": 29,
            "accession": "0001045810-24-000029",
            "source_concept": "us-gaap_Revenues",
            "debug_blob": "must stay out of the prompt",
        },
    }
    chunk.update(overrides)
    return chunk


def test_plan_route_financial_capabilities_come_from_registry():
    cfg = SimpleNamespace(financial_metric_registry={
        "reported": frozenset({"revenue"}),
        "derived": frozenset({"revenue_growth_yoy", "roe"}),
        "snapshot": frozenset({"pe_ttm"}),
    })

    summary = build_financial_capability_summary(cfg)

    assert "Reported metrics: revenue" in summary
    assert "Derived metrics: revenue_growth_yoy, roe" in summary
    assert "Snapshot metrics: pe_ttm" in summary
    assert "Never expand a derived metric" in summary
    assert "revenue_growth_yoy" in nodes.PLAN_ROUTE_SYSTEM_PROMPT


def test_financial_synthesis_format_is_readable_and_keeps_raw_citation():
    chunk = _financial_chunk(
        metric="gross_margin",
        section="Financial_gross_margin",
        value="0.5425",
        unit="ratio",
        source_kind="derived",
        provenance={
            "derived_id": 7,
            "input_fact_ids": [29, 30],
            "formula_version": "v1",
            "debug_blob": "kept in raw citation only",
        },
    )

    formatted, citation_lookup = nodes._format_chunks_for_synthesis([chunk])

    assert "evidence_type=financial" in formatted
    assert "value=54.25% (exact=0.5425 ratio)" in formatted
    assert '"input_fact_ids": [29, 30]' in formatted
    assert "debug_blob" not in formatted
    assert citation_lookup[1] == chunk


def test_synthesis_formatter_keeps_full_chunk_text():
    chunk = {
        "chunk_id": "C1",
        "text": "start-" + "x" * 3_000 + "-important-tail",
    }

    formatted, _ = nodes._format_chunks_for_synthesis([chunk])

    assert "-important-tail" in formatted
