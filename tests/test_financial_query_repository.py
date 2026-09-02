"""Unit tests for the Step 10 curated financial query repository."""

from __future__ import annotations

from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from semigraph.financial import query_repository


class FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class FakeConnection:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def execute(self, statement, params):
        self.calls.append((statement, params))
        return FakeResult(self.rows)


def _cfg(max_rows=50):
    return SimpleNamespace(financial_max_query_rows=max_rows)


def _install_connection(monkeypatch, rows):
    connection = FakeConnection(rows)
    calls = []

    @contextmanager
    def fake_connection(readonly, cfg):
        calls.append((readonly, cfg))
        yield connection

    monkeypatch.setattr(
        query_repository,
        "financial_connection",
        fake_connection,
    )
    return connection, calls


def test_periodic_query_uses_curated_view_and_bound_params(monkeypatch):
    row = {
        "evidence_id": "42",
        "ticker": "NVDA",
        "metric": "revenue",
    }
    connection, connection_calls = _install_connection(monkeypatch, [row])
    cfg = _cfg()

    result = query_repository.query_periodic_metrics(
        tickers=["nvda", "NVDA"],
        metrics=["revenue"],
        frequency="annual",
        start_year=2023,
        end_year=2025,
        limit=10,
        cfg=cfg,
    )

    assert result == [row]
    assert connection_calls == [(True, cfg)]
    statement, params = connection.calls[0]
    assert "FROM financial.agent_periodic_metrics" in statement
    assert "NVDA" not in statement
    assert params == {
        "tickers": ["NVDA"],
        "metrics": ["revenue"],
        "frequency": "annual",
        "start_year": 2023,
        "end_year": 2025,
        "quarter": None,
        "limit": 10,
    }


def test_market_query_uses_curated_view(monkeypatch):
    connection, _ = _install_connection(monkeypatch, [])

    result = query_repository.query_market_metrics(
        tickers=["amd"],
        metrics=["current_price", "pe_ttm"],
        cfg=_cfg(),
    )

    assert result == []
    statement, params = connection.calls[0]
    assert "FROM financial.agent_market_metrics" in statement
    assert params["tickers"] == ["AMD"]
    assert params["metrics"] == ["current_price", "pe_ttm"]


@pytest.mark.parametrize("frequency", ["snapshot", "monthly", ""])
def test_periodic_query_rejects_unsupported_frequency(frequency):
    with pytest.raises(ValueError, match="frequency"):
        query_repository.query_periodic_metrics(
            tickers=["NVDA"],
            metrics=["revenue"],
            frequency=frequency,
            cfg=_cfg(),
        )


def test_periodic_query_rejects_quarter_for_annual():
    with pytest.raises(ValueError, match="quarter"):
        query_repository.query_periodic_metrics(
            tickers=["NVDA"],
            metrics=["revenue"],
            frequency="annual",
            quarter=1,
            cfg=_cfg(),
        )


def test_repository_rejects_empty_filters_and_excessive_limit():
    with pytest.raises(ValueError, match="tickers"):
        query_repository.query_market_metrics(
            tickers=[],
            metrics=["current_price"],
            cfg=_cfg(),
        )
    with pytest.raises(ValueError, match="between 1 and 5"):
        query_repository.query_market_metrics(
            tickers=["NVDA"],
            metrics=["current_price"],
            limit=6,
            cfg=_cfg(max_rows=5),
        )


def test_migration_defines_revision_and_gross_profit_precedence():
    migration = (
        query_repository.get_config().project_root
        / "sql"
        / "financial"
        / "002_agent_views.sql"
    ).read_text(encoding="utf-8")

    assert "CREATE OR REPLACE VIEW financial.latest_financial_facts" in migration
    assert "row_number() OVER" in migration
    assert "CREATE OR REPLACE VIEW financial.agent_periodic_metrics" in migration
    assert "derived.metric = 'gross_profit'" in migration
    assert "CREATE OR REPLACE VIEW financial.agent_market_metrics" in migration
