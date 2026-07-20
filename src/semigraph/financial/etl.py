"""financial ETL orchestration.

The ETL boundary is intentionally explicit::

    Neo4j universe -> Finnhub raw payloads -> canonical facts -> derived rows

Each ticker is processed in its own PostgreSQL transaction.  A failed ticker
therefore rolls back its raw/fact/derived writes without deleting successful
tickers from the same run.  The run table still records the failure so a
``partial`` run cannot look like a successful one.

This module owns orchestration and persistence glue only.  The Finnhub SDK
adapter, normalizer, and deterministic formula engine remain independently
testable in their own modules.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field as dataclass_field
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from semigraph.config import Config, get_config
from semigraph.connections import get_neo4j_driver
from semigraph.financial.db import financial_connection
from semigraph.financial.derive import derive_annual_metrics
from semigraph.financial.finnhub_client import FinnhubStagingClient
from semigraph.financial.models import CanonicalFact, DerivedMetric
from semigraph.financial.normalize import normalize_report, select_latest_reports
from semigraph.financial.repository import upsert_raw_payload


RunStatus = Literal["running", "succeeded", "partial", "failed"]


class FinancialETLSummary(BaseModel):
    """Serializable result written by the Step 9 runner and CLI."""

    run_id: str
    status: RunStatus
    expected_company_count: int
    discovered_tickers: list[str] = Field(default_factory=list)
    successful_tickers: list[str] = Field(default_factory=list)
    failed_tickers: dict[str, dict[str, str]] = Field(default_factory=dict)
    stats: dict[str, Any] = Field(default_factory=dict)


ETLSummary = FinancialETLSummary


_GRAPH_TICKER_QUERY = """
MATCH (c:Chunk)
WHERE c.ticker IS NOT NULL
RETURN DISTINCT toUpper(c.ticker) AS ticker
ORDER BY ticker
"""

_VENDOR_METRICS = {
    "marketCapitalization": ("market_cap", "USD_million"),
    "peTTM": ("pe_ttm", "ratio"),
}
# Public name used by the ETL checkpoint and future serving layer.
VENDOR_METRICS = _VENDOR_METRICS


@dataclass(frozen=True)
class _FactRecord:
    fact: CanonicalFact
    raw_payload_id: int
    fact_id: int


@dataclass
class _AnnualPeriod:
    fiscal_year: int
    period_end: date
    facts: dict[str, tuple[Decimal, int]] = dataclass_field(default_factory=dict)


def _row_value(row: Any, key: str) -> Any:
    """Read psycopg dict rows and the tuple rows used by test doubles."""

    if isinstance(row, Mapping):
        return row[key]
    return row[0]


def _normalise_tickers(values: Sequence[str]) -> set[str]:
    return {
        str(value).strip().upper()
        for value in values
        if str(value).strip()
    }


def load_graph_tickers(
    cfg: Config | None = None,
    *,
    driver: Any | None = None,
) -> list[str]:
    """Load the distinct ticker universe from the configured Neo4j graph.

    ``driver`` is injectable for tests.  When omitted this function creates
    and closes the normal project driver itself.
    """

    cfg = cfg or get_config()
    owns_driver = driver is None
    graph_driver = driver or get_neo4j_driver(cfg)
    try:
        with graph_driver.session() as session:
            result = session.run(_GRAPH_TICKER_QUERY)
            data_method = getattr(result, "data", None)
            if callable(data_method):
                rows = data_method()
            elif data_method is not None:
                rows = list(data_method)
            else:
                rows = list(result)
        tickers: set[str] = set()
        for row in rows:
            try:
                value = (
                    row.get("ticker")
                    if hasattr(row, "get")
                    else _row_value(row, "ticker")
                )
            except (IndexError, KeyError, TypeError):
                continue
            if value is not None and str(value).strip():
                tickers.add(str(value).strip().upper())
        return sorted(tickers)
    finally:
        if owns_driver:
            graph_driver.close()


def validate_universe(graph_tickers: Sequence[str], cfg: Config) -> list[str]:
    """Fail fast unless Neo4j and config describe exactly one universe."""

    graph_set = _normalise_tickers(graph_tickers)
    config_set = _normalise_tickers(cfg.tickers)
    expected = int(cfg.financial_expected_company_count)

    if expected <= 0:
        raise ValueError("financial_expected_company_count must be positive")

    if (
        len(graph_set) != expected
        or len(config_set) != expected
        or graph_set != config_set
    ):
        missing = sorted(config_set - graph_set)
        extra = sorted(graph_set - config_set)
        raise RuntimeError(
            "Financial universe mismatch. "
            f"expected_count={expected}, "
            f"graph={sorted(graph_set)}, config={sorted(config_set)}, "
            f"missing_in_graph={missing}, extra_in_graph={extra}. "
            "Check that NEO4J_URI points to the main company graph, "
            "not the benchmark graph."
        )

    return sorted(graph_set)


def validate_requested_subset(
    requested: Sequence[str] | None,
    available: Sequence[str],
) -> list[str]:
    """Validate an optional smoke-test subset after full-universe preflight."""

    available_set = _normalise_tickers(available)
    if not requested:
        return sorted(available_set)

    result: list[str] = []
    unknown: set[str] = set()
    for value in requested:
        ticker = str(value).strip().upper()
        if ticker not in available_set:
            unknown.add(ticker)
        elif ticker not in result:
            result.append(ticker)
    if unknown:
        raise ValueError(
            f"Requested ticker(s) are outside the validated universe: "
            f"{sorted(unknown)}"
        )
    return result


def _create_run(
    conn: Any,
    *,
    run_id: str,
    expected_company_count: int,
    discovered_tickers: Sequence[str],
) -> None:
    conn.execute(
        """
        INSERT INTO financial.ingestion_runs (
            run_id,
            status,
            expected_company_count,
            discovered_tickers
        )
        VALUES (%s, 'running', %s, %s)
        """,
        (run_id, expected_company_count, list(discovered_tickers)),
    )


def _upsert_companies(conn: Any, tickers: Sequence[str]) -> None:
    for ticker in tickers:
        conn.execute(
            """
            INSERT INTO financial.companies (
                ticker,
                active,
                graph_seen_at
            )
            VALUES (%s, true, now())
            ON CONFLICT (ticker) DO UPDATE SET
                active = true,
                graph_seen_at = EXCLUDED.graph_seen_at
            """,
            (ticker,),
        )


def _finish_run(
    conn: Any,
    *,
    run_id: str,
    status: RunStatus,
    successful_tickers: Sequence[str],
    failed_tickers: Mapping[str, Mapping[str, str]],
    stats: Mapping[str, Any],
) -> None:
    import json

    conn.execute(
        """
        UPDATE financial.ingestion_runs
        SET finished_at = now(),
            status = %s,
            successful_tickers = %s,
            failed_tickers = %s::jsonb,
            stats = %s::jsonb
        WHERE run_id = %s
        """,
        (
            status,
            list(successful_tickers),
            json.dumps(dict(failed_tickers), ensure_ascii=False),
            json.dumps(dict(stats), ensure_ascii=False, default=str),
            run_id,
        ),
    )


def _mark_company_ingested(conn: Any, ticker: str) -> None:
    conn.execute(
        """
        UPDATE financial.companies
        SET first_ingested_at = COALESCE(first_ingested_at, now()),
            last_ingested_at = now()
        WHERE ticker = %s
        """,
        (ticker,),
    )


def _payload_reports(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    data = payload.get("data") or []
    if not isinstance(data, list):
        raise TypeError("Finnhub financials payload data must be a list")
    return [report for report in data if isinstance(report, dict)]


def _select_reports(
    payload: Mapping[str, Any],
    *,
    limit: int,
) -> list[dict[str, Any]]:
    if limit <= 0:
        return []
    return select_latest_reports(_payload_reports(payload), limit=limit)


def _upsert_fact(conn: Any, *, raw_payload_id: int, fact: CanonicalFact) -> int:
    params = (
        raw_payload_id,
        fact.ticker,
        fact.frequency,
        fact.fiscal_year,
        fact.fiscal_quarter,
        fact.period_start,
        fact.period_end,
        fact.accepted_at,
        fact.filed_date,
        fact.accession,
        fact.form,
        fact.statement_type,
        fact.canonical_metric,
        fact.source_concept,
        fact.source_label,
        fact.source_row_index,
        fact.value,
        fact.unit,
    )
    row = conn.execute(
        """
        INSERT INTO financial.financial_facts (
            raw_payload_id,
            ticker,
            frequency,
            fiscal_year,
            fiscal_quarter,
            period_start,
            period_end,
            accepted_at,
            filed_date,
            accession,
            form,
            statement_type,
            canonical_metric,
            source_concept,
            source_label,
            source_row_index,
            value,
            unit
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (raw_payload_id, frequency, period_end, canonical_metric)
        DO NOTHING
        RETURNING fact_id
        """,
        params,
    ).fetchone()
    if row is not None:
        return int(_row_value(row, "fact_id"))

    row = conn.execute(
        """
        SELECT fact_id
        FROM financial.financial_facts
        WHERE raw_payload_id = %s
          AND frequency = %s
          AND period_end = %s
          AND canonical_metric = %s
        """,
        (
            raw_payload_id,
            fact.frequency,
            fact.period_end,
            fact.canonical_metric,
        ),
    ).fetchone()
    if row is None:
        raise RuntimeError("financial fact upsert succeeded but its id was not found")
    return int(_row_value(row, "fact_id"))


def _store_report_facts(
    conn: Any,
    *,
    ticker: str,
    frequency: str,
    reports: Sequence[dict[str, Any]],
    raw_payload_id: int,
) -> list[_FactRecord]:
    records: list[_FactRecord] = []
    for report in reports:
        facts = normalize_report(
            ticker=ticker,
            frequency=frequency,
            report=report,
        )
        for fact in facts:
            fact_id = _upsert_fact(
                conn,
                raw_payload_id=raw_payload_id,
                fact=fact,
            )
            records.append(
                _FactRecord(
                    fact=fact,
                    raw_payload_id=raw_payload_id,
                    fact_id=fact_id,
                )
            )
    return records


def _parse_period(report: Mapping[str, Any]) -> tuple[int, date]:
    try:
        fiscal_year = int(report["year"])
        period_end = date.fromisoformat(str(report["endDate"])[:10])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Finnhub report is missing a valid year/endDate") from exc
    return fiscal_year, period_end


def _annual_periods(
    reports: Sequence[dict[str, Any]],
    records: Sequence[_FactRecord],
) -> list[_AnnualPeriod]:
    periods: dict[date, _AnnualPeriod] = {}
    for report in reports:
        fiscal_year, period_end = _parse_period(report)
        periods[period_end] = _AnnualPeriod(
            fiscal_year=fiscal_year,
            period_end=period_end,
        )

    for record in records:
        if record.fact.frequency != "annual":
            continue
        period = periods.setdefault(
            record.fact.period_end,
            _AnnualPeriod(
                fiscal_year=record.fact.fiscal_year,
                period_end=record.fact.period_end,
            ),
        )
        period.facts[record.fact.canonical_metric] = (
            record.fact.value,
            record.fact_id,
        )

    return sorted(periods.values(), key=lambda item: item.period_end, reverse=True)


def _upsert_derived_metric(conn: Any, metric: DerivedMetric) -> None:
    conn.execute(
        """
        INSERT INTO financial.derived_metrics (
            ticker,
            frequency,
            fiscal_year,
            period_end,
            metric,
            value,
            unit,
            formula_version,
            input_fact_ids,
            status,
            missing_inputs
        )
        VALUES (%s, 'annual', %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (ticker, frequency, period_end, metric, formula_version)
        DO UPDATE SET
            fiscal_year = EXCLUDED.fiscal_year,
            value = EXCLUDED.value,
            unit = EXCLUDED.unit,
            input_fact_ids = EXCLUDED.input_fact_ids,
            status = EXCLUDED.status,
            missing_inputs = EXCLUDED.missing_inputs
        """,
        (
            metric.ticker,
            metric.fiscal_year,
            metric.period_end,
            metric.metric,
            metric.value,
            metric.unit,
            metric.formula_version,
            metric.input_fact_ids,
            metric.status,
            metric.missing_inputs,
        ),
    )


def _store_annual_derived_metrics(
    conn: Any,
    *,
    ticker: str,
    reports: Sequence[dict[str, Any]],
    records: Sequence[_FactRecord],
) -> int:
    periods = _annual_periods(reports, records)
    count = 0
    for index, period in enumerate(periods):
        previous = periods[index + 1].facts if index + 1 < len(periods) else None
        metrics = derive_annual_metrics(
            ticker=ticker,
            fiscal_year=period.fiscal_year,
            period_end=period.period_end,
            current=period.facts,
            prior=previous,
        )
        for metric in metrics:
            _upsert_derived_metric(conn, metric)
            count += 1
    return count


def _as_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return number if number.is_finite() else None


def _unix_timestamp(value: Any) -> datetime | None:
    try:
        timestamp = float(value)
    except (TypeError, ValueError):
        return None
    try:
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None


def _store_vendor_metrics(
    conn: Any,
    *,
    ticker: str,
    raw_payload_id: int,
    payload: Mapping[str, Any],
) -> int:
    metric_values = payload.get("metric") or {}
    if not isinstance(metric_values, Mapping):
        return 0

    count = 0
    for source_name, (metric_name, unit) in _VENDOR_METRICS.items():
        if source_name not in metric_values:
            continue
        value = _as_decimal(metric_values.get(source_name))
        if value is None:
            continue
        conn.execute(
            """
            INSERT INTO financial.vendor_metrics (
                raw_payload_id,
                ticker,
                metric,
                value,
                unit
            )
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (raw_payload_id, metric)
            DO UPDATE SET
                ticker = EXCLUDED.ticker,
                value = EXCLUDED.value,
                unit = EXCLUDED.unit
            """,
            (raw_payload_id, ticker, metric_name, value, unit),
        )
        count += 1
    return count


def _store_market_snapshot(
    conn: Any,
    *,
    ticker: str,
    raw_payload_id: int,
    payload: Mapping[str, Any],
) -> None:
    conn.execute(
        """
        INSERT INTO financial.market_snapshots (
            raw_payload_id,
            ticker,
            source_time,
            current_price,
            change_amount,
            change_percent,
            high_price,
            low_price,
            open_price,
            previous_close
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (raw_payload_id)
        DO UPDATE SET
            ticker = EXCLUDED.ticker,
            source_time = EXCLUDED.source_time,
            current_price = EXCLUDED.current_price,
            change_amount = EXCLUDED.change_amount,
            change_percent = EXCLUDED.change_percent,
            high_price = EXCLUDED.high_price,
            low_price = EXCLUDED.low_price,
            open_price = EXCLUDED.open_price,
            previous_close = EXCLUDED.previous_close
        """,
        (
            raw_payload_id,
            ticker,
            _unix_timestamp(payload.get("t")),
            _as_decimal(payload.get("c")),
            _as_decimal(payload.get("d")),
            _as_decimal(payload.get("dp")),
            _as_decimal(payload.get("h")),
            _as_decimal(payload.get("l")),
            _as_decimal(payload.get("o")),
            _as_decimal(payload.get("pc")),
        ),
    )


def _process_ticker(
    *,
    cfg: Config,
    run_id: str,
    ticker: str,
    client: FinnhubStagingClient,
) -> dict[str, int]:
    """Process one ticker inside one transaction."""

    with financial_connection(readonly=False, cfg=cfg) as conn:
        annual_payload = client.annual_reports(ticker)
        quarterly_payload = client.quarterly_reports(ticker)
        basic_payload = client.basic_financials(ticker)
        quote_payload = client.quote(ticker)

        annual_raw_id = upsert_raw_payload(
            conn,
            run_id=run_id,
            ticker=ticker,
            endpoint="financials_reported",
            frequency="annual",
            payload=annual_payload,
        )
        quarterly_raw_id = upsert_raw_payload(
            conn,
            run_id=run_id,
            ticker=ticker,
            endpoint="financials_reported",
            frequency="quarterly",
            payload=quarterly_payload,
        )
        basic_raw_id = upsert_raw_payload(
            conn,
            run_id=run_id,
            ticker=ticker,
            endpoint="basic_financials",
            payload=basic_payload,
        )
        quote_raw_id = upsert_raw_payload(
            conn,
            run_id=run_id,
            ticker=ticker,
            endpoint="quote",
            payload=quote_payload,
        )

        annual_reports = _select_reports(
            annual_payload,
            limit=int(cfg.financial_annual_reports),
        )
        quarterly_reports = _select_reports(
            quarterly_payload,
            limit=int(cfg.financial_quarterly_reports),
        )

        annual_records = _store_report_facts(
            conn,
            ticker=ticker,
            frequency="annual",
            reports=annual_reports,
            raw_payload_id=annual_raw_id,
        )
        quarterly_records = _store_report_facts(
            conn,
            ticker=ticker,
            frequency="quarterly",
            reports=quarterly_reports,
            raw_payload_id=quarterly_raw_id,
        )
        derived_count = _store_annual_derived_metrics(
            conn,
            ticker=ticker,
            reports=annual_reports,
            records=annual_records,
        )
        vendor_count = _store_vendor_metrics(
            conn,
            ticker=ticker,
            raw_payload_id=basic_raw_id,
            payload=basic_payload,
        )
        _store_market_snapshot(
            conn,
            ticker=ticker,
            raw_payload_id=quote_raw_id,
            payload=quote_payload,
        )
        _mark_company_ingested(conn, ticker)

    return {
        "raw_payloads": 4,
        "annual_reports": len(annual_reports),
        "quarterly_reports": len(quarterly_reports),
        "facts": len(annual_records) + len(quarterly_records),
        "derived_metrics": derived_count,
        "vendor_metrics": vendor_count,
        "market_snapshots": 1,
    }


def _failure(exc: Exception) -> dict[str, str]:
    return {
        "type": type(exc).__name__,
        "message": str(exc)[:1000],
    }


def run_financial_etl(
    *,
    cfg: Config | None = None,
    only_tickers: Sequence[str] | None = None,
    client: FinnhubStagingClient | Any | None = None,
) -> FinancialETLSummary:
    """Run the Step 9 pipeline with preflight and per-ticker isolation.

    When supplied, ``only_tickers`` is an explicit ETL target list and may
    contain companies that have not been extracted into Neo4j yet.  Without
    it, the validated Neo4j/config universe remains the default.  A client can
    be injected for deterministic tests; production callers omit it and the
    Finnhub staging client is constructed from ``Config``.
    """

    cfg = cfg or get_config()
    discovered = validate_universe(load_graph_tickers(cfg), cfg)
    targets = (
        sorted(_normalise_tickers(only_tickers))
        if only_tickers
        else discovered
    )
    run_id = str(uuid4())

    # Run metadata and company rows must be committed before raw payloads are
    # inserted because raw_payloads has foreign keys to both tables.
    with financial_connection(readonly=False, cfg=cfg) as conn:
        _create_run(
            conn,
            run_id=run_id,
            expected_company_count=int(cfg.financial_expected_company_count),
            discovered_tickers=discovered,
        )
        # Explicit targets may not exist in Neo4j yet, but PostgreSQL foreign
        # keys require their company rows before staging Finnhub payloads.
        _upsert_companies(conn, sorted(set(discovered) | set(targets)))

    successful: list[str] = []
    failures: dict[str, dict[str, str]] = {}
    totals = {
        "raw_payloads": 0,
        "annual_reports": 0,
        "quarterly_reports": 0,
        "facts": 0,
        "derived_metrics": 0,
        "vendor_metrics": 0,
        "market_snapshots": 0,
    }

    try:
        if client is None:
            client = FinnhubStagingClient(
                cfg.finnhub_api_key,
                max_retries=cfg.financial_max_retries,
                request_interval_seconds=cfg.financial_request_interval_seconds,
            )
    except Exception as exc:  # API key/SDK configuration failure
        failure = _failure(exc)
        failures = {ticker: failure for ticker in targets}
    else:
        for ticker in targets:
            try:
                ticker_stats = _process_ticker(
                    cfg=cfg,
                    run_id=run_id,
                    ticker=ticker,
                    client=client,
                )
            except Exception as exc:  # noqa: BLE001 - isolate one ticker
                failures[ticker] = _failure(exc)
                continue
            successful.append(ticker)
            for key, value in ticker_stats.items():
                totals[key] += value

    if not failures:
        status: RunStatus = "succeeded"
    elif len(failures) == len(targets):
        status = "failed"
    else:
        status = "partial"

    stats: dict[str, Any] = {
        "target_company_count": len(targets),
        "successful_company_count": len(successful),
        "failed_company_count": len(failures),
        **totals,
    }
    with financial_connection(readonly=False, cfg=cfg) as conn:
        _finish_run(
            conn,
            run_id=run_id,
            status=status,
            successful_tickers=successful,
            failed_tickers=failures,
            stats=stats,
        )

    return FinancialETLSummary(
        run_id=run_id,
        status=status,
        expected_company_count=int(cfg.financial_expected_company_count),
        discovered_tickers=discovered,
        successful_tickers=successful,
        failed_tickers=failures,
        stats=stats,
    )


__all__ = [
    "ETLSummary",
    "FinancialETLSummary",
    "VENDOR_METRICS",
    "load_graph_tickers",
    "run_financial_etl",
    "validate_requested_subset",
    "validate_universe",
]
