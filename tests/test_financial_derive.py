"""Unit tests for Step 8 deterministic derived metrics."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from semigraph.financial.derive import (
    derive_annual_metrics,
    derive_fcf,
    safe_ratio,
)
from semigraph.financial.models import DerivedMetric


PERIOD_END = date(2025, 1, 26)


def _pair(value: str, fact_id: int):
    return Decimal(value), fact_id


def _by_metric(metrics: list[DerivedMetric]) -> dict[str, DerivedMetric]:
    return {metric.metric: metric for metric in metrics}


class TestSafeRatio:
    def test_ratio_uses_decimal_and_retains_input_fact_ids(self):
        result = safe_ratio(
            ticker="NVDA",
            fiscal_year=2025,
            period_end=PERIOD_END,
            metric="gross_margin",
            numerator=_pair("40", 101),
            denominator=_pair("100", 102),
            missing_names=("gross_profit", "revenue"),
        )

        assert result.value == Decimal("0.4")
        assert isinstance(result.value, Decimal)
        assert result.unit == "ratio"
        assert result.status == "ok"
        assert result.input_fact_ids == [101, 102]
        assert result.missing_inputs == []

    def test_missing_input_returns_null_without_partial_provenance(self):
        result = safe_ratio(
            ticker="NVDA",
            fiscal_year=2025,
            period_end=PERIOD_END,
            metric="gross_margin",
            numerator=None,
            denominator=_pair("100", 102),
            missing_names=("gross_profit", "revenue"),
        )

        assert result.value is None
        assert result.status == "missing_input"
        assert result.input_fact_ids == []
        assert result.missing_inputs == ["gross_profit"]

    def test_zero_denominator_returns_null_and_keeps_available_ids(self):
        result = safe_ratio(
            ticker="NVDA",
            fiscal_year=2025,
            period_end=PERIOD_END,
            metric="current_ratio",
            numerator=_pair("50", 201),
            denominator=_pair("0", 202),
            missing_names=("current_assets", "current_liabilities"),
        )

        assert result.value is None
        assert result.status == "zero_denominator"
        assert result.input_fact_ids == [201, 202]
        assert result.missing_inputs == []


class TestFreeCashFlow:
    def test_fcf_is_operating_cash_flow_minus_positive_capex(self):
        result = derive_fcf(
            ticker="NVDA",
            fiscal_year=2025,
            period_end=PERIOD_END,
            operating_cash_flow=_pair("10", 301),
            capital_expenditure=_pair("3", 302),
        )

        assert result.metric == "free_cash_flow"
        assert result.value == Decimal("7")
        assert result.unit == "USD"
        assert result.status == "ok"
        assert result.input_fact_ids == [301, 302]

    def test_fcf_missing_input_is_explicit(self):
        result = derive_fcf(
            ticker="NVDA",
            fiscal_year=2025,
            period_end=PERIOD_END,
            operating_cash_flow=_pair("10", 301),
            capital_expenditure=None,
        )

        assert result.value is None
        assert result.status == "missing_input"
        assert result.missing_inputs == ["capital_expenditure"]
        assert result.input_fact_ids == []


class TestDeriveAnnualMetrics:
    def test_calculates_the_full_v1_annual_metric_set(self):
        current = {
            "revenue": _pair("100", 1),
            "cost_of_revenue": _pair("60", 2),
            "operating_income": _pair("20", 3),
            "net_income": _pair("10", 4),
            "research_and_development": _pair("10", 5),
            "operating_cash_flow": _pair("25", 6),
            "capital_expenditure": _pair("5", 7),
            "current_assets": _pair("50", 8),
            "current_liabilities": _pair("25", 9),
            "total_assets": _pair("100", 10),
            "stockholders_equity": _pair("50", 11),
        }
        prior = {
            "revenue": _pair("80", 21),
            "net_income": _pair("5", 22),
            "total_assets": _pair("80", 23),
            "stockholders_equity": _pair("40", 24),
        }

        results = derive_annual_metrics(
            ticker="NVDA",
            fiscal_year=2025,
            period_end=PERIOD_END,
            current=current,
            prior=prior,
        )
        metrics = _by_metric(results)

        assert set(metrics) == {
            "gross_profit",
            "gross_margin",
            "operating_margin",
            "net_margin",
            "rd_intensity",
            "free_cash_flow",
            "free_cash_flow_margin",
            "revenue_growth_yoy",
            "net_income_growth_yoy",
            "current_ratio",
            "roa",
            "roe",
        }
        assert metrics["gross_profit"].value == Decimal("40")
        assert metrics["gross_profit"].input_fact_ids == [1, 2]
        assert metrics["gross_margin"].value == Decimal("0.4")
        assert metrics["operating_margin"].value == Decimal("0.2")
        assert metrics["net_margin"].value == Decimal("0.1")
        assert metrics["rd_intensity"].value == Decimal("0.1")
        assert metrics["free_cash_flow"].value == Decimal("20")
        assert metrics["free_cash_flow_margin"].value == Decimal("0.2")
        assert metrics["revenue_growth_yoy"].value == Decimal("0.25")
        assert metrics["net_income_growth_yoy"].value == Decimal("1")
        assert metrics["current_ratio"].value == Decimal("2")
        assert metrics["roa"].value == Decimal("10") / Decimal("90")
        assert metrics["roe"].value == Decimal("10") / Decimal("45")
        assert all(metric.status == "ok" for metric in results)

    def test_source_gross_profit_wins_and_is_not_overwritten_by_fallback(self):
        results = derive_annual_metrics(
            ticker="NVDA",
            fiscal_year=2025,
            period_end=PERIOD_END,
            current={
                "revenue": _pair("100", 1),
                "cost_of_revenue": _pair("60", 2),
                "gross_profit": _pair("35", 3),
            },
        )
        metrics = _by_metric(results)

        assert "gross_profit" not in metrics
        assert metrics["gross_margin"].value == Decimal("0.35")
        assert metrics["gross_margin"].input_fact_ids == [3, 1]

    def test_formula_version_is_carried_to_every_derived_row(self):
        results = derive_annual_metrics(
            ticker="AMD",
            fiscal_year=2025,
            period_end=PERIOD_END,
            current={"revenue": _pair("100", 1)},
            formula_version="v2",
        )

        assert results
        assert {metric.formula_version for metric in results} == {"v2"}

    def test_missing_inputs_produce_null_rows_without_crashing(self):
        results = derive_annual_metrics(
            ticker="NVDA",
            fiscal_year=2025,
            period_end=PERIOD_END,
            current={
                "revenue": _pair("100", 1),
                "operating_cash_flow": _pair("10", 2),
            },
        )
        metrics = _by_metric(results)

        assert metrics["gross_profit"].status == "missing_input"
        assert metrics["gross_profit"].missing_inputs == ["cost_of_revenue"]
        assert metrics["gross_margin"].status == "missing_input"
        assert metrics["gross_margin"].missing_inputs == ["gross_profit"]
        assert metrics["free_cash_flow"].status == "missing_input"
        assert metrics["free_cash_flow"].missing_inputs == [
            "capital_expenditure"
        ]
        assert metrics["roa"].status == "missing_input"
        assert metrics["roe"].status == "missing_input"

    def test_zero_denominators_are_reported_for_each_affected_metric(self):
        results = derive_annual_metrics(
            ticker="NVDA",
            fiscal_year=2025,
            period_end=PERIOD_END,
            current={
                "revenue": _pair("0", 1),
                "gross_profit": _pair("0", 2),
                "operating_income": _pair("10", 3),
                "net_income": _pair("10", 4),
                "research_and_development": _pair("5", 5),
                "current_assets": _pair("10", 6),
                "current_liabilities": _pair("0", 7),
                "total_assets": _pair("0", 8),
                "stockholders_equity": _pair("0", 9),
            },
            prior={
                "revenue": _pair("0", 21),
                "net_income": _pair("5", 22),
                "total_assets": _pair("0", 23),
                "stockholders_equity": _pair("0", 24),
            },
        )
        metrics = _by_metric(results)

        assert metrics["gross_margin"].status == "zero_denominator"
        assert metrics["operating_margin"].status == "zero_denominator"
        assert metrics["net_margin"].status == "zero_denominator"
        assert metrics["rd_intensity"].status == "zero_denominator"
        assert metrics["revenue_growth_yoy"].status == "zero_denominator"
        assert metrics["current_ratio"].status == "zero_denominator"
        assert metrics["roa"].status == "zero_denominator"
        assert metrics["roe"].status == "zero_denominator"

    def test_growth_uses_absolute_prior_value_for_negative_base(self):
        results = derive_annual_metrics(
            ticker="AMD",
            fiscal_year=2025,
            period_end=PERIOD_END,
            current={"net_income": _pair("5", 1)},
            prior={"net_income": _pair("-10", 2)},
        )
        metric = _by_metric(results)["net_income_growth_yoy"]

        assert metric.value == Decimal("1.5")
        assert metric.status == "ok"
        assert metric.input_fact_ids == [1, 2]

    def test_roa_requires_both_current_and_prior_assets(self):
        results = derive_annual_metrics(
            ticker="NVDA",
            fiscal_year=2025,
            period_end=PERIOD_END,
            current={
                "net_income": _pair("10", 1),
                "total_assets": _pair("100", 2),
            },
        )
        metric = _by_metric(results)["roa"]

        assert metric.value is None
        assert metric.status == "missing_input"
        assert metric.missing_inputs == ["prior_total_assets"]

    @pytest.mark.parametrize("metric_name", ["roa", "roe"])
    def test_average_denominator_keeps_both_period_fact_ids(self, metric_name):
        current = {
            "net_income": _pair("10", 1),
            "total_assets": _pair("100", 2),
            "stockholders_equity": _pair("50", 3),
        }
        prior = {
            "total_assets": _pair("80", 4),
            "stockholders_equity": _pair("40", 5),
        }

        metric = _by_metric(
            derive_annual_metrics(
                ticker="NVDA",
                fiscal_year=2025,
                period_end=PERIOD_END,
                current=current,
                prior=prior,
            )
        )[metric_name]

        assert metric.status == "ok"
        if metric_name == "roa":
            assert metric.input_fact_ids == [1, 2, 4]
        else:
            assert metric.input_fact_ids == [1, 3, 5]


def test_non_finite_fact_values_are_rejected_before_calculation():
    with pytest.raises(ValueError, match="finite"):
        safe_ratio(
            ticker="NVDA",
            fiscal_year=2025,
            period_end=PERIOD_END,
            metric="gross_margin",
            numerator=(Decimal("NaN"), 1),
            denominator=_pair("100", 2),
            missing_names=("gross_profit", "revenue"),
        )
