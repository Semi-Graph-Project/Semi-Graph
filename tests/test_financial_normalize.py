"""Unit tests for Step 7: deterministic canonical normalization.

These tests use small Finnhub-shaped dictionaries.  They do not call Finnhub
or PostgreSQL, so failures point directly to report selection or normalization
rules.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from semigraph.financial.models import CanonicalFact
from semigraph.financial.normalize import (
    normalize_report,
    select_latest_reports,
)


def _report(
    *,
    year: int = 2025,
    quarter: int = 0,
    start_date: str = "2024-01-29",
    end_date: str | None = "2025-01-26",
    accepted_date: str | None = "2025-02-21T18:00:00Z",
    filed_date: str | None = "2025-02-21",
    accession: str = "0001045810-25-000023",
    form: str = "10-K",
    ic: list[dict] | None = None,
    bs: list[dict] | None = None,
    cf: list[dict] | None = None,
) -> dict:
    return {
        "year": year,
        "quarter": quarter,
        "startDate": start_date,
        "endDate": end_date,
        "acceptedDate": accepted_date,
        "filedDate": filed_date,
        "accessNumber": accession,
        "form": form,
        "report": {
            "ic": ic or [],
            "bs": bs or [],
            "cf": cf or [],
        },
    }


def _row(concept: str, value, *, label: str | None = None, unit: str = "USD"):
    return {
        "concept": concept,
        "label": label or concept,
        "unit": unit,
        "value": value,
    }


def _by_metric(facts: list[CanonicalFact]) -> dict[str, CanonicalFact]:
    return {fact.canonical_metric: fact for fact in facts}


class TestSelectLatestReports:
    def test_input_order_does_not_change_selected_reports(self):
        original = _report(
            end_date="2025-01-26",
            accepted_date="2025-02-20T10:00:00Z",
            accession="original",
        )
        amendment = _report(
            end_date="2025-01-26",
            accepted_date="2025-03-01T10:00:00Z",
            accession="amendment",
            form="10-K/A",
        )
        previous = _report(
            year=2024,
            end_date="2024-01-28",
            accepted_date="2024-02-21T10:00:00Z",
            accession="previous",
        )

        forward = select_latest_reports(
            [original, previous, amendment],
            limit=2,
        )
        reversed_input = select_latest_reports(
            [amendment, previous, original],
            limit=2,
        )

        assert [row["accessNumber"] for row in forward] == [
            "amendment",
            "previous",
        ]
        assert [row["accessNumber"] for row in reversed_input] == [
            "amendment",
            "previous",
        ]

    def test_latest_accepted_date_wins_for_the_same_period(self):
        original = _report(
            accepted_date="2025-02-21T10:00:00Z",
            accession="original",
        )
        amendment = _report(
            accepted_date="2025-03-03T10:00:00Z",
            accession="amendment",
            form="10-K/A",
        )

        selected = select_latest_reports([original, amendment], limit=3)

        assert len(selected) == 1
        assert selected[0]["accessNumber"] == "amendment"

    def test_filed_date_breaks_tie_when_accepted_date_is_missing(self):
        older = _report(
            accepted_date=None,
            filed_date="2025-02-20",
            accession="older",
        )
        newer = _report(
            accepted_date=None,
            filed_date="2025-02-25",
            accession="newer",
        )

        selected = select_latest_reports([newer, older], limit=3)

        assert selected[0]["accessNumber"] == "newer"

    def test_annual_and_quarterly_limits_are_enforced(self):
        reports = [
            _report(
                year=year,
                end_date=f"{year}-12-31",
                accepted_date=f"{year + 1}-02-01T00:00:00Z",
                accession=str(year),
            )
            for year in range(2015, 2026)
        ]

        annual = select_latest_reports(reports, limit=3)
        quarterly = select_latest_reports(reports, limit=8)

        assert [row["year"] for row in annual] == [2025, 2024, 2023]
        assert len(quarterly) == 8
        assert [row["year"] for row in quarterly[:2]] == [2025, 2024]

    def test_report_without_period_end_is_ignored(self):
        valid = _report(accession="valid")
        missing_period = _report(end_date=None, accession="missing-period")

        selected = select_latest_reports([missing_period, valid], limit=3)

        assert [row["accessNumber"] for row in selected] == ["valid"]


class TestNormalizeReport:
    def test_known_concepts_become_typed_canonical_facts(self):
        report = _report(
            ic=[
                _row("us-gaap_Revenues", "130497000000", label="Revenue"),
                _row("us-gaap:NetIncomeLoss", "72880000000"),
            ],
            bs=[_row("us-gaap_Assets", "111601000000")],
            cf=[
                _row(
                    "us-gaap:NetCashProvidedByUsedInOperatingActivities",
                    "64089000000",
                )
            ],
        )

        facts = normalize_report(
            ticker="NVDA",
            frequency="annual",
            report=report,
        )
        by_metric = _by_metric(facts)

        assert set(by_metric) == {
            "revenue",
            "net_income",
            "total_assets",
            "operating_cash_flow",
        }
        revenue = by_metric["revenue"]
        assert isinstance(revenue, CanonicalFact)
        assert revenue.value == Decimal("130497000000")
        assert revenue.statement_type == "income"
        assert revenue.source_concept == "us-gaap_Revenues"
        assert revenue.source_label == "Revenue"
        assert revenue.source_row_index == 0
        assert revenue.unit == "USD"

    def test_report_metadata_and_provenance_are_preserved(self):
        report = _report(
            ic=[_row("Revenues", "100")],
            accession="accession-123",
            form="10-K/A",
        )

        fact = normalize_report(
            ticker="NVDA",
            frequency="annual",
            report=report,
        )[0]

        assert fact.ticker == "NVDA"
        assert fact.fiscal_year == 2025
        assert fact.fiscal_quarter is None
        assert fact.period_start == date(2024, 1, 29)
        assert fact.period_end == date(2025, 1, 26)
        assert fact.accepted_at == datetime(
            2025,
            2,
            21,
            18,
            0,
            tzinfo=timezone.utc,
        )
        assert fact.filed_date == date(2025, 2, 21)
        assert fact.accession == "accession-123"
        assert fact.form == "10-K/A"

    def test_unknown_and_fuzzy_concepts_are_skipped(self):
        report = _report(
            ic=[
                _row("RevenueFromContract", "999"),
                _row("CostOfRevenueExtra", "888"),
                _row("Revenues", "100"),
            ]
        )

        facts = normalize_report(
            ticker="NVDA",
            frequency="annual",
            report=report,
        )

        assert [fact.canonical_metric for fact in facts] == ["revenue"]
        assert facts[0].value == Decimal("100")

    def test_concept_in_the_wrong_statement_is_skipped(self):
        report = _report(
            ic=[_row("Assets", "100")],
            bs=[_row("Revenues", "200")],
        )

        facts = normalize_report(
            ticker="NVDA",
            frequency="annual",
            report=report,
        )

        assert facts == []

    @pytest.mark.parametrize(
        "rows",
        [
            [
                _row("SalesRevenueNet", "10"),
                _row(
                    "RevenueFromContractWithCustomerExcludingAssessedTax",
                    "20",
                ),
            ],
            [
                _row(
                    "RevenueFromContractWithCustomerExcludingAssessedTax",
                    "20",
                ),
                _row("SalesRevenueNet", "10"),
            ],
        ],
    )
    def test_preferred_alias_wins_independent_of_row_order(self, rows):
        report = _report(ic=rows)

        facts = normalize_report(
            ticker="NVDA",
            frequency="annual",
            report=report,
        )

        assert len(facts) == 1
        assert facts[0].canonical_metric == "revenue"
        assert (
            facts[0].source_concept
            == "RevenueFromContractWithCustomerExcludingAssessedTax"
        )
        assert facts[0].value == Decimal("20")

    @pytest.mark.parametrize("source_value", ["300", "-300"])
    def test_capex_is_always_normalized_to_positive_outflow(self, source_value):
        report = _report(
            cf=[
                _row(
                    "PaymentsToAcquirePropertyPlantAndEquipment",
                    source_value,
                )
            ]
        )

        fact = normalize_report(
            ticker="NVDA",
            frequency="annual",
            report=report,
        )[0]

        assert fact.canonical_metric == "capital_expenditure"
        assert fact.value == Decimal("300")

    def test_nvda_fiscal_year_and_actual_period_end_are_not_recalculated(self):
        report = _report(
            year=2025,
            start_date="2024-01-29",
            end_date="2025-01-26",
            ic=[_row("Revenues", "100")],
        )

        fact = normalize_report(
            ticker="NVDA",
            frequency="annual",
            report=report,
        )[0]

        assert fact.fiscal_year == 2025
        assert fact.period_start == date(2024, 1, 29)
        assert fact.period_end == date(2025, 1, 26)

    def test_quarterly_report_preserves_fiscal_quarter(self):
        report = _report(
            year=2025,
            quarter=3,
            form="10-Q",
            ic=[_row("Revenues", "35")],
        )

        fact = normalize_report(
            ticker="NVDA",
            frequency="quarterly",
            report=report,
        )[0]

        assert fact.frequency == "quarterly"
        assert fact.fiscal_quarter == 3

    def test_invalid_or_missing_values_are_skipped_without_losing_valid_rows(self):
        report = _report(
            ic=[
                {"concept": "Revenues", "unit": "USD"},
                _row("GrossProfit", "not-a-number"),
                _row("NetIncomeLoss", None),
                _row("EarningsPerShareDiluted", "0.1", unit="USD/share"),
            ]
        )

        facts = normalize_report(
            ticker="NVDA",
            frequency="annual",
            report=report,
        )

        assert len(facts) == 1
        assert facts[0].canonical_metric == "diluted_eps"
        assert facts[0].value == Decimal("0.1")

    def test_empty_report_body_returns_no_facts(self):
        report = _report()

        assert normalize_report(
            ticker="NVDA",
            frequency="annual",
            report=report,
        ) == []
