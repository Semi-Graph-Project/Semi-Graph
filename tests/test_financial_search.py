"""Unit tests for Phase F.v1 financial_search.

Focus: orchestrator pure-function logic + Protocol contract. Backend API calls
are mocked — real Finnhub hits live in integration scripts, not unit tests.
"""
from __future__ import annotations

import pytest

from semigraph.online._ticker import CORPUS_TICKERS, extract_tickers, resolve_tickers
from semigraph.online.financial_search import (
    FINANCIAL_KEYWORDS,
    SNAPSHOT_KINDS,
    FinancialBackend,
    _has_financial_intent,
    _make_chunk,
    financial_search,
)


# ─────────────────────────────────────────────────────────────────────────────
# Ticker extraction
# ─────────────────────────────────────────────────────────────────────────────


class TestExtractTickers:
    def test_single_ticker(self):
        assert extract_tickers("What is NVDA revenue?") == ["NVDA"]

    def test_two_tickers_in_order(self):
        assert extract_tickers("Compare AMD and NVDA") == ["AMD", "NVDA"]

    def test_dedup_preserves_first_seen_order(self):
        assert extract_tickers("NVDA vs AMD vs NVDA again") == ["NVDA", "AMD"]

    def test_no_ticker_returns_empty(self):
        assert extract_tickers("What is the market doing?") == []

    def test_ignores_unknown_uppercase_tokens(self):
        # "USA" / "GAAP" / "PDF" are uppercase but not in corpus
        assert extract_tickers("USA GAAP PDF report") == []

    def test_lowercase_tickers_ignored(self):
        # ticker regex is uppercase-only — Finnhub expects uppercase symbols
        assert extract_tickers("what is nvda doing") == []

    def test_all_ten_corpus_tickers_detected(self):
        q = " ".join(sorted(CORPUS_TICKERS))
        out = extract_tickers(q)
        assert set(out) == CORPUS_TICKERS


# ─────────────────────────────────────────────────────────────────────────────
# Intent guard
# ─────────────────────────────────────────────────────────────────────────────


class TestHasFinancialIntent:
    @pytest.mark.parametrize("q", [
        "NVDA revenue",
        "What is the gross margin?",
        "Compare earnings",
        "stock price today",
        "operating income trend",
        "ROE comparison",
    ])
    def test_keyword_present(self, q: str):
        assert _has_financial_intent(q)

    @pytest.mark.parametrize("q", [
        "we use INTC platform",
        "TSMC supply chain risk",
        "What is AMD's CEO name?",
        "Describe NVIDIA business segments",
    ])
    def test_no_keyword(self, q: str):
        assert not _has_financial_intent(q)

    def test_case_insensitive(self):
        assert _has_financial_intent("REVENUE growth")
        assert _has_financial_intent("Revenue Growth")


# ─────────────────────────────────────────────────────────────────────────────
# Chunk shape contract
# ─────────────────────────────────────────────────────────────────────────────


class TestMakeChunk:
    def test_has_six_keys_exactly(self):
        c = _make_chunk("NVDA", "financials_annual", "text here", 2025)
        assert set(c.keys()) == {
            "chunk_id", "text", "ticker", "fiscal_year", "section", "score"
        }

    def test_chunk_id_deterministic(self):
        c1 = _make_chunk("AMD", "key_metrics", "x", 0)
        c2 = _make_chunk("AMD", "key_metrics", "different text", 0)
        assert c1["chunk_id"] == c2["chunk_id"] == "fin_AMD_key_metrics_0"

    def test_section_prefix_distinguishes_from_10k(self):
        c = _make_chunk("NVDA", "quote", "x", 0)
        # 10-K chunks use "Item_1" / "Item_1A" / "Item_7"; Financial uses Financial_*
        assert c["section"].startswith("Financial_")

    def test_fiscal_year_int(self):
        c = _make_chunk("INTC", "financials_annual", "x", 2024)
        assert isinstance(c["fiscal_year"], int)

    def test_score_one_point_zero(self):
        c = _make_chunk("AVGO", "quote", "x", 0)
        assert c["score"] == 1.0


# ─────────────────────────────────────────────────────────────────────────────
# Ticker resolution — regex + LLM expansion fallback
# ─────────────────────────────────────────────────────────────────────────────


