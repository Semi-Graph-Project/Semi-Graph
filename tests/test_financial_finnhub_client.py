"""Unit tests for the Finnhub adapter (no API key or network required)."""

from __future__ import annotations

import pytest

from semigraph.financial.finnhub_client import FinnhubStagingClient, payload_sha256


class FakeFinnhub:
    def __init__(self):
        self.calls: list[tuple[str, dict[str, str]]] = []

    def financials_reported(self, symbol, freq):
        self.calls.append(
            ("financials_reported", {"symbol": symbol, "freq": freq})
        )
        return {"symbol": symbol, "freq": freq}

    def company_basic_financials(self, symbol, metric):
        self.calls.append(
            (
                "company_basic_financials",
                {"symbol": symbol, "metric": metric},
            )
        )
        return {"symbol": symbol, "metric": metric}

    def quote(self, symbol):
        self.calls.append(("quote", {"symbol": symbol}))
        return {"symbol": symbol, "c": 100.0}


def _client(fake=None, **kwargs):
    return FinnhubStagingClient(
        "test-key",
        client=fake or FakeFinnhub(),
        request_interval_seconds=0,
        **kwargs,
    )


def test_payload_hash_is_independent_of_dictionary_insertion_order():
    first = {"symbol": "NVDA", "data": {"b": 2, "a": 1}}
    second = {"data": {"a": 1, "b": 2}, "symbol": "NVDA"}

    assert payload_sha256(first) == payload_sha256(second)
    assert len(payload_sha256(first)) == 64


def test_payload_hash_rejects_non_object():
    with pytest.raises(TypeError, match="dictionary"):
        payload_sha256(["not", "an", "object"])


def test_endpoint_methods_normalize_ticker_and_use_expected_sdk_calls():
    fake = FakeFinnhub()
    client = _client(fake)

    assert client.annual_reports(" nvda ")["freq"] == "annual"
    assert client.quarterly_reports("nvda")["freq"] == "quarterly"
    assert client.basic_financials("nvda")["metric"] == "all"
    assert client.quote("nvda")["symbol"] == "NVDA"

    assert fake.calls == [
        ("financials_reported", {"symbol": "NVDA", "freq": "annual"}),
        ("financials_reported", {"symbol": "NVDA", "freq": "quarterly"}),
        ("company_basic_financials", {"symbol": "NVDA", "metric": "all"}),
        ("quote", {"symbol": "NVDA"}),
    ]


def test_empty_api_key_is_rejected_without_an_injected_client():
    with pytest.raises(RuntimeError, match="FINNHUB_API_KEY"):
        FinnhubStagingClient("", request_interval_seconds=0)


def test_transient_error_is_retried_with_exponential_backoff_and_interval():
    calls = 0
    sleeps: list[float] = []

    def operation():
        nonlocal calls
        calls += 1
        if calls == 1:
            raise ConnectionError("temporary network failure")
        return {"ok": True}

    client = _client(sleep=sleeps.append, retry_backoff_seconds=0.5)
    assert client._call(operation) == {"ok": True}
    assert calls == 2
    assert sleeps == [0.5]


def test_non_retryable_http_error_fails_immediately():
    calls = 0
    sleeps: list[float] = []

    class Unauthorized(Exception):
        status_code = 401

    def operation():
        nonlocal calls
        calls += 1
        raise Unauthorized("bad key")

    client = _client(sleep=sleeps.append, max_retries=3)
    with pytest.raises(RuntimeError, match="after retries"):
        client._call(operation)

    assert calls == 1
    assert sleeps == []


def test_retry_limit_is_bounded():
    calls = 0

    def operation():
        nonlocal calls
        calls += 1
        raise ConnectionError("down")

    client = _client(max_retries=2, retry_backoff_seconds=0)
    with pytest.raises(RuntimeError, match="after retries"):
        client._call(operation)
    assert calls == 3


@pytest.mark.parametrize("ticker", ["", "   ", "TOO-LONG-TICKER"])
def test_invalid_ticker_is_rejected(ticker):
    client = _client()
    with pytest.raises(ValueError, match="ticker"):
        client.quote(ticker)


def test_non_dictionary_response_is_not_retried():
    calls = 0

    def operation():
        nonlocal calls
        calls += 1
        return ["unexpected"]

    client = _client(max_retries=3, retry_backoff_seconds=0)
    with pytest.raises(RuntimeError, match="after retries"):
        client._call(operation)
    assert calls == 1
