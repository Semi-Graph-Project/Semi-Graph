"""Compatibility wrapper for typed PostgreSQL financial retrieval.

The default path turns natural language into a validated ``FinancialQuerySpec``.
Only the deterministic compiler may create SQL.  The old direct Finnhub backend
is retained as an explicitly configured migration fallback.
"""
from __future__ import annotations

import json
from typing import Any, Optional

from pydantic import ValidationError

from semigraph.config import Config, get_config
from semigraph.connections import get_llm
from semigraph.financial.backend import (
    FinancialBackend,
    FinancialQueryResult,
    PostgreSQLBackend,
)
from semigraph.financial.query_spec import (
    FinancialQuerySpec,
    PERIODIC_METRICS,
    SNAPSHOT_METRICS,
)
from semigraph.online._ticker import resolve_tickers


# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

SNAPSHOT_KINDS: tuple[str, ...] = ("financials_annual", "key_metrics", "quote")


class FinancialIntentParseError(ValueError):
    """Raised after both financial-intent parsing attempts fail validation."""


class UnsupportedFinancialQuery(ValueError):
    """Raised when the requested metric is outside the configured registry."""


# ─────────────────────────────────────────────────────────────────────────────
# Helpers (pure functions — used by tests directly)
# ─────────────────────────────────────────────────────────────────────────────


