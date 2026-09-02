"""Persistence helpers for Finnhub raw responses.

This module is intentionally small: Step 6 stages the vendor response as
JSONB and records which ingestion run observed it.  Normalisation and metric
derivation belong to later ETL steps.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from semigraph.financial.finnhub_client import payload_sha256


_ENDPOINT_FREQUENCIES = {
    "financials_reported": {"annual", "quarterly"},
    "basic_financials": {"none"},
    "quote": {"none"},
}


def _row_value(row: Any, key: str) -> Any:
    """Read both psycopg ``dict_row`` and simple tuple test doubles."""

    if isinstance(row, Mapping):
        return row[key]
    return row[0]


def _validate_dimensions(
    ticker: str, endpoint: str, frequency: str
) -> tuple[str, str, str]:
    normalized_ticker = str(ticker).strip().upper()
    if not normalized_ticker or len(normalized_ticker) > 10:
        raise ValueError("ticker must be 1-10 characters")
    if endpoint not in _ENDPOINT_FREQUENCIES:
        raise ValueError(f"unsupported Finnhub endpoint: {endpoint}")
    if frequency not in _ENDPOINT_FREQUENCIES[endpoint]:
        raise ValueError(
            f"frequency {frequency!r} is invalid for endpoint {endpoint!r}"
        )
    return normalized_ticker, endpoint, frequency


def upsert_raw_payload(
    conn: Any,
    run_id: str,
    ticker: str,
    endpoint: str,
    payload: dict[str, Any],
    frequency: str = "none",
) -> int:
    """Insert a raw response once and link it to ``run_id``.

    The unique key contains the deterministic payload hash.  ``DO NOTHING``
    deliberately keeps the first JSON document immutable; if the same vendor
    response is seen by another run, only the association row is added.
    The caller owns the transaction and decides when to commit.
    """

    ticker, endpoint, frequency = _validate_dimensions(ticker, endpoint, frequency)
    if not isinstance(payload, dict):
        raise TypeError("payload must be a dictionary")

    serialized = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    digest = payload_sha256(payload)
    params = (run_id, ticker, endpoint, frequency, digest, serialized)

    insert_result = conn.execute(
        """
        INSERT INTO financial.raw_payloads (
            first_seen_run_id,
            ticker,
            endpoint,
            frequency,
            payload_sha256,
            payload
        )
        VALUES (%s, %s, %s, %s, %s, %s::jsonb)
        ON CONFLICT (ticker, endpoint, frequency, payload_sha256)
        DO NOTHING
        RETURNING raw_payload_id
        """,
        params,
    )
    row = insert_result.fetchone()
    if row is None:
        row = conn.execute(
            """
            SELECT raw_payload_id
            FROM financial.raw_payloads
            WHERE ticker = %s
              AND endpoint = %s
              AND frequency = %s
              AND payload_sha256 = %s
            """,
            (ticker, endpoint, frequency, digest),
        ).fetchone()
    if row is None:
        raise RuntimeError("raw payload insert succeeded but its id was not found")

    raw_payload_id = int(_row_value(row, "raw_payload_id"))
    conn.execute(
        """
        INSERT INTO financial.ingestion_run_payloads (run_id, raw_payload_id)
        VALUES (%s, %s)
        ON CONFLICT (run_id, raw_payload_id) DO NOTHING
        """,
        (run_id, raw_payload_id),
    )
    return raw_payload_id
