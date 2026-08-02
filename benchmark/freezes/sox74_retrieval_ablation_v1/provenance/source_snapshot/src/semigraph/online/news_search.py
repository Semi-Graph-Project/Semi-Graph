"""
Phase E.v1 — news_search: real-time company news retrieval via Finnhub News API.

Mirrors Phase F.v1 architecture (Protocol pattern, 4 guards, 6-key chunks)
so news_search is a drop-in 5th retriever alongside vector/graph/hybrid/financial.

Default behaviour: real-time API call per query (no cache, no scraping) — matches
Proposal §5.1.4 "real-time, no cache". Two opt-in extensions:

  - `use_cache=True`  -> file-based JSON cache under `data/news/cache/`. Needed
                        for eval batch (555 queries hit 60/min rate limit).
  - `depth="full"`    -> fetch full article body via newspaper3k. Slow (~5 sec
                        per article) + can fail on paywalled / JS-rendered
                        pages → graceful fallback to headline+summary.

Output shape matches the other four retrievers exactly:
    [{chunk_id, text, ticker, fiscal_year, section, score}, ...]

`section` prefix is always "News_finnhub" so demo_rag SYSTEM_PROMPT and app.py
can attribute the source distinctly from 10-K (Item_*) and Financial_* chunks.
"""
from __future__ import annotations

import json
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Literal, Optional, Protocol

from semigraph.config import Config, get_config
from semigraph.online._ticker import resolve_tickers


# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

# Lowercase tokens that signal real-time / news intent. Used to gate ticker
# extraction so a 10-K narrative query like "NVDA suppliers" doesn't trigger
# a wasted Finnhub call.
NEWS_KEYWORDS: frozenset[str] = frozenset({
    # English
    "news", "latest", "recent", "today", "yesterday", "week", "headline",
    "headlines", "update", "report", "announced", "announcement", "event",
    "earnings call", "press release",
    # Thai
    "ข่าว", "ล่าสุด", "เพิ่งเกิด", "วันนี้", "เมื่อวาน", "สัปดาห์",
    "ประกาศ", "รายงาน", "อัพเดท", "อัปเดต",
})

DEFAULT_DAYS_BACK = 90
SECTION_PREFIX = "News_finnhub"


# ─────────────────────────────────────────────────────────────────────────────
# Helpers (pure functions — used by tests directly)
# ─────────────────────────────────────────────────────────────────────────────


def _has_news_intent(query: str) -> bool:
    """True iff query contains at least one news / real-time keyword."""
    q = query.lower()
    return any(kw in q for kw in NEWS_KEYWORDS)


def _recency_score(article_ts: int, now_ts: int, days_back: int) -> float:
    """Linear decay: today → 1.0, oldest (days_back ago) → 0.1. Clamped.

    Article timestamps in the future (Finnhub revision bug seen on quote
    fields) clamp to 1.0 instead of producing negative ages.
    """
    if days_back <= 0:
        return 1.0
    age_days = (now_ts - article_ts) / 86400.0
    if age_days < 0:
        return 1.0
    if age_days > days_back:
        return 0.1
    return 1.0 - 0.9 * (age_days / days_back)