def _make_chunk(ticker: str, kind: str, text: str, fiscal_year: int) -> dict:
    """Wrap a snapshot text into the 6-key contract used by all retrievers.

    `section` prefix "Financial_" distinguishes API-sourced chunks from 10-K
    chunks ("Item_1", "Item_1A", "Item_7") so the LLM system prompt + UI can
    surface the source kind explicitly.
    """
    return {
        "chunk_id": f"fin_{ticker}_{kind}_{fiscal_year}",
        "text": text,
        "ticker": ticker,
        "fiscal_year": fiscal_year,
        "section": f"Financial_{kind}",
        "score": 1.0,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Natural-language query -> validated spec
# ─────────────────────────────────────────────────────────────────────────────


def _response_text(response: Any) -> str:
    content = response.content if hasattr(response, "content") else response
    if not isinstance(content, str):
        raise ValueError("LLM response content must be a string")
    return content.strip()


def _decode_json_object(text: str) -> dict[str, Any]:
    """Accept plain JSON and tolerate a surrounding Markdown code fence."""

    candidate = text.strip()
    if candidate.startswith("```"):
        lines = candidate.splitlines()
        if len(lines) >= 3 and lines[-1].strip() == "```":
            candidate = "\n".join(lines[1:-1]).strip()

    try:
        value = json.loads(candidate)
    except json.JSONDecodeError:
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("LLM response does not contain a JSON object")
        value = json.loads(candidate[start : end + 1])

    if not isinstance(value, dict):
        raise ValueError("LLM response must be one JSON object")
    return value


def _financial_intent_schema() -> dict[str, Any]:
    """Describe supported-spec and unsupported decision response shapes."""

    schema = FinancialQuerySpec.model_json_schema()
    intent_properties = {
        name: definition
        for name, definition in schema["properties"].items()
        if name not in {"query", "tickers"}
    }
    intent_required = [
        name
        for name in schema.get("required", [])
        if name not in {"query", "tickers"}
    ]
    return {
        "$defs": schema.get("$defs", {}),
        "oneOf": [
            {
                "type": "object",
                "properties": {
                    "supported": {"const": True},
                    "unsupported_reason": {"type": "null"},
                    **intent_properties,
                },
                "required": ["supported", *intent_required],
                "additionalProperties": False,
            },
            {
                "type": "object",
                "properties": {
                    "supported": {"const": False},
                    "unsupported_reason": {"type": "string", "minLength": 1},
                },
                "required": ["supported", "unsupported_reason"],
                "additionalProperties": False,
            },
        ]
    }


def _intent_messages(
    query: str,
    tickers: list[str],
    validation_feedback: str | None,
) -> list[dict[str, str]]:
    schema = json.dumps(_financial_intent_schema(), ensure_ascii=False)
    feedback = (
        f"\nThe previous output failed validation:\n{validation_feedback}\n"
        if validation_feedback
        else ""
    )
    system = f"""You translate a financial question into one JSON intent object.
Never write SQL. Do not output query or tickers; the Financial Tool owns them.
Output JSON only, with no explanation.

Allowed periodic metrics: {sorted(PERIODIC_METRICS)}
Allowed snapshot metrics: {sorted(SNAPSHOT_METRICS)}

Metric rules:
- Return supported=true only when every requested metric exists in the allowed
  registry and can be answered with the available frequency semantics.
- With supported=true, select only the exact metric requested by the user and
  set unsupported_reason=null or omit it.
- Never substitute a missing metric with a similar metric or its components.
- If any requested metric is unavailable, return only supported=false and a
  concise unsupported_reason. Do not return substitute metrics.

frequency meanings:
- annual: one value per fiscal year
- quarterly: one value per fiscal quarter
- snapshot: latest market/vendor observation without a fiscal period

operation meanings:
- lookup: retrieve a metric
- compare: compare at least two companies
- trend: retrieve an ordered time series
- rank: order companies by exactly one metric
- aggregate: avg/min/max/sum of exactly one periodic metric

fiscal period rules:
- exact FY2025: start_year=2025 and end_year=2025
- FY2023 through FY2025: start_year=2023 and end_year=2025
- since/from FY2025: start_year=2025, end_year=null, operation=trend
- through/until FY2025: start_year=null, end_year=2025, operation=trend
- latest available period: start_year=null and end_year=null

Financial intent JSON schema:
{schema}
{feedback}"""
    user = json.dumps(
        {
            "query": query,
            "resolved_tickers": tickers,
            "instruction": (
                "Return only the intent fields. Do not return query or tickers."
            ),
        },
        ensure_ascii=False,
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def _build_financial_query_spec(
    query: str,
    tickers: list[str],
    cfg: Config,
) -> FinancialQuerySpec:
    """Resolve LLM-owned intent fields and assemble the tool-owned query spec."""

    llm = get_llm(cfg)
    feedback: str | None = None
    errors: list[str] = []

    for _ in range(2):
        try:
            response = llm.invoke(
                _intent_messages(
                    query,
                    tickers=tickers,
                    validation_feedback=feedback,
                )
            )
            intent = _decode_json_object(_response_text(response))
            forbidden = sorted({"query", "tickers"} & intent.keys())
            if forbidden:
                raise ValueError(
                    f"LLM must not provide tool-owned fields: {forbidden}"
                )

            supported = intent.pop("supported", None)
            unsupported_reason = intent.pop("unsupported_reason", None)
            if supported is False:
                if intent:
                    raise ValueError(
                        "Unsupported intent must not include query-spec fields"
                    )
                if (
                    not isinstance(unsupported_reason, str)
                    or not unsupported_reason.strip()
                ):
                    raise ValueError(
                        "Unsupported intent requires unsupported_reason"
                    )
                raise UnsupportedFinancialQuery(unsupported_reason.strip())
            if supported is not True:
                raise ValueError("Intent must include boolean supported")
            if unsupported_reason not in (None, ""):
                raise ValueError(
                    "Supported intent cannot include unsupported_reason"
                )

            return FinancialQuerySpec.model_validate(
                {"query": query, "tickers": tickers, **intent}
            )
        except UnsupportedFinancialQuery:
            raise
        except (ValidationError, ValueError) as exc:
            feedback = str(exc)
            errors.append(feedback)

    raise FinancialIntentParseError(
        "Could not produce a valid FinancialQuerySpec after 2 attempts: "
        + " | ".join(errors)
    )


# ─────────────────────────────────────────────────────────────────────────────
# v1: FinnhubAPIBackend — direct API call per snapshot kind
# ─────────────────────────────────────────────────────────────────────────────


class FinnhubAPIBackend:
    """v1 backend: Finnhub API calls returned as natural-language snapshots.

    Three snapshot kinds (per Phase F.v1 scope):
      - financials_annual : revenue, gross/operating/net income, margins
      - key_metrics       : P/E, ROE, debt/equity, market cap
      - quote             : current price, day change

    Each call is wrapped in try/except + 1 retry on transient errors so a single
    failed metric never poisons the whole result. Failed snapshots are dropped
    silently — the orchestrator filters out None values.
    """

    def __init__(self, api_key: str):
        if not api_key:
            raise RuntimeError(
                "FINNHUB_API_KEY is empty — set it in .env (sign up free at "
                "https://finnhub.io/dashboard)"
            )
        # Late import: keeps semigraph importable even when finnhub-python
        # is not yet installed. Real call will fail loudly with ModuleNotFoundError.
        import finnhub
        self.client = finnhub.Client(api_key=api_key)

    # -- public API expected by the Protocol ---------------------------------

    def search(self, query: str, tickers: list[str], top_k: int = 5) -> list[dict]:
        chunks: list[dict] = []
        for ticker in tickers:
            for kind in SNAPSHOT_KINDS:
                c = self._dispatch_snapshot(ticker, kind)
                if c is not None:
                    chunks.append(c)
        return chunks[:top_k]

    # -- snapshot dispatch ---------------------------------------------------

    def _dispatch_snapshot(self, ticker: str, kind: str) -> Optional[dict]:
        try:
            if kind == "financials_annual":
                return self._snapshot_financials_annual(ticker)
            if kind == "key_metrics":
                return self._snapshot_key_metrics(ticker)
            if kind == "quote":
                return self._snapshot_quote(ticker)
        except Exception as exc:  # noqa: BLE001 — wide catch by design
            # Snapshot-level isolation: one failure must not kill others.
            print(f"[financial_search] {ticker} {kind} failed: {exc}")
        return None

    # -- snapshot implementations --------------------------------------------

    def _snapshot_financials_annual(self, ticker: str) -> Optional[dict]:
        """Annual income-statement summary — revenue + gross/operating/net income."""
        resp = self.client.financials_reported(symbol=ticker, freq="annual")
        data = (resp or {}).get("data") or []
        if not data:
            return None
        latest = data[0]
        fy = int(latest.get("year") or 0)
        report = latest.get("report") or {}
        ic = report.get("ic") or []  # income statement rows

        # Finnhub income-statement rows are dicts with `concept`/`label`/`value`.
        # Map common concepts → readable numbers. Concept naming follows US-GAAP.
        def find(concepts: tuple[str, ...]) -> Optional[float]:
            for row in ic:
                concept = (row.get("concept") or "").lower()
                if any(c in concept for c in concepts):
                    try:
                        return float(row.get("value"))
                    except (TypeError, ValueError):
                        continue
            return None

        revenue = find(("revenues", "revenue", "salesrevenuenet"))
        gross = find(("grossprofit",))
        op_inc = find(("operatingincomeloss",))
        net_inc = find(("netincomeloss",))

        def fmt(v: Optional[float]) -> str:
            if v is None:
                return "n/a"
            return f"${v / 1e9:.2f}B" if abs(v) >= 1e9 else f"${v / 1e6:.0f}M"

        def margin(num: Optional[float], denom: Optional[float]) -> str:
            if not num or not denom:
                return "n/a"
            return f"{100 * num / denom:.1f}%"

        text = (
            f"{ticker} FY{fy} annual financials (Finnhub): "
            f"revenue {fmt(revenue)}, "
            f"gross profit {fmt(gross)} (margin {margin(gross, revenue)}), "
            f"operating income {fmt(op_inc)} (margin {margin(op_inc, revenue)}), "
            f"net income {fmt(net_inc)} (margin {margin(net_inc, revenue)})."
        )
        return _make_chunk(ticker, "financials_annual", text, fy)

    def _snapshot_key_metrics(self, ticker: str) -> Optional[dict]:
        """P/E, ROE, margins, debt/equity, market cap."""
        resp = self.client.company_basic_financials(symbol=ticker, metric="all")
        metric = (resp or {}).get("metric") or {}
        if not metric:
            return None

        def g(key: str) -> Optional[float]:
            v = metric.get(key)
            try:
                return float(v) if v is not None else None
            except (TypeError, ValueError):
                return None

        pe_ttm = g("peTTM") or g("peNormalizedAnnual")
        roe = g("roeTTM") or g("roeRfy")
        gm = g("grossMarginTTM") or g("grossMarginAnnual")
        om = g("operatingMarginTTM") or g("operatingMarginAnnual")
        de = g("totalDebt/totalEquityAnnual") or g("longTermDebt/equityAnnual")
        mcap = g("marketCapitalization")

        def f1(v: Optional[float], suffix: str = "x") -> str:
            return f"{v:.1f}{suffix}" if v is not None else "n/a"

        def fpct(v: Optional[float]) -> str:
            return f"{v:.1f}%" if v is not None else "n/a"

        def fcap(v: Optional[float]) -> str:
            if v is None:
                return "n/a"
            return f"${v / 1000:.1f}B" if v >= 1000 else f"${v:.0f}M"

        text = (
            f"{ticker} key metrics (Finnhub TTM/latest): "
            f"P/E {f1(pe_ttm)}, "
            f"ROE {fpct(roe)}, "
            f"gross margin {fpct(gm)}, "
            f"operating margin {fpct(om)}, "
            f"debt/equity {f1(de, 'x')}, "
            f"market cap {fcap(mcap)}."
        )
        # Use 0 as fiscal_year for TTM/realtime metrics (no fixed FY).
        return _make_chunk(ticker, "key_metrics", text, 0)

    def _snapshot_quote(self, ticker: str) -> Optional[dict]:
        """Current price + day change + day range (real-time)."""
        q = self.client.quote(symbol=ticker)
        if not q or q.get("c") in (None, 0):
            return None
        cur = q.get("c")
        prev = q.get("pc")
        high = q.get("h")
        low = q.get("l")
        delta = (cur - prev) if (cur is not None and prev is not None) else None
        pct = (100 * delta / prev) if (delta is not None and prev) else None

        def f(v) -> str:
            return f"${v:.2f}" if isinstance(v, (int, float)) else "n/a"

        change_str = (
            f"{delta:+.2f} ({pct:+.2f}%)" if delta is not None and pct is not None else "n/a"
        )
        text = (
            f"{ticker} latest quote (Finnhub real-time): "
            f"price {f(cur)} (prev close {f(prev)}, change {change_str}), "
            f"day range {f(low)}–{f(high)}."
        )
        return _make_chunk(ticker, "quote", text, 0)


# ─────────────────────────────────────────────────────────────────────────────
# Backend factory — single swap point during the v1 -> v2 migration
# ─────────────────────────────────────────────────────────────────────────────


def _get_backend(
    cfg: Optional[Config] = None,
) -> FinancialBackend | FinnhubAPIBackend:
    """Select PostgreSQL by default; Finnhub must be opted into explicitly."""

    cfg = cfg or get_config()
    backend_name = cfg.financial_backend.strip().lower()
    if backend_name == "postgresql":
        return PostgreSQLBackend(cfg)
    if backend_name == "finnhub":
        return FinnhubAPIBackend(api_key=cfg.finnhub_api_key)
    raise ValueError(f"Unsupported financial backend: {cfg.financial_backend!r}")


def _empty_result(
    reason: str,
    unsupported_reason: str | None = None,
) -> dict[str, Any]:
    result = {
        "chunks": [],
        "trace": {
            "retriever": "financial",
            "profile": "financial_compatibility_v2",
            "status": "skipped",
            "reason": reason,
            "returned_count": 0,
        },
    }
    if unsupported_reason:
        result["trace"]["unsupported_reason"] = unsupported_reason
    return result


def _error_result(exc: Exception, stage: str) -> dict[str, Any]:
    return {
        "chunks": [],
        "trace": {
            "retriever": "financial",
            "profile": "financial_compatibility_v2",
            "status": "error",
            "stage": stage,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "returned_count": 0,
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# Public orchestrator — registered in RETRIEVERS dispatch
# ─────────────────────────────────────────────────────────────────────────────


def financial_search(
    query: str,
    top_k_chunks: int = 5,
    cfg: Optional[Config] = None,
    use_expansion: bool = True,
) -> dict[str, Any]:
    """Resolve a natural-language query entirely inside the Financial Tool.

    The caller supplies only a query.  This function owns ticker resolution and
    spec construction; the LLM supplies only financial intent fields.  The
    function always returns ``{"chunks": ..., "trace": ...}``.
    """

    if not query.strip():
        return _empty_result("empty_query")

    cfg = cfg or get_config()
    if isinstance(top_k_chunks, bool) or not isinstance(top_k_chunks, int):
        return _error_result(
            TypeError("top_k_chunks must be an integer"),
            stage="request_validation",
        )
    if top_k_chunks < 1:
        return _error_result(
            ValueError("top_k_chunks must be positive"),
            stage="request_validation",
        )

    try:
        tickers = resolve_tickers(
            query,
            cfg=cfg,
            use_expansion=use_expansion,
        )
        if not tickers:
            return _empty_result("no_corpus_ticker")
        parsed_spec = _build_financial_query_spec(
            query,
            tickers=tickers,
            cfg=cfg,
        )
    except UnsupportedFinancialQuery as exc:
        return _empty_result(
            "unsupported_metric",
            unsupported_reason=str(exc),
        )
    except (ValidationError, TypeError, ValueError) as exc:
        return _error_result(exc, stage="query_spec_validation")
    except Exception as exc:  # noqa: BLE001 - external LLM failures are traced
        return _error_result(exc, stage="query_spec_parsing")

    try:
        backend = _get_backend(cfg)
        if cfg.financial_backend.strip().lower() == "finnhub":
            chunks = backend.search(  # type: ignore[union-attr]
                query,
                parsed_spec.tickers,
                top_k=top_k_chunks,
            )
            return FinancialQueryResult(
                chunks=chunks,
                trace={
                    "retriever": "financial",
                    "profile": "finnhub_legacy_v1",
                    "query_spec": parsed_spec.model_dump(mode="json"),
                    "returned_count": len(chunks),
                },
            ).model_dump(mode="json")

        result = backend.query(  # type: ignore[union-attr]
            parsed_spec,
            top_k=top_k_chunks,
        )
        return result.model_dump(mode="json")
    except Exception as exc:  # noqa: BLE001 - retrieval failures are traced
        return _error_result(exc, stage="backend_execution")


# ─────────────────────────────────────────────────────────────────────────────
# Smoke main — `python -m semigraph.online.financial_search`
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    demo_queries = [
        "Show NVDA annual revenue trend",
        "Compare AMD and NVDA gross margin",
        "What is NVDA current stock price?",
    ]

    for demo_number, demo_query in enumerate(demo_queries, start=1):
        print("\n" + "=" * 88)
        print(f"FINANCIAL SEARCH DEMO #{demo_number}")
        print("=" * 88)
        print(f"Query: {demo_query}")

        demo_result = financial_search(
            query=demo_query,
            top_k_chunks=6,
        )
        demo_trace = demo_result["trace"]
        demo_chunks = demo_result["chunks"]

        print("\nTRACE")
        print("-" * 88)
        print(
            json.dumps(
                demo_trace,
                ensure_ascii=False,
                indent=2,
                default=str,
            )
        )

        print(f"\nCHUNKS ({len(demo_chunks)} returned)")
        if not demo_chunks:
            print("-" * 88)
            print("No financial evidence was returned.")
            continue

        for rank, chunk in enumerate(demo_chunks, start=1):
            fiscal_year = chunk.get("fiscal_year") or "snapshot"
            value = chunk.get("value")
            unit = chunk.get("unit") or ""

            print("-" * 88)
            print(
                f"#{rank}  {chunk['ticker']} | {chunk.get('metric', 'n/a')} "
                f"| period={fiscal_year} | value={value} {unit}".rstrip()
            )
            print(f"chunk_id   : {chunk['chunk_id']}")
            print(f"section    : {chunk['section']}")
            print(f"period_end : {chunk.get('period_end') or 'n/a'}")
            print(
                f"source      : {chunk.get('source_kind', 'n/a')} "
                f"(status={chunk.get('status', 'n/a')})"
            )
            print(f"text        : {chunk['text']}")
            print("provenance  :")
            print(
                json.dumps(
                    chunk.get("provenance", {}),
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                )
            )
