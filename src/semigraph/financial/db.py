from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import psycopg
from psycopg import Connection
from psycopg.rows import dict_row

from semigraph.config import Config, get_config


@contextmanager
def financial_connection(
    readonly: bool,
    cfg: Config | None = None,
) -> Iterator[Connection]:
    cfg = cfg or get_config()
    dsn = cfg.postgres_agent_dsn if readonly else cfg.postgres_admin_dsn
    if not dsn:
        role = "POSTGRES_AGENT_DSN" if readonly else "POSTGRES_ADMIN_DSN"
        raise RuntimeError(f"{role} is empty")

    with psycopg.connect(dsn, row_factory=dict_row) as conn:
        if readonly:
            conn.execute("SET TRANSACTION READ ONLY")
            conn.execute(
                "SELECT set_config('statement_timeout', %s, true)",
                (f"{cfg.financial_query_timeout_ms}ms",),
            )
        yield conn
