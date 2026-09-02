"""Small, testable adapter around the Finnhub Python SDK.

The adapter is deliberately kept separate from PostgreSQL.  It only knows how
to call Finnhub and apply the retry/rate-limit policy; the repository module is
responsible for persisting the response as an immutable raw payload.
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Callable, Protocol


class FinnhubAPI(Protocol):
    """The small part of the SDK used by the staging client."""

    def financials_reported(self, symbol: str, freq: str) -> dict[str, Any]: ...

    def company_basic_financials(
        self, symbol: str, metric: str
    ) -> dict[str, Any]: ...

    def quote(self, symbol: str) -> dict[str, Any]: ...


def payload_sha256(payload: dict[str, Any]) -> str:
    """Return a deterministic hash for a JSON object.

    Sorting keys makes semantically identical objects hash identically even if
    their insertion order differs.  Compact separators avoid hashing optional
    whitespace, while ``ensure_ascii=False`` keeps Unicode stable and readable.
    """

    if not isinstance(payload, dict):
        raise TypeError("Finnhub payload must be a dictionary")
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _normalize_ticker(ticker: str) -> str:
    normalized = str(ticker).strip().upper()
    if not normalized:
        raise ValueError("ticker must not be empty")
    if len(normalized) > 10:
        raise ValueError("ticker must be at most 10 characters")
    return normalized


def _status_code(error: Exception) -> int | None:
    """Extract an HTTP status from common SDK/HTTP exception shapes."""

    direct = getattr(error, "status_code", None)
    if isinstance(direct, int):
        return direct
    response = getattr(error, "response", None)
    nested = getattr(response, "status_code", None)
    return nested if isinstance(nested, int) else None


def _is_retryable(error: Exception) -> bool:
    """Retry network failures, throttling, and server errors only.

    A 401/403/404 is a configuration or request problem and retrying it wastes
    the Finnhub quota.  Exceptions without an HTTP status are treated as
    transient because the SDK commonly wraps connection errors this way.
    """

    status = _status_code(error)
    if status is None:
        return not isinstance(error, (TypeError, ValueError))
    return status == 429 or status >= 500


class FinnhubStagingClient:
    """Finnhub client with bounded retries and a configurable request delay.

    ``client`` is injectable so unit tests never need an API key or network
    access.  Production code can omit it and the Finnhub SDK is imported lazily
    here.
    """

    def __init__(
        self,
        api_key: str,
        max_retries: int = 3,
        request_interval_seconds: float = 1.1,
        retry_backoff_seconds: float = 1.0,
        sleep: Callable[[float], None] = time.sleep,
        client: FinnhubAPI | None = None,
    ):
        if not api_key and client is None:
            raise RuntimeError("FINNHUB_API_KEY is empty")
        if max_retries < 0:
            raise ValueError("max_retries must be >= 0")
        if request_interval_seconds < 0:
            raise ValueError("request_interval_seconds must be >= 0")
        if retry_backoff_seconds < 0:
            raise ValueError("retry_backoff_seconds must be >= 0")

        if client is None:
            # Keep the optional SDK import out of module import time.  This
            # allows hashing/repository code and unit tests to run without the
            # external dependency being initialized.
            import finnhub

            client = finnhub.Client(api_key=api_key)
        self._client = client
        self._max_retries = max_retries
        self._interval = request_interval_seconds
        self._retry_backoff = retry_backoff_seconds
        self._sleep = sleep

    def _call(self, operation: Callable[[], dict[str, Any]]) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                payload = operation() or {}
                if not isinstance(payload, dict):
                    raise TypeError("Finnhub response must be a dictionary")
                if self._interval:
                    self._sleep(self._interval)
                return payload
            except Exception as exc:
                last_error = exc
                if attempt >= self._max_retries or not _is_retryable(exc):
                    break
                delay = self._retry_backoff * (2**attempt)
                if delay:
                    self._sleep(delay)

        raise RuntimeError("Finnhub request failed after retries") from last_error

    def annual_reports(self, ticker: str) -> dict[str, Any]:
        ticker = _normalize_ticker(ticker)
        return self._call(
            lambda: self._client.financials_reported(symbol=ticker, freq="annual")
        )

    def quarterly_reports(self, ticker: str) -> dict[str, Any]:
        ticker = _normalize_ticker(ticker)
        return self._call(
            lambda: self._client.financials_reported(symbol=ticker, freq="quarterly")
        )

    def basic_financials(self, ticker: str) -> dict[str, Any]:
        ticker = _normalize_ticker(ticker)
        return self._call(
            lambda: self._client.company_basic_financials(
                symbol=ticker, metric="all"
            )
        )

    def quote(self, ticker: str) -> dict[str, Any]:
        ticker = _normalize_ticker(ticker)
        return self._call(lambda: self._client.quote(symbol=ticker))


def main() -> int:
    """Run a small live demo of the Finnhub adapter.

    This is intentionally a client-only demo.  It shows the four API calls
    used by the staging workflow; PostgreSQL persistence is handled by
    ``financial.repository.upsert_raw_payload`` in the ETL step.
    """

    from semigraph.config import get_config

    cfg = get_config()
    if not cfg.finnhub_api_key:
        print("FINNHUB_API_KEY is empty; add it to .env before running this demo.")
        return 1

    ticker = "NVDA"
    print(f"[1/5] Creating Finnhub client for {ticker}...")
    client = FinnhubStagingClient(
        cfg.finnhub_api_key,
        max_retries=cfg.financial_max_retries,
        request_interval_seconds=cfg.financial_request_interval_seconds,
    )

    calls = (
        ("annual reports", client.annual_reports),
        ("quarterly reports", client.quarterly_reports),
        ("basic financials", client.basic_financials),
        ("quote", client.quote),
    )
    for step, (name, operation) in enumerate(calls, start=2):
        print(f"[{step}/5] Requesting {name}...")
        payload = operation(ticker)
        print(
            f"       received JSON object with {len(payload)} top-level keys: "
            f"{list(payload)[:5]}"
        )

    print("Done. The returned objects are raw payloads ready for PostgreSQL staging.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


if __name__ == "__main__":
    pass