class TestResolveTickers:
    """`resolve_tickers` is the orchestrator's ticker entry point.

    Stage 1 (regex) should hit on hot-path queries. Stage 2 (LLM expansion)
    should fire only when regex is empty AND use_expansion is True.
    """

    def test_regex_hit_skips_expansion(self, monkeypatch):
        """When regex finds a ticker, expand_query MUST NOT be called."""
        called = {"flag": False}

        def fake_expand(q, cfg=None):
            called["flag"] = True
            return q

        monkeypatch.setattr(
            "semigraph.online._ticker.expand_query",
            fake_expand,
        )
        tickers = resolve_tickers("What is NVDA revenue?")
        assert tickers == ["NVDA"]
        assert called["flag"] is False  # hot path → no LLM call

    def test_regex_miss_triggers_expansion(self, monkeypatch):
        """When regex is empty, expand_query is called and result re-scanned."""
        def fake_expand(q, cfg=None):
            # Simulate LLM emitting ticker hint
            return f"{q} NVDA NVIDIA stock price"

        monkeypatch.setattr(
            "semigraph.online._ticker.expand_query",
            fake_expand,
        )
        tickers = resolve_tickers("What is Nvidia's current stock price?")
        assert tickers == ["NVDA"]

    def test_use_expansion_false_skips_llm(self, monkeypatch):
        """use_expansion=False → never call expand_query even on regex miss."""
        called = {"flag": False}

        def fake_expand(q, cfg=None):
            called["flag"] = True
            return f"{q} NVDA"

        monkeypatch.setattr(
            "semigraph.online._ticker.expand_query",
            fake_expand,
        )
        tickers = resolve_tickers("Nvidia revenue", use_expansion=False)
        assert tickers == []
        assert called["flag"] is False

    def test_expansion_fails_returns_empty(self, monkeypatch):
        """If expand_query returns the original query (LLM failed), result is []."""
        def fake_expand(q, cfg=None):
            return q  # expand_query() fallback behaviour

        monkeypatch.setattr(
            "semigraph.online._ticker.expand_query",
            fake_expand,
        )
        tickers = resolve_tickers("Nvidia stock price")
        assert tickers == []

    def test_expanded_hints_filtered_through_corpus(self, monkeypatch):
        """LLM may hallucinate non-corpus tickers — they must NOT leak."""
        def fake_expand(q, cfg=None):
            # LLM hallucinates AAPL (not in our corpus) alongside the real one
            return f"{q} AAPL NVDA TSLA"

        monkeypatch.setattr(
            "semigraph.online._ticker.expand_query",
            fake_expand,
        )
        tickers = resolve_tickers("Nvidia P/E")
        assert tickers == ["NVDA"]  # only corpus tickers survive


# ─────────────────────────────────────────────────────────────────────────────
# Orchestrator behaviour (mocked backend)
# ─────────────────────────────────────────────────────────────────────────────


class FakeBackend:
    """Concrete `FinancialBackend` for unit tests — no Finnhub dependency."""

    def __init__(self, chunks_per_ticker: int = 3):
        self.chunks_per_ticker = chunks_per_ticker
        self.calls: list[tuple[str, tuple[str, ...]]] = []

    def search(self, query: str, tickers: list[str], top_k: int = 5) -> list[dict]:
        self.calls.append((query, tuple(tickers)))
        out: list[dict] = []
        for t in tickers:
            for kind in SNAPSHOT_KINDS[: self.chunks_per_ticker]:
                out.append(_make_chunk(t, kind, f"{t} {kind} fake", 2025))
        return out[:top_k]


@pytest.fixture
def patch_backend(monkeypatch):
    """Replace `_get_backend` with a FakeBackend so tests never call Finnhub."""
    fake = FakeBackend()
    monkeypatch.setattr(
        "semigraph.online.financial_search._get_backend",
        lambda cfg=None: fake,
    )
    return fake


