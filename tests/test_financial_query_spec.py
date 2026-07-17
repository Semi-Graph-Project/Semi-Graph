"""Validation tests for the Step 11 FinancialQuerySpec contract."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from semigraph.financial.query_spec import FinancialQuerySpec


def _spec(**overrides):
    values = {
        "query": "NVDA annual revenue",
        "tickers": ["NVDA"],
        "metrics": ["revenue"],
        "frequency": "annual",
        "operation": "lookup",
    }
    values.update(overrides)
    return FinancialQuerySpec(**values)


def test_normalizes_query_tickers_and_metrics():
    spec = _spec(
        query="  NVDA revenue  ",
        tickers=[" nvda ", "NVDA", "amd"],
        metrics=[" Revenue ", "revenue"],
    )

    assert spec.query == "NVDA revenue"
    assert spec.tickers == ["NVDA", "AMD"]
    assert spec.metrics == ["revenue"]


def test_rejects_metric_outside_frequency_allowlist():
    with pytest.raises(ValidationError, match="Unsupported metrics"):
        _spec(metrics=["pe_ttm"])
    with pytest.raises(ValidationError, match="Unsupported metrics"):
        _spec(frequency="snapshot", metrics=["revenue"])


def test_snapshot_rejects_period_filters_and_unsupported_operations():
    with pytest.raises(ValidationError, match="fiscal period"):
        _spec(
            frequency="snapshot",
            metrics=["current_price"],
            start_year=2025,
        )
    with pytest.raises(ValidationError, match="support"):
        _spec(
            frequency="snapshot",
            metrics=["current_price"],
            operation="trend",
        )


def test_aggregate_requires_exactly_one_metric_and_aggregation():
    with pytest.raises(ValidationError, match="aggregate requires"):
        _spec(operation="aggregate")
    with pytest.raises(ValidationError, match="aggregate requires"):
        _spec(
            operation="aggregate",
            aggregation="avg",
            metrics=["revenue", "net_income"],
        )

    spec = _spec(operation="aggregate", aggregation="avg")
    assert spec.aggregation.value == "avg"


def test_aggregation_is_rejected_for_non_aggregate_operation():
    with pytest.raises(ValidationError, match="only for aggregate"):
        _spec(aggregation="sum")


def test_rank_requires_one_metric_and_compare_requires_two_tickers():
    with pytest.raises(ValidationError, match="rank requires"):
        _spec(operation="rank", metrics=["revenue", "net_income"])
    with pytest.raises(ValidationError, match="compare requires"):
        _spec(operation="compare")


def test_quarter_is_valid_for_quarterly_only():
    with pytest.raises(ValidationError, match="quarter is valid"):
        _spec(quarter=1)

    spec = _spec(frequency="quarterly", quarter=1)
    assert spec.quarter == 1


def test_rejects_invalid_year_range_limit_and_extra_fields():
    with pytest.raises(ValidationError, match="start_year"):
        _spec(start_year=2025, end_year=2024)
    with pytest.raises(ValidationError, match="less than or equal to 50"):
        _spec(limit=51)
    with pytest.raises(ValidationError, match="Extra inputs"):
        _spec(raw_sql="DROP TABLE financial.companies")

