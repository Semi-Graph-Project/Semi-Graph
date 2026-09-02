"""Small read-only repository over the curated financial views.

The public functions accept filters only.  SQL structure is fixed here and
all user-controlled values are bound parameters, so callers never pass raw SQL.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from semigraph.config import Config, get_config
from semigraph.financial.db import financial_connection


_PERIODIC_SQL = """
SELECT
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
FROM financial.agent_periodic_metrics
WHERE ticker = ANY(%(tickers)s)
  AND metric = ANY(%(metrics)s)
  AND frequency = %(frequency)s
  AND (%(start_year)s::integer IS NULL OR fiscal_year >= %(start_year)s)
  AND (%(end_year)s::integer IS NULL OR fiscal_year <= %(end_year)s)
  AND (%(quarter)s::smallint IS NULL OR fiscal_quarter = %(quarter)s)
ORDER BY ticker, metric, period_end DESC
LIMIT %(limit)s
"""

_MARKET_SQL = """
SELECT
    evidence_id,
    ticker,
    observed_at,
    metric,
    value,
    unit,
    source_kind,
    provenance
FROM financial.agent_market_metrics
WHERE ticker = ANY(%(tickers)s)
  AND metric = ANY(%(metrics)s)
ORDER BY ticker, metric, observed_at DESC
LIMIT %(limit)s
"""


def _clean_values(
    values: Sequence[str],
    name: str,
    uppercase: bool = False,
) -> list[str]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{name} must be a sequence of strings")

    cleaned: list[str] = []
    for value in values:
        normalized = str(value).strip()
        if not normalized:
            continue
        normalized = normalized.upper() if uppercase else normalized
        if normalized not in cleaned:
            cleaned.append(normalized)
    if not cleaned:
        raise ValueError(f"{name} must not be empty")
    return cleaned


def _validated_limit(limit: int, cfg: Config) -> int:
    maximum = int(cfg.financial_max_query_rows)
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise TypeError("limit must be an integer")
    if not 1 <= limit <= maximum:
        raise ValueError(f"limit must be between 1 and {maximum}")
    return limit


def _rows(result: Any) -> list[dict[str, Any]]:
    rows = result.fetchall()
    if not all(isinstance(row, Mapping) for row in rows):
        raise TypeError("financial queries require psycopg dict_row results")
    return [dict(row) for row in rows]


def query_periodic_metrics(
    tickers: Sequence[str],
    metrics: Sequence[str],
    frequency: str = "annual",
    start_year: int | None = None,
    end_year: int | None = None,
    quarter: int | None = None,
    limit: int = 50,
    cfg: Config | None = None,
) -> list[dict[str, Any]]:
    """Return reported and derived periodic metrics from one curated view."""

    cfg = cfg or get_config()
    if frequency not in {"annual", "quarterly"}:
        raise ValueError("frequency must be 'annual' or 'quarterly'")
    if start_year is not None and end_year is not None and start_year > end_year:
        raise ValueError("start_year must be <= end_year")
    if quarter is not None and (
        frequency != "quarterly" or quarter not in range(1, 5)
    ):
        raise ValueError(
            "quarter requires quarterly frequency and a value from 1 to 4"
        )

    params = {
        "tickers": _clean_values(tickers, name="tickers", uppercase=True),
        "metrics": _clean_values(metrics, name="metrics"),
        "frequency": frequency,
        "start_year": start_year,
        "end_year": end_year,
        "quarter": quarter,
        "limit": _validated_limit(limit, cfg),
    }
    with financial_connection(readonly=True, cfg=cfg) as conn:
        return _rows(conn.execute(_PERIODIC_SQL, params))


def query_market_metrics(
    tickers: Sequence[str],
    metrics: Sequence[str],
    limit: int = 50,
    cfg: Config | None = None,
) -> list[dict[str, Any]]:
    """Return the latest quote and vendor metrics from the market view."""

    cfg = cfg or get_config()
    params = {
        "tickers": _clean_values(tickers, name="tickers", uppercase=True),
        "metrics": _clean_values(metrics, name="metrics"),
        "limit": _validated_limit(limit, cfg),
    }
    with financial_connection(readonly=True, cfg=cfg) as conn:
        return _rows(conn.execute(_MARKET_SQL, params))


__all__ = ["query_market_metrics", "query_periodic_metrics"]
