"""Compile a validated FinancialQuerySpec into deterministic PostgreSQL SQL."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from semigraph.financial.query_spec import (
    Aggregation,
    FinancialQuerySpec,
    Frequency,
    Operation,
)


@dataclass(frozen=True)
class CompiledFinancialQuery:
    """SQL template plus values that must be bound separately by psycopg."""

    template_id: str
    sql: str
    params: dict[str, Any]


_PERIODIC_COLUMNS = """
    evidence_id,
    ticker,
    frequency,
    fiscal_year,
    fiscal_quarter,
    period_end,
    metric,
    value,
    unit,
    source_kind,
    status,
    provenance
"""

_PERIOD_FILTERS = """
  AND (%(start_year)s::integer IS NULL OR fiscal_year >= %(start_year)s)
  AND (%(end_year)s::integer IS NULL OR fiscal_year <= %(end_year)s)
  AND (%(quarter)s::smallint IS NULL OR fiscal_quarter = %(quarter)s)
"""

PERIODIC_BASE_SQL = f"""
SELECT
{_PERIODIC_COLUMNS}
FROM financial.agent_periodic_metrics
WHERE ticker = ANY(%(tickers)s)
  AND metric = ANY(%(metrics)s)
  AND frequency = %(frequency)s
{_PERIOD_FILTERS}
ORDER BY ticker, metric, period_end {{sort_order}}
LIMIT %(limit)s
"""

_PERIODIC_LATEST_SQL = f"""
WITH ranked AS (
    SELECT
{_PERIODIC_COLUMNS},
        row_number() OVER (
            PARTITION BY ticker, metric
            ORDER BY period_end DESC, evidence_id DESC
        ) AS period_rank
    FROM financial.agent_periodic_metrics
    WHERE ticker = ANY(%(tickers)s)
      AND metric = ANY(%(metrics)s)
      AND frequency = %(frequency)s
)
SELECT
{_PERIODIC_COLUMNS}
FROM ranked
WHERE period_rank = 1
ORDER BY ticker, metric
LIMIT %(limit)s
"""

_PERIODIC_TREND_SQL = f"""
SELECT
{_PERIODIC_COLUMNS}
FROM financial.agent_periodic_metrics
WHERE ticker = ANY(%(tickers)s)
  AND metric = ANY(%(metrics)s)
  AND frequency = %(frequency)s
{_PERIOD_FILTERS}
ORDER BY ticker, metric, period_end ASC
LIMIT %(limit)s
"""

_RANK_FILTERED_SQL = f"""
WITH ranked_periods AS (
    SELECT
{_PERIODIC_COLUMNS},
        row_number() OVER (
            PARTITION BY ticker, metric
            ORDER BY period_end DESC, evidence_id DESC
        ) AS period_rank
    FROM financial.agent_periodic_metrics
    WHERE ticker = ANY(%(tickers)s)
      AND metric = ANY(%(metrics)s)
      AND frequency = %(frequency)s
{_PERIOD_FILTERS}
)
SELECT
{_PERIODIC_COLUMNS}
FROM ranked_periods
WHERE period_rank = 1
ORDER BY value {{sort_order}} NULLS LAST, ticker
LIMIT %(limit)s
"""

_RANK_LATEST_SQL = f"""
WITH ranked_periods AS (
    SELECT
{_PERIODIC_COLUMNS},
        row_number() OVER (
            PARTITION BY ticker, metric
            ORDER BY period_end DESC, evidence_id DESC
        ) AS period_rank
    FROM financial.agent_periodic_metrics
    WHERE ticker = ANY(%(tickers)s)
      AND metric = ANY(%(metrics)s)
      AND frequency = %(frequency)s
)
SELECT
{_PERIODIC_COLUMNS}
FROM ranked_periods
WHERE period_rank = 1
ORDER BY value {{sort_order}} NULLS LAST, ticker
LIMIT %(limit)s
"""

_AGGREGATE_SQL = """
SELECT
    ('aggregate:' || %(aggregation)s || ':' || metric)::text AS evidence_id,
    'ALL'::text AS ticker,
    %(frequency)s::text AS frequency,
    NULL::integer AS fiscal_year,
    NULL::smallint AS fiscal_quarter,
    NULL::date AS period_end,
    metric,
    {aggregate_function}(value) AS value,
    min(unit) AS unit,
    'aggregate'::text AS source_kind,
    'ok'::text AS status,
    jsonb_build_object(
        'aggregation', %(aggregation)s,
        'row_count', count(value),
        'tickers', %(tickers)s::text[]
    ) AS provenance
FROM financial.agent_periodic_metrics
WHERE ticker = ANY(%(tickers)s)
  AND metric = ANY(%(metrics)s)
  AND frequency = %(frequency)s
  AND value IS NOT NULL
{period_filters}
GROUP BY metric
ORDER BY metric
LIMIT %(limit)s
"""

_SNAPSHOT_SQL = """
SELECT
    evidence_id,
    ticker,
    observed_at,
    metric,
    value,
    unit,
    source_kind,
    'ok'::text AS status,
    provenance
