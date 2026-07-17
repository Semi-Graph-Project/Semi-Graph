"""Unit tests for the Step 12 read-only PostgreSQL backend."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest

from semigraph.financial import backend
from semigraph.financial.backend import (
    FinancialBackend,
    FinancialQueryResult,
    PostgreSQLBackend,
    row_to_financial_chunk,
)
from semigraph.financial.query_spec import FinancialQuerySpec


class FakeResult:
    def __init__(self, rows):
        self.rows = rows

    def fetchall(self):
        return self.rows


class FakeConnection:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def execute(self, sql, params):
        self.calls.append((sql, params))
        return FakeResult(self.rows)


def _spec(**overrides):
    values = {
        "query": "NVDA annual revenue trend",
        "tickers": ["NVDA"],
        "metrics": ["revenue"],
        "frequency": "annual",
        "operation": "trend",
        "limit": 10,
    }
    values.update(overrides)
    return FinancialQuerySpec(**values)


def _row(**overrides):
    values = {
        "evidence_id": "fact:42",
        "ticker": "NVDA",
        "frequency": "annual",
        "fiscal_year": 2025,
        "fiscal_quarter": None,
        "period_end": date(2025, 1, 26),
        "metric": "revenue",
        "value": Decimal("130497000000.0000000000"),
        "unit": "USD",
        "source_kind": "reported",
        "status": "ok",
        "provenance": {"fact_id": 42},
    }
    values.update(overrides)
    return values


def _install_connection(monkeypatch, rows):
    connection = FakeConnection(rows)
    connection_calls = []

    @contextmanager
    def fake_connection(*, readonly, cfg):
        connection_calls.append((readonly, cfg))
        yield connection

    monkeypatch.setattr(backend, "financial_connection", fake_connection)
    return connection, connection_calls


def test_row_to_chunk_preserves_contract_and_provenance():
    chunk = row_to_financial_chunk(_row(), rank=1)

    assert {
        "chunk_id",
        "text",
        "ticker",
        "fiscal_year",
        "section",
        "score",
    } <= chunk.keys()
    assert chunk["chunk_id"] == "fin_fact:42_1"
    assert chunk["value"] == "130497000000.0000000000"
    assert chunk["period_end"] == "2025-01-26"
    assert chunk["provenance"] == {"fact_id": 42}
    assert "NVDA revenue for FY2025" in chunk["text"]


def test_snapshot_chunk_uses_latest_snapshot_label():
    chunk = row_to_financial_chunk(
        _row(
            frequency=None,
            fiscal_year=None,
            period_end=None,
            observed_at="2026-07-17T00:00:00Z",
            metric="current_price",
            unit="USD/share",
        ),
        rank=2,
    )

    assert chunk["fiscal_year"] == 0
    assert chunk["frequency"] == "snapshot"
    assert chunk["period_end"] is None
    assert chunk["observed_at"] == "2026-07-17T00:00:00Z"
    assert "latest snapshot" in chunk["text"]


def test_quarterly_chunk_keeps_quarter_in_period_label():
    chunk = row_to_financial_chunk(
        _row(frequency="quarterly", fiscal_year=2025, fiscal_quarter=2),
        rank=1,
    )

    assert chunk["frequency"] == "quarterly"
    assert chunk["fiscal_quarter"] == 2
    assert "FY2025 Q2" in chunk["text"]


def test_postgresql_backend_executes_compiled_sql_read_only(monkeypatch):
    connection, connection_calls = _install_connection(monkeypatch, [_row()])
    cfg = SimpleNamespace(financial_max_query_rows=50)

    result = PostgreSQLBackend(cfg).query(_spec(), top_k=5)

    assert isinstance(result, FinancialQueryResult)
    assert connection_calls == [(True, cfg)]
    sql, params = connection.calls[0]
    assert "financial.agent_periodic_metrics" in sql
    assert params["tickers"] == ["NVDA"]
    assert params["limit"] == 5
    assert result.trace["template_id"] == "periodic.trend.v1"
    assert result.trace["returned_count"] == 1
    assert result.trace["missing_count"] == 0


def test_backend_counts_missing_values(monkeypatch):
    _install_connection(monkeypatch, [_row(value=None, status="missing")])

    result = PostgreSQLBackend(
        SimpleNamespace(financial_max_query_rows=50)
    ).query(_spec(), top_k=5)

    assert result.chunks[0]["value"] is None
    assert result.trace["missing_count"] == 1


@pytest.mark.parametrize("top_k", [0, -1, True, 1.5])
def test_backend_rejects_invalid_top_k(top_k):
    with pytest.raises(ValueError, match="top_k"):
        PostgreSQLBackend(
            SimpleNamespace(financial_max_query_rows=50)
        ).query(_spec(), top_k=top_k)


def test_postgresql_backend_satisfies_protocol_shape(monkeypatch):
    _install_connection(monkeypatch, [])
    typed_backend: FinancialBackend = PostgreSQLBackend(
        SimpleNamespace(financial_max_query_rows=50)
    )

    assert isinstance(typed_backend.query(_spec()), FinancialQueryResult)
