"""Unit tests for canonical and derived financial Pydantic models."""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from semigraph.financial.models import CanonicalFact, DerivedMetric


def _canonical_fact(**overrides) -> CanonicalFact:
    values = {
        "ticker": "NVDA",
        "frequency": "annual",
        "fiscal_year": 2025,
        "period_end": date(2025, 1, 26),
        "statement_type": "income",
        "canonical_metric": "revenue",
        "source_concept": "us-gaap_Revenues",
        "source_row_index": 0,
        "value": Decimal("130497"),
        "unit": "USD",
    }
    values.update(overrides)
    return CanonicalFact(**values)


def _derived_metric(**overrides) -> DerivedMetric:
    values = {
        "ticker": "NVDA",
        "fiscal_year": 2025,
        "period_end": date(2025, 1, 26),
        "metric": "gross_margin",
        "value": Decimal("0.742"),
        "unit": "ratio",
        "status": "ok",
    }
    values.update(overrides)
    return DerivedMetric(**values)


class TestCanonicalFact:
    def test_valid_annual_fact_preserves_financial_types(self):
        fact = _canonical_fact(
            period_start="2024-01-29",
            period_end="2025-01-26",
            accepted_at="2025-02-21T18:00:00Z",
            filed_date="2025-02-21",
            value="130497000000.00",
        )

        assert fact.ticker == "NVDA"
        assert fact.frequency == "annual"
        assert fact.period_start == date(2024, 1, 29)
        assert fact.period_end == date(2025, 1, 26)
        assert fact.accepted_at == datetime(
            2025, 2, 21, 18, 0, tzinfo=timezone.utc
        )
        assert fact.filed_date == date(2025, 2, 21)
        assert fact.value == Decimal("130497000000.00")
        assert isinstance(fact.value, Decimal)

    def test_valid_quarterly_fact_accepts_quarter_number(self):
        fact = _canonical_fact(
            frequency="quarterly",
            fiscal_quarter=3,
            period_start=date(2025, 2, 1),
            period_end=date(2025, 4, 30),
        )
        assert fact.frequency == "quarterly"
        assert fact.fiscal_quarter == 3

    @pytest.mark.parametrize("quarter", [0, 5, -1, 6])
    def test_fiscal_quarter_must_be_between_one_and_four(self, quarter):
        with pytest.raises(ValidationError):
            _canonical_fact(frequency="quarterly", fiscal_quarter=quarter)

    @pytest.mark.parametrize("frequency", ["monthly", "snapshot", "YEARLY"])
    def test_frequency_is_a_closed_domain(self, frequency):
        with pytest.raises(ValidationError):
            _canonical_fact(frequency=frequency)

    @pytest.mark.parametrize("statement_type", ["cashflow", "assets", "unknown"])
    def test_statement_type_is_a_closed_domain(self, statement_type):
        with pytest.raises(ValidationError):
            _canonical_fact(statement_type=statement_type)

    def test_missing_optional_provenance_fields_are_allowed(self):
        fact = _canonical_fact(
            period_start=None,
            accepted_at=None,
            filed_date=None,
            accession=None,
            form=None,
            source_label=None,
        )
        assert fact.period_start is None
        assert fact.accepted_at is None
        assert fact.accession is None

    def test_source_row_index_is_retained(self):
        fact = _canonical_fact(source_row_index=17)
        assert fact.source_row_index == 17


class TestDerivedMetric:
    def test_valid_metric_defaults_formula_version_and_input_ids(self):
        metric = _derived_metric()

        assert metric.formula_version == "v1"
        assert metric.input_fact_ids == []
        assert metric.missing_inputs == []
        assert metric.value == Decimal("0.742")

    def test_input_fact_ids_are_integer_ids(self):
        metric = _derived_metric(input_fact_ids=[101, 102])

        assert metric.input_fact_ids == [101, 102]
        assert all(isinstance(fact_id, int) for fact_id in metric.input_fact_ids)

    def test_default_lists_are_not_shared_between_instances(self):
        first = _derived_metric()
        second = _derived_metric()

        first.input_fact_ids.append(101)
        first.missing_inputs.append("revenue")

        assert second.input_fact_ids == []
        assert second.missing_inputs == []

    @pytest.mark.parametrize("status", ["invalid", "failed", "ok_with_warning"])
    def test_status_is_a_closed_domain(self, status):
        with pytest.raises(ValidationError):
            _derived_metric(status=status)

    def test_missing_input_metric_can_have_null_value(self):
        metric = _derived_metric(
            value=None,
            status="missing_input",
            missing_inputs=["revenue"],
        )

        assert metric.value is None
        assert metric.status == "missing_input"
        assert metric.missing_inputs == ["revenue"]

