"""Unit tests for the Phase F.v2 PostgreSQL bootstrap helpers.

These tests deliberately do not require Docker or a live PostgreSQL server.
Live role permissions and migration execution belong to the integration smoke
test described in the Coach handbook.
"""
from __future__ import annotations

from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from semigraph.financial import db
from scripts import init_financial_db


class FakeConnection:
    """Small context-manager-compatible psycopg connection double."""

    def __init__(self) -> None:
        self.execute_calls: list[tuple[object, tuple[object, ...] | None]] = []
        self.entered = False
        self.exited = False

    def __enter__(self) -> "FakeConnection":
        self.entered = True
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.exited = True

    def execute(self, statement, params=None):
        self.execute_calls.append((statement, params))
        return self


def _config(**overrides):
    values = {
        "postgres_admin_dsn": "postgresql://admin@example.test/semigraph",
        "postgres_agent_dsn": "postgresql://agent@example.test/semigraph",
        "financial_query_timeout_ms": 5000,
        "postgres_agent_user": "semigraph_agent",
        "postgres_agent_password": "test-agent-password",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class TestFinancialConnection:
    def test_writer_connection_uses_admin_dsn(self, monkeypatch):
        fake_conn = FakeConnection()
        calls = []

        def fake_connect(dsn, **kwargs):
            calls.append((dsn, kwargs))
            return fake_conn

        monkeypatch.setattr(db.psycopg, "connect", fake_connect)

        with db.financial_connection(readonly=False, cfg=_config()) as conn:
            assert conn is fake_conn

        assert calls == [
            (
                "postgresql://admin@example.test/semigraph",
                {"row_factory": db.dict_row},
            )
        ]
        assert fake_conn.execute_calls == []
        assert fake_conn.entered is True
        assert fake_conn.exited is True

    def test_readonly_connection_uses_agent_dsn_and_session_guards(
        self, monkeypatch
    ):
        fake_conn = FakeConnection()
        calls = []

        def fake_connect(dsn, **kwargs):
            calls.append((dsn, kwargs))
            return fake_conn

        monkeypatch.setattr(db.psycopg, "connect", fake_connect)

        with db.financial_connection(readonly=True, cfg=_config()):
            pass

        assert calls[0][0] == "postgresql://agent@example.test/semigraph"
        assert calls[0][1] == {"row_factory": db.dict_row}
        assert fake_conn.execute_calls == [
            ("SET TRANSACTION READ ONLY", None),
            (
                "SELECT set_config('statement_timeout', %s, true)",
                ("5000ms",),
            ),
        ]

    @pytest.mark.parametrize(
        ("readonly", "missing_attribute"),
        [
            (False, "postgres_admin_dsn"),
            (True, "postgres_agent_dsn"),
        ],
    )
    def test_missing_dsn_fails_before_connect(
        self, monkeypatch, readonly, missing_attribute
    ):
        cfg = _config(**{missing_attribute: ""})
        connect_called = False

        def fake_connect(*args, **kwargs):
            nonlocal connect_called
            connect_called = True
            raise AssertionError("connect must not be called for an empty DSN")

        monkeypatch.setattr(db.psycopg, "connect", fake_connect)

        with pytest.raises(RuntimeError, match="DSN is empty"):
            with db.financial_connection(readonly=readonly, cfg=cfg):
                pass

        assert connect_called is False


class TestFinancialDatabaseInitializer:
    def test_initializer_executes_schema_and_grants_without_live_database(
        self, tmp_path, monkeypatch, capsys
    ):
        schema_path = tmp_path / "sql" / "financial" / "001_init.sql"
        schema_path.parent.mkdir(parents=True)
        schema_path.write_text(
            "BEGIN; CREATE SCHEMA financial; COMMIT;",
            encoding="utf-8",
        )
        views_path = schema_path.with_name("002_agent_views.sql")
        views_path.write_text(
            "BEGIN; CREATE VIEW financial.agent_metrics AS SELECT 1; COMMIT;",
            encoding="utf-8",
        )

        fake_conn = FakeConnection()
        cfg = _config(project_root=tmp_path)
        connection_calls = []

        @contextmanager
        def fake_financial_connection(*, readonly, cfg):
            connection_calls.append((readonly, cfg))
            yield fake_conn

        monkeypatch.setattr(init_financial_db, "get_config", lambda: cfg)
        monkeypatch.setattr(
            init_financial_db,
            "financial_connection",
            fake_financial_connection,
        )

        init_financial_db.main()

        assert connection_calls == [(False, cfg)]
        assert len(fake_conn.execute_calls) == 7

        schema_statement, schema_params = fake_conn.execute_calls[0]
        assert schema_statement == "BEGIN; CREATE SCHEMA financial; COMMIT;"
        assert schema_params is None
        views_statement, views_params = fake_conn.execute_calls[1]
        assert "CREATE VIEW financial.agent_metrics" in views_statement
        assert views_params is None

        # The remaining calls are role creation plus CONNECT, USAGE, SELECT,
        # and ALTER DEFAULT PRIVILEGES grants. They are composed psycopg SQL
        # objects; exact rendering belongs to the integration smoke test.
        assert all(params is None for _, params in fake_conn.execute_calls[2:])
        assert "Financial schema initialized." in capsys.readouterr().out
