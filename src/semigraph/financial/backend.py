"""Read-only PostgreSQL backend for typed financial queries."""

from __future__ import annotations

import time
from collections.abc import Mapping
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field

from semigraph.config import Config, get_config
from semigraph.financial.db import financial_connection
from semigraph.financial.query_spec import FinancialQuerySpec
from semigraph.financial.sql_compiler import compile_financial_query


class FinancialQueryResult(BaseModel):
    """Chunks consumed by the agent plus an auditable execution trace."""

    model_config = ConfigDict(extra="forbid")

    chunks: list[dict[str, Any]] = Field(default_factory=list)
    trace: dict[str, Any] = Field(default_factory=dict)


class FinancialBackend(Protocol):
    """Internal contract implemented by typed financial backends."""

    def query(
        self,
        spec: FinancialQuerySpec,
        *,
        top_k: int = 5,
    ) -> FinancialQueryResult:
        ...


def row_to_financial_chunk(
    row: Mapping[str, Any],
    *,
    rank: int,
) -> dict[str, Any]:
    """Convert one curated-view row into the retriever chunk contract."""

    ticker = str(row["ticker"])
    metric = str(row["metric"])
    frequency = str(row.get("frequency") or "snapshot")
    fiscal_year = int(row.get("fiscal_year") or 0)
    fiscal_quarter = row.get("fiscal_quarter")
    period_end = row.get("period_end")
    observed_at = row.get("observed_at")
    value = row.get("value")
    unit = row.get("unit")
    status = str(row.get("status") or "ok")
    source_kind = str(row.get("source_kind") or "unknown")

    if value is None:
        value_text = "unavailable"
    else:
        value_text = f"{value} {unit or ''}".strip()

    if frequency == "quarterly" and fiscal_year and fiscal_quarter:
        period_label = f"FY{fiscal_year} Q{fiscal_quarter}"
    elif fiscal_year:
        period_label = f"FY{fiscal_year}"
    else:
        period_label = "latest snapshot"
    text = (
        f"{ticker} {metric} for {period_label} "
        f"(period end {period_end or 'n/a'}) is {value_text}. "
        f"Status: {status}. Source kind: {source_kind}."
    )

    return {
        # Stable six-key contract shared by every retriever.
        "chunk_id": f"fin_{row['evidence_id']}_{rank}",
        "text": text,
        "ticker": ticker,
        "fiscal_year": fiscal_year,
        "section": f"Financial_{metric}",
        "score": 1.0,
        # Structured values retained for evaluation and citations.
        "metric": metric,
        "value": str(value) if value is not None else None,
        "unit": unit,
        "frequency": frequency,
        "fiscal_quarter": int(fiscal_quarter) if fiscal_quarter else None,
        "period_end": str(period_end) if period_end else None,
        "observed_at": str(observed_at) if observed_at else None,
        "status": status,
        "source_kind": source_kind,
        "provenance": row.get("provenance") or {},
    }


class PostgreSQLBackend:
    """Execute compiler-generated SQL against the read-only agent role."""

    def __init__(self, cfg: Config | None = None):
        self.cfg = cfg or get_config()

    def query(
        self,
        spec: FinancialQuerySpec,
        *,
        top_k: int = 5,
    ) -> FinancialQueryResult:
        if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k < 1:
            raise ValueError("top_k must be a positive integer")

        max_rows = int(self.cfg.financial_max_query_rows)
        effective_limit = min(spec.limit, top_k, max_rows)
        effective_spec = spec.model_copy(update={"limit": effective_limit})
        compiled = compile_financial_query(effective_spec)
        started = time.perf_counter()

        with financial_connection(readonly=True, cfg=self.cfg) as conn:
            rows = conn.execute(compiled.sql, compiled.params).fetchall()

        if not all(isinstance(row, Mapping) for row in rows):
            raise TypeError("financial backend requires psycopg dict_row results")

        chunks = [
            row_to_financial_chunk(row, rank=index)
            for index, row in enumerate(rows, start=1)
        ]
        return FinancialQueryResult(
            chunks=chunks,
            trace={
                "retriever": "financial",
                "profile": "postgresql_typed_v1",
                "query_spec": effective_spec.model_dump(mode="json"),
                "template_id": compiled.template_id,
                "bound_params": compiled.params,
                "returned_count": len(chunks),
                "latency_sec": round(time.perf_counter() - started, 4),
                "missing_count": sum(
                    chunk.get("value") is None for chunk in chunks
                ),
            },
        )


__all__ = [
    "FinancialBackend",
    "FinancialQueryResult",
    "PostgreSQLBackend",
    "row_to_financial_chunk",
]
