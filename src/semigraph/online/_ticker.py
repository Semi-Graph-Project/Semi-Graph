"""Shared ticker resolution for online retrieval tools.

Extracted from `financial_search.py` so the financial and news tools can reuse
the same low-level extraction utility without duplicating regex/expansion code.

`CORPUS_TICKERS` is **derived from config** (`tickers:` in default.yaml), which
`scripts/pilot.py` keeps synced to Neo4j reality. Source-of-truth chain:
Neo4j DB → config/default.yaml → here. Never hard-code the ticker set again —
onboard via pilot.py and it flows through automatically.

Two-stage resolution:
  1. Regex match against CORPUS_TICKERS (~10 µs, $0) — hot path
  2. LLM query expansion via expand_query() then regex again (~1-2 s, ~$0.0005)
     — cold path when natural language / Thai needs entity → ticker mapping
"""
from __future__ import annotations

import re
from typing import Optional

from semigraph.config import Config, get_config
from semigraph.online.query_expand import expand_query


CORPUS_TICKERS: frozenset[str] = frozenset(
    t.upper() for t in get_config().tickers
)

TICKER_RE = re.compile(r"\b[A-Z]{2,5}\b")

# Uppercase domain terms that match TICKER_RE but are not stock symbols. This
# keeps queries such as "NVDA ROA in FY2025" from being rejected as containing
# an out-of-corpus ticker.
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

    Pure regex match — only catches uppercase ticker tokens already in the
    query. For natural-language company names ("Nvidia", "Ryzen maker",
    "ราคาหุ้น Qualcomm") use `resolve_tickers()` which adds an LLM expansion
    fallback.
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

    Stage 1 (always): reject explicit out-of-corpus symbols, then regex over the
    original query. ~10 µs, $0 — catches the hot path "What is NVDA revenue?"
    before any LLM cost. Rejecting first prevents an explicit AAPL query from
    being expanded into an unrelated in-corpus ticker.

    Stage 2 (only if Stage 1 returned empty AND `use_expansion`): call
    `expand_query()` which adds entity hints from LLM world knowledge
    (e.g. "Nvidia revenue" → "Nvidia revenue NVDA stock price quote"). Run
    regex again on the expanded string. Tokens are anti-hallucination-filtered
    against CORPUS_TICKERS so out-of-scope tickers can never reach a backend.
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
