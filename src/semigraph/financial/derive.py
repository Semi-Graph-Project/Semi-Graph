"""Deterministic, provenance-preserving derived financial metrics.

The functions in this module deliberately do not talk to PostgreSQL or an
LLM.  ETL supplies canonical facts as ``(Decimal value, fact_id)`` pairs and
receives typed :class:`DerivedMetric` rows ready to persist.  Missing inputs
and zero denominators become explicit statuses instead of exceptions.

Version 1 derives annual metrics only.  Quarterly TTM calculations are kept out
of this module because Finnhub cash-flow rows can be year-to-date values; naive
quarterly summation would double-count cash flows.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Mapping, Sequence

from semigraph.financial.models import DerivedMetric


FactValue = tuple[Decimal, int]


@dataclass(frozen=True)
class _ResolvedInput:
    value: Decimal
    fact_ids: tuple[int, ...]


def _resolve(pair: FactValue | None) -> _ResolvedInput | None:
    if pair is None:
        return None
    value, fact_id = pair
    decimal_value = value if isinstance(value, Decimal) else Decimal(str(value))
    if not decimal_value.is_finite():
        raise ValueError("financial fact values must be finite Decimal numbers")
    return _ResolvedInput(decimal_value, (int(fact_id),))


def _merge_ids(*inputs: _ResolvedInput | None) -> list[int]:
    result: list[int] = []
    for item in inputs:
        if item is None:
            continue
        for fact_id in item.fact_ids:
            if fact_id not in result:
                result.append(fact_id)
    return result


def _derived(
    ticker: str,
    fiscal_year: int,
    period_end: date,
    metric: str,
    value: Decimal | None,
    unit: str,
    formula_version: str,
    status: str,
    input_fact_ids: Sequence[int] = (),
    missing_inputs: Sequence[str] = (),
) -> DerivedMetric:
    return DerivedMetric(
        ticker=ticker,
        fiscal_year=fiscal_year,
        period_end=period_end,
        metric=metric,
        value=value,
        unit=unit,
        formula_version=formula_version,
        input_fact_ids=list(input_fact_ids),
        status=status,
        missing_inputs=list(missing_inputs),
    )


def _safe_ratio_resolved(
    ticker: str,
    fiscal_year: int,
    period_end: date,
    metric: str,
    numerator: _ResolvedInput | None,
    denominator: _ResolvedInput | None,
    missing_names: Sequence[str],
    formula_version: str,
) -> DerivedMetric:
    missing: list[str] = []
    if numerator is None:
        missing.append(missing_names[0])
    if denominator is None:
        missing.append(missing_names[1])

    if missing:
        return _derived(
            ticker=ticker,
            fiscal_year=fiscal_year,
            period_end=period_end,
            metric=metric,
            value=None,
            unit="ratio",
            formula_version=formula_version,
            status="missing_input",
            missing_inputs=missing,
        )

    assert numerator is not None
    assert denominator is not None
    input_fact_ids = _merge_ids(numerator, denominator)
    if denominator.value == 0:
        return _derived(
            ticker=ticker,
            fiscal_year=fiscal_year,
            period_end=period_end,
            metric=metric,
            value=None,
            unit="ratio",
            formula_version=formula_version,
            status="zero_denominator",
            input_fact_ids=input_fact_ids,
        )

    return _derived(
        ticker=ticker,
        fiscal_year=fiscal_year,
        period_end=period_end,
        metric=metric,
        value=numerator.value / denominator.value,
        unit="ratio",
        formula_version=formula_version,
        status="ok",
        input_fact_ids=input_fact_ids,
    )


def safe_ratio(
    ticker: str,
    fiscal_year: int,
    period_end: date,
    metric: str,
    numerator: FactValue | None,
    denominator: FactValue | None,
    missing_names: tuple[str, str],
    formula_version: str = "v1",
) -> DerivedMetric:
    """Safely calculate a ratio while retaining both input fact IDs."""

    return _safe_ratio_resolved(
        ticker=ticker,
        fiscal_year=fiscal_year,
        period_end=period_end,
        metric=metric,
        numerator=_resolve(numerator),
        denominator=_resolve(denominator),
        missing_names=missing_names,
        formula_version=formula_version,
    )


def _missing_amount_metric(
    ticker: str,
    fiscal_year: int,
    period_end: date,
    metric: str,
    missing_inputs: Sequence[str],
    formula_version: str,
) -> DerivedMetric:
    return _derived(
        ticker=ticker,
        fiscal_year=fiscal_year,
        period_end=period_end,
        metric=metric,
        value=None,
        unit="USD",
        formula_version=formula_version,
        status="missing_input",
        missing_inputs=missing_inputs,
    )


def derive_fcf(
    ticker: str,
    fiscal_year: int,
    period_end: date,
    operating_cash_flow: FactValue | None,
    capital_expenditure: FactValue | None,
    formula_version: str = "v1",
) -> DerivedMetric:
    """Calculate ``operating_cash_flow - capital_expenditure``."""

    ocf = _resolve(operating_cash_flow)
    capex = _resolve(capital_expenditure)
    missing: list[str] = []
    if ocf is None:
        missing.append("operating_cash_flow")
    if capex is None:
        missing.append("capital_expenditure")
    if missing:
        return _missing_amount_metric(
            ticker=ticker,
            fiscal_year=fiscal_year,
            period_end=period_end,
            metric="free_cash_flow",
            missing_inputs=missing,
            formula_version=formula_version,
        )

    assert ocf is not None
    assert capex is not None
    return _derived(
        ticker=ticker,
        fiscal_year=fiscal_year,
        period_end=period_end,
        metric="free_cash_flow",
        value=ocf.value - capex.value,
        unit="USD",
        formula_version=formula_version,
        status="ok",
        input_fact_ids=_merge_ids(ocf, capex),
    )


def _difference(
    left: _ResolvedInput | None,
    right: _ResolvedInput | None,
) -> _ResolvedInput | None:
    if left is None or right is None:
        return None
    return _ResolvedInput(
        left.value - right.value,
        tuple(_merge_ids(left, right)),
    )


def _growth_ratio(
    ticker: str,
    fiscal_year: int,
    period_end: date,
    metric: str,
    current: _ResolvedInput | None,
    prior: _ResolvedInput | None,
    current_name: str,
    prior_name: str,
    formula_version: str,
) -> DerivedMetric:
    if current is None or prior is None:
        missing = []
        if current is None:
            missing.append(current_name)
        if prior is None:
            missing.append(prior_name)
        return _derived(
            ticker=ticker,
            fiscal_year=fiscal_year,
            period_end=period_end,
            metric=metric,
            value=None,
            unit="ratio",
            formula_version=formula_version,
            status="missing_input",
            missing_inputs=missing,
        )

    numerator = _ResolvedInput(
        current.value - prior.value,
        tuple(_merge_ids(current, prior)),
    )
    denominator = _ResolvedInput(abs(prior.value), prior.fact_ids)
    return _safe_ratio_resolved(
        ticker=ticker,
        fiscal_year=fiscal_year,
        period_end=period_end,
        metric=metric,
        numerator=numerator,
        denominator=denominator,
        missing_names=(current_name, prior_name),
        formula_version=formula_version,
    )


def _average(
    current: _ResolvedInput | None,
    prior: _ResolvedInput | None,
) -> _ResolvedInput | None:
    if current is None or prior is None:
        return None
    return _ResolvedInput(
        (current.value + prior.value) / Decimal("2"),
        tuple(_merge_ids(current, prior)),
    )


def _average_ratio(
    ticker: str,
    fiscal_year: int,
    period_end: date,
    metric: str,
    numerator: _ResolvedInput | None,
    current_denominator: _ResolvedInput | None,
    prior_denominator: _ResolvedInput | None,
    numerator_name: str,
    denominator_name: str,
    prior_denominator_name: str,
    formula_version: str,
) -> DerivedMetric:
    missing: list[str] = []
    if numerator is None:
        missing.append(numerator_name)
    if current_denominator is None:
        missing.append(denominator_name)
    if prior_denominator is None:
        missing.append(prior_denominator_name)
    if missing:
        return _derived(
            ticker=ticker,
            fiscal_year=fiscal_year,
            period_end=period_end,
            metric=metric,
            value=None,
            unit="ratio",
            formula_version=formula_version,
            status="missing_input",
            missing_inputs=missing,
        )

    denominator = _average(current_denominator, prior_denominator)
    assert denominator is not None
    return _safe_ratio_resolved(
        ticker=ticker,
        fiscal_year=fiscal_year,
        period_end=period_end,
        metric=metric,
        numerator=numerator,
        denominator=denominator,
        missing_names=(numerator_name, denominator_name),
        formula_version=formula_version,
    )


def derive_annual_metrics(
    ticker: str,
    fiscal_year: int,
    period_end: date,
    current: Mapping[str, FactValue],
    prior: Mapping[str, FactValue] | None = None,
    formula_version: str = "v1",
) -> list[DerivedMetric]:
    """Derive the annual metric set from canonical fact references.

    ``current`` and ``prior`` map canonical metric names to ``(value,
    fact_id)``.  A source ``gross_profit`` fact takes precedence.  If absent,
    a derived gross profit fallback is emitted from revenue and cost of
    revenue; its provenance points to those source facts.
    """

    previous = prior or {}
    current_values = {name: _resolve(pair) for name, pair in current.items()}
    previous_values = {name: _resolve(pair) for name, pair in previous.items()}
    results: list[DerivedMetric] = []

    revenue = current_values.get("revenue")
    cost_of_revenue = current_values.get("cost_of_revenue")
    source_gross_profit = current_values.get("gross_profit")
    gross_profit = source_gross_profit or _difference(revenue, cost_of_revenue)

    if source_gross_profit is None:
        if gross_profit is None:
            missing = []
            if revenue is None:
                missing.append("revenue")
            if cost_of_revenue is None:
                missing.append("cost_of_revenue")
            results.append(
                _missing_amount_metric(
                    ticker=ticker,
                    fiscal_year=fiscal_year,
                    period_end=period_end,
                    metric="gross_profit",
                    missing_inputs=missing,
                    formula_version=formula_version,
                )
            )
        else:
            results.append(
                _derived(
                    ticker=ticker,
                    fiscal_year=fiscal_year,
                    period_end=period_end,
                    metric="gross_profit",
                    value=gross_profit.value,
                    unit="USD",
                    formula_version=formula_version,
                    status="ok",
                    input_fact_ids=gross_profit.fact_ids,
                )
            )

    results.append(
        _safe_ratio_resolved(
            ticker=ticker,
            fiscal_year=fiscal_year,
            period_end=period_end,
            metric="gross_margin",
            numerator=gross_profit,
            denominator=revenue,
            missing_names=("gross_profit", "revenue"),
            formula_version=formula_version,
        )
    )
    results.append(
        safe_ratio(
            ticker=ticker,
            fiscal_year=fiscal_year,
            period_end=period_end,
            metric="operating_margin",
            numerator=current.get("operating_income"),
            denominator=current.get("revenue"),
            missing_names=("operating_income", "revenue"),
            formula_version=formula_version,
        )
    )
    results.append(
        safe_ratio(
            ticker=ticker,
            fiscal_year=fiscal_year,
            period_end=period_end,
            metric="net_margin",
            numerator=current.get("net_income"),
            denominator=current.get("revenue"),
            missing_names=("net_income", "revenue"),
            formula_version=formula_version,
        )
    )
    results.append(
        safe_ratio(
            ticker=ticker,
            fiscal_year=fiscal_year,
            period_end=period_end,
            metric="rd_intensity",
            numerator=current.get("research_and_development"),
            denominator=current.get("revenue"),
            missing_names=("research_and_development", "revenue"),
            formula_version=formula_version,
        )
    )

    fcf = derive_fcf(
        ticker=ticker,
        fiscal_year=fiscal_year,
        period_end=period_end,
        operating_cash_flow=current.get("operating_cash_flow"),
        capital_expenditure=current.get("capital_expenditure"),
        formula_version=formula_version,
    )
    results.append(fcf)
    fcf_input = (
        _ResolvedInput(fcf.value, tuple(fcf.input_fact_ids))
        if fcf.status == "ok" and fcf.value is not None
        else None
    )
    results.append(
        _safe_ratio_resolved(
            ticker=ticker,
            fiscal_year=fiscal_year,
            period_end=period_end,
            metric="free_cash_flow_margin",
            numerator=fcf_input,
            denominator=revenue,
            missing_names=("free_cash_flow", "revenue"),
            formula_version=formula_version,
        )
    )

    results.append(
        _growth_ratio(
            ticker=ticker,
            fiscal_year=fiscal_year,
            period_end=period_end,
            metric="revenue_growth_yoy",
            current=revenue,
            prior=previous_values.get("revenue"),
            current_name="revenue",
            prior_name="prior_revenue",
            formula_version=formula_version,
        )
    )
    results.append(
        _growth_ratio(
            ticker=ticker,
            fiscal_year=fiscal_year,
            period_end=period_end,
            metric="net_income_growth_yoy",
            current=current_values.get("net_income"),
            prior=previous_values.get("net_income"),
            current_name="net_income",
            prior_name="prior_net_income",
            formula_version=formula_version,
        )
    )
    results.append(
        safe_ratio(
            ticker=ticker,
            fiscal_year=fiscal_year,
            period_end=period_end,
            metric="current_ratio",
            numerator=current.get("current_assets"),
            denominator=current.get("current_liabilities"),
            missing_names=("current_assets", "current_liabilities"),
            formula_version=formula_version,
        )
    )
    results.append(
        _average_ratio(
            ticker=ticker,
            fiscal_year=fiscal_year,
            period_end=period_end,
            metric="roa",
            numerator=current_values.get("net_income"),
            current_denominator=current_values.get("total_assets"),
            prior_denominator=previous_values.get("total_assets"),
            numerator_name="net_income",
            denominator_name="total_assets",
            prior_denominator_name="prior_total_assets",
            formula_version=formula_version,
        )
    )
    results.append(
        _average_ratio(
            ticker=ticker,
            fiscal_year=fiscal_year,
            period_end=period_end,
            metric="roe",
            numerator=current_values.get("net_income"),
            current_denominator=current_values.get("stockholders_equity"),
            prior_denominator=previous_values.get("stockholders_equity"),
            numerator_name="net_income",
            denominator_name="stockholders_equity",
            prior_denominator_name="prior_stockholders_equity",
            formula_version=formula_version,
        )
    )

    return results


# A descriptive alias for callers that do not want to encode the annual-only
# scope in their ETL function name.
derive_metrics_for_period = derive_annual_metrics
