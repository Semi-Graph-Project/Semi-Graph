"""Golden-template tests for the Step 11 deterministic SQL compiler."""

from __future__ import annotations

import pytest

from semigraph.financial.query_spec import FinancialQuerySpec
from semigraph.financial.sql_compiler import compile_financial_query


def _compile(**overrides):
    values = {
        "query": "NVDA annual revenue",
        "tickers": ["NVDA"],
        "metrics": ["revenue"],
        "frequency": "annual",
        "operation": "lookup",
    }
    values.update(overrides)
    return compile_financial_query(FinancialQuerySpec(**values))


def test_latest_periodic_lookup_uses_latest_template():
    compiled = _compile()

    assert compiled.template_id == "periodic.lookup.latest.v1"
    assert "row_number() OVER" in compiled.sql
    assert compiled.params == {
        "tickers": ["NVDA"],
        "metrics": ["revenue"],
        "frequency": "annual",
        "limit": 20,
    }


def test_filtered_compare_binds_period_and_tickers():
    compiled = _compile(
        query="Compare AMD and NVDA gross margin FY2024",
        tickers=["AMD", "NVDA"],
        metrics=["gross_margin"],
        operation="compare",
        start_year=2024,
        end_year=2024,
    )

    assert compiled.template_id == "periodic.compare.filtered.v1"
    assert compiled.params["tickers"] == ["AMD", "NVDA"]
    assert compiled.params["start_year"] == 2024
    assert compiled.params["end_year"] == 2024
    assert "AMD" not in compiled.sql
    assert "NVDA" not in compiled.sql


def test_trend_is_always_ordered_oldest_to_newest():
    compiled = _compile(
        query="MU revenue FY2022 to FY2025",
        tickers=["MU"],
        operation="trend",
        start_year=2022,
        end_year=2025,
        sort_order="desc",
    )

    assert compiled.template_id == "periodic.trend.v1"
    assert "period_end ASC" in compiled.sql


@pytest.mark.parametrize(
    ("filters", "template_id"),
    [
        ({}, "periodic.rank.latest.v1"),
        ({"start_year": 2025, "end_year": 2025}, "periodic.rank.filtered.v1"),
    ],
)
def test_periodic_rank_selects_one_period_per_ticker(filters, template_id):
    compiled = _compile(
        query="Rank companies by net margin",
        tickers=["NVDA", "AMD", "MU"],
        metrics=["net_margin"],
        operation="rank",
        **filters,
    )

    assert compiled.template_id == template_id
    assert "PARTITION BY ticker, metric" in compiled.sql
    assert "ORDER BY value DESC NULLS LAST" in compiled.sql


def test_aggregate_uses_allowlisted_function_and_bound_values():
    compiled = _compile(
        query="Average revenue",
        tickers=["NVDA", "AMD"],
        operation="aggregate",
        aggregation="avg",
    )

    assert compiled.template_id == "periodic.aggregate.v1"
    assert "avg(value) AS value" in compiled.sql
    assert compiled.params["aggregation"] == "avg"
    assert compiled.params["tickers"] == ["NVDA", "AMD"]


@pytest.mark.parametrize(
    ("operation", "template_id"),
    [
        ("lookup", "snapshot.lookup.v1"),
        ("compare", "snapshot.compare.v1"),
        ("rank", "snapshot.rank.v1"),
    ],
)
def test_snapshot_templates(operation, template_id):
    tickers = ["NVDA", "AMD"] if operation == "compare" else ["NVDA"]
    compiled = _compile(
        query="Current NVDA price",
        tickers=tickers,
        metrics=["current_price"],
        frequency="snapshot",
        operation=operation,
    )

    assert compiled.template_id == template_id
    assert "financial.agent_market_metrics" in compiled.sql
    assert compiled.params["tickers"] == tickers


def test_sql_like_ticker_remains_a_bound_parameter():
    malicious = "NVDA'); DROP TABLE financial.companies; --"
    compiled = _compile(tickers=[malicious])

    assert malicious.upper() in compiled.params["tickers"]
    assert malicious.upper() not in compiled.sql


def test_compiler_requires_validated_spec():
    with pytest.raises(TypeError, match="FinancialQuerySpec"):
        compile_financial_query({"tickers": ["NVDA"]})


@pytest.mark.parametrize(
    ("operation", "filters", "template_id"),
    [
        (
            "lookup",
            {"start_year": 2025, "end_year": 2025},
            "periodic.lookup.filtered.v1",
        ),
        ("compare", {}, "periodic.compare.latest.v1"),
    ],
)
def test_remaining_periodic_template_ids(operation, filters, template_id):
    tickers = ["NVDA", "AMD"] if operation == "compare" else ["NVDA"]
    compiled = _compile(operation=operation, tickers=tickers, **filters)
    assert compiled.template_id == template_id