class TestOrchestrator:
    def test_empty_query_returns_empty(self):
        assert financial_search("") == []
        assert financial_search("   ") == []

    def test_no_financial_intent_returns_empty(self, patch_backend):
        # Has ticker but no keyword → backend never invoked
        assert financial_search("we use INTC for our research") == []
        assert patch_backend.calls == []

    def test_no_ticker_returns_empty(self, patch_backend, monkeypatch):
        # Has keyword but no corpus ticker → expand fails → backend never invoked
        # Patch expand_query to return original (simulating LLM finding nothing relevant)
        monkeypatch.setattr(
            "semigraph.online._ticker.expand_query",
            lambda q, cfg=None: q,
        )
        assert financial_search("What is the market revenue trend?") == []
        assert patch_backend.calls == []

    def test_natural_language_ticker_via_expansion(self, patch_backend, monkeypatch):
        """End-to-end: "Nvidia revenue" → LLM expand → backend.search(["NVDA"])."""
        monkeypatch.setattr(
            "semigraph.online._ticker.expand_query",
            lambda q, cfg=None: f"{q} NVDA",
        )
        out = financial_search("What is Nvidia's revenue?", top_k_chunks=5)
        assert len(patch_backend.calls) == 1
        assert patch_backend.calls[0][1] == ("NVDA",)
        assert len(out) == 3

    def test_use_expansion_false_blocks_natural_language(self, patch_backend, monkeypatch):
        """use_expansion=False should NOT call expand_query at all."""
        called = {"flag": False}

        def fake_expand(q, cfg=None):
            called["flag"] = True
            return f"{q} NVDA"

        monkeypatch.setattr(
            "semigraph.online._ticker.expand_query",
            fake_expand,
        )
        out = financial_search("Nvidia revenue", use_expansion=False)
        assert out == []
        assert called["flag"] is False

    def test_single_ticker_dispatches_backend(self, patch_backend):
        out = financial_search("What is NVDA latest revenue?", top_k_chunks=5)
        assert len(patch_backend.calls) == 1
        assert patch_backend.calls[0][1] == ("NVDA",)
        assert len(out) == 3  # 3 snapshot kinds

    def test_multi_ticker_passes_all(self, patch_backend):
        out = financial_search("Compare AMD and NVDA gross margin", top_k_chunks=10)
        assert patch_backend.calls[0][1] == ("AMD", "NVDA")
        assert len(out) == 6  # 2 tickers × 3 kinds

    def test_top_k_truncation_applied(self, patch_backend):
        out = financial_search("Compare AMD and NVDA revenue", top_k_chunks=4)
        # Backend returns 6, orchestrator should truncate to 4
        assert len(out) == 4

    def test_six_key_shape_enforced(self, patch_backend):
        out = financial_search("NVDA revenue", top_k_chunks=5)
        required = {"chunk_id", "text", "ticker", "fiscal_year", "section", "score"}
        for c in out:
            assert set(c.keys()) == required


# ─────────────────────────────────────────────────────────────────────────────
# Protocol contract — structural typing sanity
# ─────────────────────────────────────────────────────────────────────────────


class TestProtocolContract:
    def test_fake_backend_satisfies_protocol(self):
        # typing.Protocol is structural — FakeBackend has `.search()` so the
        # isinstance check via runtime_checkable would pass. We assert by
        # assignment instead (runtime-checkable Protocol not required for v1).
        backend: FinancialBackend = FakeBackend()
        result = backend.search("q", ["NVDA"], top_k=5)
        assert isinstance(result, list)

    def test_finnhub_backend_has_search_method(self):
        # Don't instantiate (needs real API key) — just verify class shape
        from semigraph.online.financial_search import FinnhubAPIBackend
        assert hasattr(FinnhubAPIBackend, "search")
        assert callable(FinnhubAPIBackend.search)


# ─────────────────────────────────────────────────────────────────────────────
# Constants sanity (catches accidental shrinkage of corpus)
# ─────────────────────────────────────────────────────────────────────────────


def test_corpus_has_ten_tickers():
    assert len(CORPUS_TICKERS) == 10


def test_snapshot_kinds_are_three():
    assert len(SNAPSHOT_KINDS) == 3
    assert SNAPSHOT_KINDS == ("financials_annual", "key_metrics", "quote")


def test_financial_keywords_include_core_terms():
    for kw in ("revenue", "margin", "earnings", "p/e", "price", "ebitda"):
        assert kw in FINANCIAL_KEYWORDS