def _make_chunk(
    article: dict,
    ticker: str,
    text: str,
    days_back: int,
    now_ts: Optional[int] = None,
) -> dict:
    """Wrap an article into the 6-key contract shared across all retrievers.

    `now_ts` is injectable so tests can produce deterministic recency scores
    without mocking `time.time()` globally.
    """
    article_id = article.get("id") or abs(hash(article.get("url", "")))
    article_ts = int(article.get("datetime") or 0)
    article_year = datetime.fromtimestamp(article_ts).year if article_ts else 0
    score = _recency_score(article_ts, now_ts or int(time.time()), days_back)
    return {
        "chunk_id": f"news_{ticker}_{article_id}",
        "text": text,
        "ticker": ticker,
        "fiscal_year": article_year,
        "section": SECTION_PREFIX,
        "score": round(score, 3),
        "datetime": datetime.fromtimestamp(article_ts).isoformat() if article_ts else None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Backend Protocol — v1 (Finnhub API) and any future backend implement this
# ─────────────────────────────────────────────────────────────────────────────


class NewsBackend(Protocol):
    """Stable interface — `_get_backend()` returns a concrete implementation."""

    def search(
        self,
        query: str,
        tickers: list[str],
        top_k: int = 5,
        days_back: int = DEFAULT_DAYS_BACK,
        depth: Literal["headline", "full"] = "headline",
        use_cache: bool = False,
    ) -> list[dict]:
        """Return 6-key chunks for the given query and resolved tickers."""
        ...


class FinnhubNewsBackend:
    """v1 backend: Finnhub `company_news` per ticker.

    Date window: caller-supplied `days_back` from today back. Finnhub returns
    up to ~100 articles per ticker per call. Per-ticker fetch is isolated in
    try/except so one ticker's failure never poisons the rest of the result.
    """

    def __init__(self, api_key: str, cache_dir: Path):
        if not api_key:
            raise RuntimeError(
                "FINNHUB_API_KEY is empty — set it in .env (sign up free at "
                "https://finnhub.io/dashboard)"
            )
        # Late import: keep package importable when finnhub-python isn't installed
        import finnhub
        self.client = finnhub.Client(api_key=api_key)
        self.cache_dir = cache_dir

    # -- public API expected by the Protocol ---------------------------------

    def search(
        self,
        query: str,
        tickers: list[str],
        top_k: int = 5,
        days_back: int = DEFAULT_DAYS_BACK,
        depth: Literal["headline", "full"] = "headline",
        use_cache: bool = False,
    ) -> list[dict]:
        from_date = (date.today() - timedelta(days=days_back)).isoformat()
        to_date = date.today().isoformat()
        now_ts = int(time.time())

        chunks: list[dict] = []
        for ticker in tickers:
            articles = self._fetch(ticker, from_date, to_date, use_cache)
            for art in articles:
                text = self._format_text(art, depth)
                chunks.append(_make_chunk(art, ticker, text, days_back, now_ts))

        # Recency-weighted ranking — newest article in result rises to the top
        chunks.sort(key=lambda c: c["score"], reverse=True)
        return chunks[:top_k]

    # -- fetch (with optional cache) -----------------------------------------

    def _fetch(
        self,
        ticker: str,
        from_date: str,
        to_date: str,
        use_cache: bool,
    ) -> list[dict]:
        if use_cache:
            cached = self._cache_get(ticker, from_date, to_date)
            if cached is not None:
                return cached
        try:
            articles = self.client.company_news(ticker, _from=from_date, to=to_date)
        except Exception as exc: 
            print(f"[news_search] {ticker} fetch failed: {exc}")
            return []
        if use_cache:
            self._cache_put(ticker, from_date, to_date, articles or [])
        return articles or []

    # -- two-tier content formatter ------------------------------------------

    def _format_text(self, article: dict, depth: str) -> str:
        """Compose chunk text from article. depth controls headline vs full body.

        - "headline" (default): "{headline}: {summary}" — ~200-500 chars. Fast.
        - "full": scrape `url` via newspaper3k → "{headline}\\n\\n{body[:3000]}".
          Slow + can fail (paywall, JS, 404). On any exception → graceful
          fallback to the headline form so the chunk is never empty.
        """
        headline = (article.get("headline") or "").strip()
        summary = (article.get("summary") or "").strip()
        base = f"{headline}: {summary}" if summary else headline

        if depth == "headline":
            return base

        url = article.get("url")
        if not url:
            return base
        try:
            from newspaper import Article  # late import — newspaper3k is heavy
            a = Article(url)
            a.download()
            a.parse()
            body = (a.text or "").strip()[:3000]
            if not body:
                return base
            return f"{headline}\n\n{body}"
        except Exception as exc:  # noqa: BLE001
            print(f"[news_search] full-content fetch failed for {url}: {exc}")
            return base

    # -- file-based cache (default OFF; opt-in via use_cache=True) -----------

    def _cache_path(self, ticker: str, from_date: str, to_date: str) -> Path:
        fname = f"{ticker}_{from_date.replace('-', '')}_{to_date.replace('-', '')}.json"
        return self.cache_dir / fname

    def _cache_get(
        self, ticker: str, from_date: str, to_date: str
    ) -> Optional[list]:
        p = self._cache_path(ticker, from_date, to_date)
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text())
        except Exception as exc:  # noqa: BLE001
            print(f"[news_search] cache read failed for {p.name}: {exc}")
            return None

    def _cache_put(
        self, ticker: str, from_date: str, to_date: str, articles: list
    ) -> None:
        p = self._cache_path(ticker, from_date, to_date)
        p.parent.mkdir(parents=True, exist_ok=True)
        try:
            p.write_text(json.dumps(articles))
        except Exception as exc:  # noqa: BLE001
            print(f"[news_search] cache write failed for {p.name}: {exc}")


