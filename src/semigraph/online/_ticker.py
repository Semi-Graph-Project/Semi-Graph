from __future__ import annotations

import re
from typing import Optional

from semigraph.config import Config, get_config
from semigraph.online.query_expand import expand_query


CORPUS_TICKERS: frozenset[str] = frozenset(
    t.upper() for t in get_config().tickers
)

TICKER_RE = re.compile(r"\b[A-Z]{2,5}\b")

NON_TICKER_TOKENS: frozenset[str] = frozenset({
    "AI", "API", "CAGR", "CEO", "CFO", "EPS", "ETF", "FCF", "FY",
    "GAAP", "GPU", "HBM", "IFRS", "LLM", "PDF", "PE", "PPR", "QA",
    "RAG", "RAM", "ROA", "ROE", "SEC", "SQL", "TTM", "USA", "USD",
    "YTD", "YOY",
})


def _out_of_corpus_tickers(query: str) -> list[str]:
    """Return explicit ticker-like tokens that are outside this corpus."""

    seen: dict[str, None] = {}
    for token in TICKER_RE.findall(query):
        if token not in CORPUS_TICKERS and token not in NON_TICKER_TOKENS:
            seen.setdefault(token, None)
    return list(seen)


def extract_tickers(query: str) -> list[str]:
    """Return corpus tickers mentioned in query, preserving first-seen order.

    """
    seen: dict[str, None] = {}
    for tok in TICKER_RE.findall(query):
        if tok in CORPUS_TICKERS:
            seen.setdefault(tok, None)
    return list(seen.keys())


def resolve_tickers(
    query: str,
    cfg: Optional[Config] = None,
    use_expansion: bool = True,
) -> list[str]:
    """Two-stage ticker resolution: regex first, LLM expansion as fallback.
     """
    if _out_of_corpus_tickers(query):
        return []

    tickers = extract_tickers(query)
    if tickers or not use_expansion:
        return tickers
    expanded = expand_query(query, cfg=cfg)
    if expanded == query:
        # expand_query() failed or LLM hint shape was invalid — already logged
        return []
    return extract_tickers(expanded)
