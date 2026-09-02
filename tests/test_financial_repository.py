"""Unit tests for raw JSONB staging and ingestion-run associations."""

from __future__ import annotations

import json

import pytest

from semigraph.financial.repository import upsert_raw_payload


class FakeResult:
    def __init__(self, row):
        self.row = row

    def fetchone(self):
        return self.row


class FakeConnection:
    def __init__(self, inserted_id=42, existing_id=42):
        self.inserted_id = inserted_id
        self.existing_id = existing_id
        self.execute_calls: list[tuple[str, tuple[object, ...] | None]] = []

    def execute(self, statement, params=None):
        self.execute_calls.append((str(statement), params))
        sql = str(statement)
        if "INSERT INTO financial.raw_payloads" in sql:
            return FakeResult(
                {"raw_payload_id": self.inserted_id}
                if self.inserted_id is not None
                else None
            )
        if "SELECT raw_payload_id" in sql:
            return FakeResult({"raw_payload_id": self.existing_id})
        return FakeResult(None)


def test_inserted_payload_is_linked_to_run_and_returns_id():
    conn = FakeConnection(inserted_id=101)

    result = upsert_raw_payload(
        conn,
        run_id="run-1",
        ticker=" nvda ",
        endpoint="financials_reported",
        frequency="annual",
        payload={"symbol": "NVDA", "data": [{"value": 1}]},
    )

    assert result == 101
    assert len(conn.execute_calls) == 2
    insert_sql, insert_params = conn.execute_calls[0]
    assert "ON CONFLICT (ticker, endpoint, frequency, payload_sha256)" in insert_sql
    assert "DO NOTHING" in insert_sql
    assert insert_params[:4] == ("run-1", "NVDA", "financials_reported", "annual")
    assert json.loads(insert_params[5]) == {"symbol": "NVDA", "data": [{"value": 1}]}

    association_sql, association_params = conn.execute_calls[1]
    assert "ingestion_run_payloads" in association_sql
    assert association_params == ("run-1", 101)


def test_duplicate_payload_is_selected_and_still_associated():
    conn = FakeConnection(inserted_id=None, existing_id=202)

    result = upsert_raw_payload(
        conn,
        run_id="run-2",
        ticker="AMD",
        endpoint="quote",
        payload={"c": 123.4},
    )

    assert result == 202
    assert len(conn.execute_calls) == 3
    assert "SELECT raw_payload_id" in conn.execute_calls[1][0]
    assert conn.execute_calls[2][1] == ("run-2", 202)


@pytest.mark.parametrize(
    ("endpoint", "frequency"),
    [
        ("financials_reported", "none"),
        ("basic_financials", "annual"),
        ("quote", "quarterly"),
        ("unknown", "none"),
    ],
)
def test_endpoint_frequency_contract_is_validated_before_sql(endpoint, frequency):
    conn = FakeConnection()
    with pytest.raises(ValueError):
        upsert_raw_payload(
            conn,
            run_id="run-1",
            ticker="NVDA",
            endpoint=endpoint,
            frequency=frequency,
            payload={},
        )
    assert conn.execute_calls == []


def test_payload_must_be_a_json_object():
    conn = FakeConnection()
    with pytest.raises(TypeError, match="dictionary"):
        upsert_raw_payload(
            conn,
            run_id="run-1",
            ticker="NVDA",
            endpoint="quote",
            payload=["not", "an", "object"],
        )