# ─────────────────────────────────────────────────────────────────────────────
# Backend factory — single swap point for any future backend
# ─────────────────────────────────────────────────────────────────────────────


def _get_backend(cfg: Optional[Config] = None) -> NewsBackend:
    cfg = cfg or get_config()
    return FinnhubNewsBackend(
        api_key=cfg.finnhub_api_key,
        cache_dir=cfg.news_cache_dir,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Public orchestrator — registered in RETRIEVERS dispatch
# ─────────────────────────────────────────────────────────────────────────────


def news_search(
    query: str,
    top_k_chunks: int = 5,
    cfg: Optional[Config] = None,
    days_back: Optional[int] = None,
    depth: Literal["headline", "full"] = "headline",
    use_cache: bool = False,
    use_expansion: bool = True,
) -> list[dict]:
    """Return top-k news chunks for a query about corpus tickers.

    Four early-exit guards layered by cost (cheapest first):
      1. Empty query                          → []
      2. No news / real-time keyword          → [] (10-K narrative query — skip)
      3. No corpus ticker (regex + LLM)       → [] (out-of-scope ticker)
      4. Missing API key                      → single error chunk (graceful)

    Args:
        query: Natural-language question. Thai or English supported.
        top_k_chunks: Max chunks returned. Multi-ticker queries are truncated
            here after recency-weighted ranking across all tickers.
        cfg: Optional Config override; defaults to cached singleton.
        days_back: Override the default date window (Config.news_days_back).
        depth: "headline" (fast, default) or "full" (slow scrape via newspaper3k).
        use_cache: Read/write file-based JSON cache. Default OFF (proposal-true);
            set True for eval batches that hit the 60/min rate limit.
        use_expansion: Fall back to LLM query expansion when regex finds no
            ticker. Set False to disable LLM cost in batch eval.

    Returns:
        `[{chunk_id, text, ticker, fiscal_year, section, score}, ...]` —
        identical 6-key shape to vector_search / graph_search / hybrid_search /
        financial_search. Empty list on miss (no exception).
    """
    if not query.strip():
        return []
    if not _has_news_intent(query):
        return []
    tickers = resolve_tickers(query, cfg=cfg, use_expansion=use_expansion)
    if not tickers:
        return []
    cfg = cfg or get_config()
    try:
        backend = _get_backend(cfg)
    except RuntimeError as exc:
        # Missing API key — surface a single info chunk so the demo doesn't
        # silently produce empty answers when the user forgets to set the key.
        return [{
            "chunk_id": "news_unavailable",
            "text": f"News backend unavailable: {exc}",
            "ticker": tickers[0],
            "fiscal_year": 0,
            "section": "News_error",
            "score": 0.0,
        }]
    return backend.search(
        query,
        tickers,
        top_k=top_k_chunks,
        days_back=days_back if days_back is not None else cfg.news_days_back,
        depth=depth,
        use_cache=use_cache,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Smoke main — `python -m semigraph.online.news_search`
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    for q in [
        # Hot path — regex hits, no LLM call
        "NVDA news latest",
        "AMD recent earnings call",
        # Cold path — natural language, LLM expansion required
        "What is Nvidia's latest news today?",
        "ข่าวล่าสุด AMD",
        # Guards
        "What is the semiconductor market outlook?",  # no ticker → []
        "NVDA suppliers",                              # no news intent → []
    ]:
        print(f"\n--- {q!r} ---")
        chunks = news_search(q, top_k_chunks=3)
        if not chunks:
            print("  (empty — guard tripped or no data)")
            continue
        for i, c in enumerate(chunks, start=1):
            print(f"  #{i} [{c['ticker']} score={c['score']} datetime={c['datetime']}]")
            print(f"     {c['text'][:120]}")