FROM financial.agent_market_metrics
WHERE ticker = ANY(%(tickers)s)
  AND metric = ANY(%(metrics)s)
ORDER BY ticker, metric
LIMIT %(limit)s
"""

_SNAPSHOT_RANK_SQL = """
SELECT
    evidence_id,
    ticker,
    observed_at,
    metric,
    value,
    unit,
    source_kind,
    'ok'::text AS status,
    provenance
FROM financial.agent_market_metrics
WHERE ticker = ANY(%(tickers)s)
  AND metric = ANY(%(metrics)s)
ORDER BY value {sort_order} NULLS LAST, ticker
LIMIT %(limit)s
"""

_AGGREGATE_FUNCTIONS = {
    Aggregation.AVG: "avg",
    Aggregation.MIN: "min",
    Aggregation.MAX: "max",
    Aggregation.SUM: "sum",
}


def _periodic_params(
    spec: FinancialQuerySpec,
    include_periods: bool,
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "tickers": list(spec.tickers),
        "metrics": list(spec.metrics),
        "frequency": spec.frequency.value,
        "limit": spec.limit,
    }
    if include_periods:
        params.update(
            start_year=spec.start_year,
            end_year=spec.end_year,
            quarter=spec.quarter,
        )
    return params


def _snapshot_params(spec: FinancialQuerySpec) -> dict[str, Any]:
    return {
        "tickers": list(spec.tickers),
        "metrics": list(spec.metrics),
        "limit": spec.limit,
    }


def _has_period_filters(spec: FinancialQuerySpec) -> bool:
    return any(
        value is not None
        for value in (spec.start_year, spec.end_year, spec.quarter)
    )


def _compiled(
    template_id: str,
    sql: str,
    params: dict[str, Any],
) -> CompiledFinancialQuery:
    return CompiledFinancialQuery(
        template_id=template_id,
        sql=sql.strip(),
        params=params,
    )


def _compile_snapshot(spec: FinancialQuerySpec) -> CompiledFinancialQuery:
    params = _snapshot_params(spec)
    if spec.operation == Operation.RANK:
        sql = _SNAPSHOT_RANK_SQL.format(
            sort_order=spec.sort_order.value.upper()
        )
        return _compiled("snapshot.rank.v1", sql, params)

    template_id = (
        "snapshot.compare.v1"
        if spec.operation == Operation.COMPARE
        else "snapshot.lookup.v1"
    )
    return _compiled(template_id, _SNAPSHOT_SQL, params)


def _compile_rank(spec: FinancialQuerySpec) -> CompiledFinancialQuery:
    filtered = _has_period_filters(spec)
    sql_template = _RANK_FILTERED_SQL if filtered else _RANK_LATEST_SQL
    sql = sql_template.format(sort_order=spec.sort_order.value.upper())
    template_id = (
        "periodic.rank.filtered.v1"
        if filtered
        else "periodic.rank.latest.v1"
    )
    return _compiled(
        template_id,
        sql,
        _periodic_params(spec, include_periods=filtered),
    )


def _compile_aggregate(spec: FinancialQuerySpec) -> CompiledFinancialQuery:
    assert spec.aggregation is not None  # guaranteed by FinancialQuerySpec
    sql = _AGGREGATE_SQL.format(
        aggregate_function=_AGGREGATE_FUNCTIONS[spec.aggregation],
        period_filters=_PERIOD_FILTERS,
    )
    params = _periodic_params(spec, include_periods=True)
    params["aggregation"] = spec.aggregation.value
    return _compiled("periodic.aggregate.v1", sql, params)


def compile_financial_query(
    spec: FinancialQuerySpec,
) -> CompiledFinancialQuery:
    """Select one allowlisted SQL template for a validated query spec."""

    if not isinstance(spec, FinancialQuerySpec):
        raise TypeError("spec must be a validated FinancialQuerySpec")

    if spec.frequency == Frequency.SNAPSHOT:
        return _compile_snapshot(spec)
    if spec.operation == Operation.TREND:
        return _compiled(
            "periodic.trend.v1",
            _PERIODIC_TREND_SQL,
            _periodic_params(spec, include_periods=True),
        )
    if spec.operation == Operation.RANK:
        return _compile_rank(spec)
    if spec.operation == Operation.AGGREGATE:
        return _compile_aggregate(spec)

    filtered = _has_period_filters(spec)
    operation = spec.operation.value
    template_id = (
        f"periodic.{operation}.filtered.v1"
        if filtered
        else f"periodic.{operation}.latest.v1"
    )
    sql = (
        PERIODIC_BASE_SQL.format(sort_order=spec.sort_order.value.upper())
        if filtered
        else _PERIODIC_LATEST_SQL
    )
    return _compiled(
        template_id,
        sql,
        _periodic_params(spec, include_periods=filtered),
    )


__all__ = [
    "CompiledFinancialQuery",
    "PERIODIC_BASE_SQL",
    "compile_financial_query",
]
