"""Unit tests for the exact Finnhub concept registry."""
from __future__ import annotations

import pytest

from semigraph.financial.metrics import (
    ALIAS_TO_METRIC,
    METRICS,
    local_concept_name,
)


class TestLocalConceptName:
    @pytest.mark.parametrize(
        ("source_concept", "expected"),
        [
            (
                "us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax",
                "RevenueFromContractWithCustomerExcludingAssessedTax",
            ),
            ("us-gaap:Revenues", "Revenues"),
            ("dei:EntityCommonStockSharesOutstanding", "EntityCommonStockSharesOutstanding"),
            ("Revenue", "Revenue"),
        ],
    )
    def test_removes_namespace_only(self, source_concept, expected):
        assert local_concept_name(source_concept) == expected

    def test_does_not_fuzzy_match_or_modify_unknown_concept(self):
        unknown = "CostOfRevenueExtra"
        assert local_concept_name(unknown) == unknown
        assert unknown not in ALIAS_TO_METRIC


class TestMetricRegistry:
    def test_required_metrics_are_registered(self):
        names = {definition.name for definition in METRICS}
        assert {
            "revenue",
            "cost_of_revenue",
            "gross_profit",
            "research_and_development",
            "operating_income",
            "net_income",
            "diluted_eps",
            "cash_and_equivalents",
            "current_assets",
            "total_assets",
            "current_liabilities",
            "total_liabilities",
            "stockholders_equity",
            "operating_cash_flow",
            "capital_expenditure",
        } <= names

    def test_metric_names_and_aliases_are_unique(self):
        names = [definition.name for definition in METRICS]
        aliases = [alias for definition in METRICS for alias in definition.aliases]

        assert len(names) == len(set(names))
        assert len(aliases) == len(set(aliases))
        assert len(ALIAS_TO_METRIC) == len(aliases)

    @pytest.mark.parametrize(
        ("concept", "metric", "statement"),
        [
            ("RevenueFromContractWithCustomerExcludingAssessedTax", "revenue", "income"),
            ("Revenues", "revenue", "income"),
            ("SalesRevenueNet", "revenue", "income"),
            ("CostOfRevenue", "cost_of_revenue", "income"),
            ("AssetsCurrent", "current_assets", "balance"),
            ("Assets", "total_assets", "balance"),
            (
                "NetCashProvidedByUsedInOperatingActivities",
                "operating_cash_flow",
                "cash_flow",
            ),
        ],
    )
    def test_exact_alias_maps_to_expected_metric(self, concept, metric, statement):
        definition = ALIAS_TO_METRIC[concept]
        assert definition.name == metric
        assert definition.statement == statement

    def test_substring_or_case_variants_do_not_map(self):
        assert "CostOfRevenueExtra" not in ALIAS_TO_METRIC
        assert "costofrevenue" not in ALIAS_TO_METRIC
        assert "RevenueFromContract" not in ALIAS_TO_METRIC

    def test_alias_order_is_preferred_to_fallback(self):
        revenue = ALIAS_TO_METRIC["RevenueFromContractWithCustomerExcludingAssessedTax"]
        assert revenue.aliases == (
            "RevenueFromContractWithCustomerExcludingAssessedTax",
            "Revenues",
            "SalesRevenueNet",
        )
        assert revenue.aliases[0] == "RevenueFromContractWithCustomerExcludingAssessedTax"

    def test_capex_is_the_only_cash_outflow_metric(self):
        capex = ALIAS_TO_METRIC["PaymentsToAcquirePropertyPlantAndEquipment"]
        assert capex.name == "capital_expenditure"
        assert capex.cash_outflow is True

        non_outflow_metrics = [
            definition
            for definition in METRICS
            if definition.name != "capital_expenditure"
        ]
        assert all(definition.cash_outflow is False for definition in non_outflow_metrics)

    def test_units_are_explicit(self):
        units = {definition.name: definition.unit for definition in METRICS}
        assert units["revenue"] == "USD"
        assert units["diluted_eps"] == "USD/share"
        assert units["gross_profit"] == "USD"

