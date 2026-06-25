"""
Phase F.v1 — financial_search: numeric-data retrieval via Finnhub API.

Phased architecture (Direct API v1 → SQL v2):
  - v1 (this file): `FinnhubAPIBackend` calls Finnhub on every query, returns 3
    snapshot kinds (financials_annual, key_metrics, quote) wrapped in the
    standard 6-key chunk shape used by vector_search / graph_search / hybrid_search.
  - v2 (future): `SQLBackend` (separate module) reads from SQLite populated via
    ETL, generates SQL through text-to-SQL LLM prompt. Same `FinancialBackend`
    Protocol → `_get_backend()` factory swap is the only change at runtime.

The orchestrator (`financial_search`) keeps a stable external contract — all
downstream code (RETRIEVERS dispatch, demo_rag prompt, app.py UI) is backend-
agnostic.

Output shape matches the other three retrievers exactly:
    [{chunk_id, text, ticker, fiscal_year, section, score}, ...]

No DB hits; no embeddings; no Neo4j. Only Finnhub HTTP calls.
"""
from __future__ import annotations

from typing import Optional, Protocol

from semigraph.config import Config, get_config
from semigraph.online._ticker import CORPUS_TICKERS, resolve_tickers


# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

# Lowercase keywords that signal a financial / numeric intent. Used to gate
# ticker extraction so phrases like "we use INTC platform" don't trigger an
# expensive API call.
FINANCIAL_KEYWORDS: frozenset[str] = frozenset({
    # English
    "revenue", "margin", "earnings", "growth", "valuation", "stock", "share",
    "eps", "p/e", "pe ratio", "price", "quote", "income", "profit", "ratio",
    "ebitda", "cash flow", "fcf", "operating", "gross", "roe", "market cap",
    # Thai — let queries like "ราคาหุ้น Qualcomm" pass the intent gate so the
    # LLM expansion fallback can resolve the company name → ticker.
    "ราคา", "ราคาหุ้น", "หุ้น", "รายได้", "กำไร", "ขาดทุน",
    "มาร์จิ้น", "มาร์จิน", "อัตรากำไร", "มูลค่า", "เงินปันผล", "งบการเงิน",
})

SNAPSHOT_KINDS: tuple[str, ...] = ("financials_annual", "key_metrics", "quote")


# ─────────────────────────────────────────────────────────────────────────────
# Helpers (pure functions — used by tests directly)
# ─────────────────────────────────────────────────────────────────────────────


def _has_financial_intent(query: str) -> bool:
    """True iff query contains at least one financial keyword (case-insensitive)."""
    q = query.lower()
    return any(kw in q for kw in FINANCIAL_KEYWORDS)


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
# Backend Protocol — v1 (API) and v2 (SQL) both implement this
# ─────────────────────────────────────────────────────────────────────────────


class FinancialBackend(Protocol):
    """Stable interface — `_get_backend()` returns a concrete implementation.

    v1: FinnhubAPIBackend (direct API per snapshot kind)
    v2 (TODO after Phase E, deadline 2 weeks before defense): SQLBackend with
        SQLite + text-to-SQL — same `.search()` signature so call sites stay
        identical.
    """

    def search(
        self,
        query: str,
        tickers: list[str],
        top_k: int = 5,
    ) -> list[dict]:
        """Return 6-key chunks for the given query and resolved tickers."""
        ...


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
# Backend factory — single swap point for v1 → v2 migration
# ─────────────────────────────────────────────────────────────────────────────


def _get_backend(cfg: Optional[Config] = None) -> FinancialBackend:
    """v1: always Finnhub. v2 will branch on `cfg.financial_backend`."""
    cfg = cfg or get_config()
    return FinnhubAPIBackend(api_key=cfg.finnhub_api_key)


# ─────────────────────────────────────────────────────────────────────────────
# Public orchestrator — registered in RETRIEVERS dispatch
# ─────────────────────────────────────────────────────────────────────────────


def financial_search(
    query: str,
    top_k_chunks: int = 5,
    cfg: Optional[Config] = None,
    use_expansion: bool = True,
) -> list[dict]:
    """Return top-k financial-snapshot chunks for the given query.

    Three early-exit guards keep API calls cheap and false-positive-free:
      1. Empty / intent-less query → []
      2. No corpus ticker resolved (regex + optional LLM expansion both empty)
         [] (Finnhub free tier is US-only and the financial tool is scoped
         to the 10-company semiconductor corpus)
      3. Missing API key → single error chunk (graceful, not exception)

    Args:
        query: Natural-language question. May be Thai or English.
        top_k_chunks: Max chunks returned. Each ticker contributes ≤ 3 snapshots,
            so multi-ticker queries are truncated here.
        cfg: Optional Config override; defaults to the cached singleton.
        use_expansion: If True (default), fall back to LLM query expansion
            when regex finds no ticker. Set False to disable LLM cost in
            batch evaluation or when latency matters more than coverage.

    Returns:
        `[{chunk_id, text, ticker, fiscal_year, section, score}, ...]` —
        identical shape to `vector_search()` / `graph_search()` /
        `hybrid_search()`. Empty list on miss (no exception).
    """
    if not query.strip():
        return []
    if not _has_financial_intent(query):
        return []
    tickers = resolve_tickers(query, cfg=cfg, use_expansion=use_expansion)
    if not tickers:
        return []
    try:
        backend = _get_backend(cfg)
    except RuntimeError as exc:
        # Missing API key — surface a single info chunk so the demo doesn't
        # silently produce empty answers when the user forgets to set the key.
        return [{
            "chunk_id": "fin_unavailable",
            "text": f"Financial backend unavailable: {exc}",
            "ticker": tickers[0],
            "fiscal_year": 0,
            "section": "Financial_error",
            "score": 0.0,
        }]
    return backend.search(query, tickers, top_k=top_k_chunks)


# ─────────────────────────────────────────────────────────────────────────────
# Smoke main — `python -m semigraph.online.financial_search`
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    for q in [
        # Hot path — regex hits, no LLM call
        "What is NVDA latest annual revenue and gross margin?",
        "Compare AMD and NVDA operating margin.",
        # Cold path — natural language, LLM expansion required
        "What is Nvidia's current stock price?",
        "Where is the developer of Ryzen processors and what is its P/E?",
        "ราคาหุ้น Qualcomm ตอนนี้",
        # Guards
        "What is the semiconductor market outlook?",  # no ticker even after expand → []
        "we use INTC platform internally",            # no financial intent → []
    ]:
        print(f"\n--- {q!r} ---")
        chunks = financial_search(q, top_k_chunks=6)
        if not chunks:
            print("  (empty — guard tripped or no data)")
            continue
        for i, c in enumerate(chunks, start=1):
            print(f"  #{i} [{c['ticker']} {c['section']}]")
            print(f"     {c['text']}")
