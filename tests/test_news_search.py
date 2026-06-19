"""Unit tests for Phase E.v1 news_search.

Focus: orchestrator pure-function logic + Protocol contract + cache + recency
score. Real Finnhub HTTP and newspaper3k scrapes are mocked — live integration
tests live in `python -m semigraph.online.news_search` smoke (not pytest).
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from semigraph.online._ticker import CORPUS_TICKERS
from semigraph.online.news_search import (
    DEFAULT_DAYS_BACK,
    NEWS_KEYWORDS,
    SECTION_PREFIX,
    FinnhubNewsBackend,
    NewsBackend,
    _has_news_intent,
    _make_chunk,
    _recency_score,
    news_search,
)


# ─────────────────────────────────────────────────────────────────────────────
# Intent gate
# ─────────────────────────────────────────────────────────────────────────────


class TestNewsIntent:
    @pytest.mark.parametrize("q", [
        "latest news on NVDA",
        "What is the recent announcement?",
        "AMD earnings call today",
        "headlines this week",
        "any update on Intel?",
    ])
    def test_keyword_present_english(self, q):
        assert _has_news_intent(q)

    @pytest.mark.parametrize("q", [
        "ข่าวล่าสุดของ NVDA",
        "AMD เพิ่งประกาศอะไร",
        "อัปเดต Intel วันนี้",
        "รายงานสัปดาห์นี้",
    ])
    def test_keyword_present_thai(self, q):
        assert _has_news_intent(q)

    @pytest.mark.parametrize("q", [
        "NVDA suppliers list",
        "AMD CEO name",
        "Intel manufacturing locations",
        "TSMC fab capacity",
    ])
    def test_no_keyword(self, q):
        assert not _has_news_intent(q)

    def test_case_insensitive(self):
        assert _has_news_intent("LATEST NEWS")
        assert _has_news_intent("Latest News")


# ─────────────────────────────────────────────────────────────────────────────
# Recency score
# ─────────────────────────────────────────────────────────────────────────────


class TestRecencyScore:
    def test_today_is_one(self):
        now = 1_700_000_000
        assert _recency_score(now, now, 90) == 1.0

    def test_oldest_is_decayed(self):
        now = 1_700_000_000
        ts = now - 90 * 86400
        score = _recency_score(ts, now, 90)
        assert score == pytest.approx(0.1)

    def test_mid_window_linear(self):
        now = 1_700_000_000
        ts = now - 45 * 86400
        # 45 / 90 = 0.5 → 1.0 - 0.9*0.5 = 0.55
        assert _recency_score(ts, now, 90) == pytest.approx(0.55)

    def test_beyond_window_clamps_to_floor(self):
        now = 1_700_000_000
        ts = now - 365 * 86400
        assert _recency_score(ts, now, 90) == pytest.approx(0.1)

    def test_future_date_clamps_to_one(self):
        """Finnhub revision bug: article ts > now should not produce negative ages."""
        now = 1_700_000_000
        ts = now + 86400
        assert _recency_score(ts, now, 90) == 1.0

    def test_zero_days_back_returns_one(self):
        """Defensive: days_back=0 should not divide by zero."""
        now = 1_700_000_000
        assert _recency_score(now, now, 0) == 1.0


# ─────────────────────────────────────────────────────────────────────────────
# Chunk shape
# ─────────────────────────────────────────────────────────────────────────────


class TestNewsChunkShape:
    @pytest.fixture
    def article(self):
        return {
            "id": 99999,
            "datetime": 1_700_000_000,
            "headline": "NVDA hits new high",
            "summary": "Stock surged 5% on AI demand.",
            "url": "https://example.com/n/1",
            "source": "Reuters",
        }

    def test_six_keys_exact(self, article):
        c = _make_chunk(article, "NVDA", "text", 90, now_ts=1_700_000_000)
        assert set(c.keys()) == {"chunk_id", "text", "ticker", "fiscal_year", "section", "score"}

    def test_chunk_id_format(self, article):
        c = _make_chunk(article, "NVDA", "x", 90, now_ts=1_700_000_000)
        assert c["chunk_id"] == "news_NVDA_99999"

    def test_chunk_id_fallback_to_url_hash(self):
        a = {"datetime": 1_700_000_000, "headline": "h", "url": "https://x"}
        c = _make_chunk(a, "AMD", "t", 90, now_ts=1_700_000_000)
        assert c["chunk_id"].startswith("news_AMD_")
        assert c["chunk_id"] != "news_AMD_0"  # didn't fall back to 0

    def test_section_prefix_distinguishes_from_other_sources(self, article):
        c = _make_chunk(article, "NVDA", "x", 90, now_ts=1_700_000_000)
        assert c["section"] == SECTION_PREFIX
        assert c["section"].startswith("News_")  # not Item_ or Financial_

    def test_fiscal_year_from_article_datetime(self, article):
        c = _make_chunk(article, "NVDA", "x", 90, now_ts=1_700_000_000)
        # 1_700_000_000 = Nov 14 2023
        assert c["fiscal_year"] == 2023

    def test_fiscal_year_zero_when_no_timestamp(self):
        a = {"id": 1, "datetime": 0, "headline": "h", "summary": "s"}
        c = _make_chunk(a, "NVDA", "x", 90, now_ts=1_700_000_000)
        assert c["fiscal_year"] == 0

    def test_score_in_range(self, article):
        c = _make_chunk(article, "NVDA", "x", 90, now_ts=1_700_000_000)
        assert 0.1 <= c["score"] <= 1.0


# ─────────────────────────────────────────────────────────────────────────────
# Cache hit / miss
# ─────────────────────────────────────────────────────────────────────────────


class _StubFinnhubClient:
    def __init__(self, articles_by_ticker):
        self._articles = articles_by_ticker
        self.calls = []

    def company_news(self, ticker, _from=None, to=None):
        self.calls.append((ticker, _from, to))
        return self._articles.get(ticker, [])


def _make_backend_with_stub(tmp_path: Path, articles_by_ticker=None, monkeypatch=None):
    backend = FinnhubNewsBackend.__new__(FinnhubNewsBackend)
    backend.client = _StubFinnhubClient(articles_by_ticker or {})
    backend.cache_dir = tmp_path / "cache"
    return backend


class TestCacheHitMiss:
    def test_cache_miss_returns_none(self, tmp_path):
        b = _make_backend_with_stub(tmp_path)
        assert b._cache_get("NVDA", "2024-01-01", "2024-01-31") is None

    def test_cache_roundtrip(self, tmp_path):
        b = _make_backend_with_stub(tmp_path)
        articles = [{"id": 1, "headline": "h"}]
        b._cache_put("NVDA", "2024-01-01", "2024-01-31", articles)
        out = b._cache_get("NVDA", "2024-01-01", "2024-01-31")
        assert out == articles

    def test_corrupt_cache_returns_none(self, tmp_path):
        b = _make_backend_with_stub(tmp_path)
        p = b._cache_path("NVDA", "2024-01-01", "2024-01-31")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("not valid json {{{")
        assert b._cache_get("NVDA", "2024-01-01", "2024-01-31") is None

    def test_use_cache_true_skips_second_api_call(self, tmp_path):
        articles = [{"id": 1, "datetime": 1_700_000_000, "headline": "h", "summary": "s"}]
        b = _make_backend_with_stub(tmp_path, {"NVDA": articles})

        out1 = b.search("q", ["NVDA"], top_k=5, use_cache=True)
        out2 = b.search("q", ["NVDA"], top_k=5, use_cache=True)

        assert len(out1) == 1 and len(out2) == 1
        # Two searches but client called only once because second hit cache
        assert len(b.client.calls) == 1

    def test_use_cache_false_always_calls_api(self, tmp_path):
        articles = [{"id": 1, "datetime": 1_700_000_000, "headline": "h", "summary": "s"}]
        b = _make_backend_with_stub(tmp_path, {"NVDA": articles})

        b.search("q", ["NVDA"], top_k=5, use_cache=False)
        b.search("q", ["NVDA"], top_k=5, use_cache=False)

        assert len(b.client.calls) == 2


# ─────────────────────────────────────────────────────────────────────────────
# Two-tier content depth
# ─────────────────────────────────────────────────────────────────────────────


class TestTwoTierContent:
    @pytest.fixture
    def article(self):
        return {
            "headline": "Headline text",
            "summary": "Short summary.",
            "url": "https://example.com/n/1",
        }

    def test_headline_uses_summary(self, tmp_path, article):
        b = _make_backend_with_stub(tmp_path)
        text = b._format_text(article, "headline")
        assert "Headline text" in text
        assert "Short summary." in text

    def test_headline_no_summary_returns_headline_only(self, tmp_path):
        b = _make_backend_with_stub(tmp_path)
        text = b._format_text({"headline": "Only headline", "summary": ""}, "headline")
        assert text == "Only headline"

    def test_full_uses_newspaper(self, tmp_path, article, monkeypatch):
        b = _make_backend_with_stub(tmp_path)

        class FakeNewspaperArticle:
            def __init__(self, url): self.url = url; self.text = "X" * 5000
            def download(self): pass
            def parse(self): pass

        # Patch the `from newspaper import Article` name inside _format_text
        fake_mod = type("M", (), {"Article": FakeNewspaperArticle})()
        import sys
        monkeypatch.setitem(sys.modules, "newspaper", fake_mod)

        text = b._format_text(article, "full")
        assert text.startswith("Headline text\n\n")
        assert len(text) >= 1500

    def test_full_fallback_on_scrape_error(self, tmp_path, article, monkeypatch):
        b = _make_backend_with_stub(tmp_path)

        class BrokenArticle:
            def __init__(self, url): pass
            def download(self): raise RuntimeError("403 paywall")
            def parse(self): pass

        fake_mod = type("M", (), {"Article": BrokenArticle})()
        import sys
        monkeypatch.setitem(sys.modules, "newspaper", fake_mod)

        text = b._format_text(article, "full")
        # Falls back to headline+summary form, not empty
        assert "Headline text" in text and "Short summary." in text

    def test_full_no_url_returns_headline(self, tmp_path):
        b = _make_backend_with_stub(tmp_path)
        text = b._format_text({"headline": "h", "summary": "s", "url": ""}, "full")
        assert text == "h: s"


# ─────────────────────────────────────────────────────────────────────────────
# Backend search() — fetch + ranking
# ─────────────────────────────────────────────────────────────────────────────


class TestBackendSearch:
    def test_fetch_failure_returns_empty(self, tmp_path):
        b = _make_backend_with_stub(tmp_path)

        def boom(ticker, _from=None, to=None):
            raise RuntimeError("network down")
        b.client.company_news = boom

        out = b.search("q", ["NVDA"], top_k=5)
        assert out == []  # no exception propagated

    def test_multi_ticker_results_ranked_by_recency(self, tmp_path):
        now = int(time.time())
        articles_by_ticker = {
            "NVDA": [{"id": 1, "datetime": now - 80 * 86400, "headline": "old NVDA", "summary": ""}],
            "AMD":  [{"id": 2, "datetime": now - 1 * 86400, "headline": "fresh AMD", "summary": ""}],
        }
        b = _make_backend_with_stub(tmp_path, articles_by_ticker)
        out = b.search("q", ["NVDA", "AMD"], top_k=5, days_back=90)
        assert len(out) == 2
        # Fresh AMD should rank above old NVDA
        assert out[0]["ticker"] == "AMD"
        assert out[0]["score"] > out[1]["score"]

    def test_top_k_truncation_after_ranking(self, tmp_path):
        now = int(time.time())
        articles = [
            {"id": i, "datetime": now - i * 86400, "headline": f"h{i}", "summary": ""}
            for i in range(10)
        ]
        b = _make_backend_with_stub(tmp_path, {"NVDA": articles})
        out = b.search("q", ["NVDA"], top_k=3, days_back=90)
        assert len(out) == 3
        # Should be the 3 most recent (lowest age days)
        assert out[0]["score"] >= out[1]["score"] >= out[2]["score"]


# ─────────────────────────────────────────────────────────────────────────────
# Orchestrator guards
# ─────────────────────────────────────────────────────────────────────────────


class _FakeBackend:
    """In-memory NewsBackend stand-in for orchestrator tests."""
    def __init__(self):
        self.calls = []

    def search(self, query, tickers, top_k=5, days_back=90, depth="headline", use_cache=False):
        self.calls.append((query, tuple(tickers), top_k, days_back, depth, use_cache))
        return [{
            "chunk_id": f"news_{t}_fake",
            "text": f"fake news for {t}",
            "ticker": t,
            "fiscal_year": 2024,
            "section": SECTION_PREFIX,
            "score": 1.0,
        } for t in tickers]


@pytest.fixture
def patch_backend(monkeypatch):
    fake = _FakeBackend()
    monkeypatch.setattr(
        "semigraph.online.news_search._get_backend",
        lambda cfg=None: fake,
    )
    return fake


class TestOrchestratorGuards:
    def test_empty_query_returns_empty(self, patch_backend):
        assert news_search("") == []
        assert news_search("   ") == []
        assert patch_backend.calls == []

    def test_no_news_intent_returns_empty(self, patch_backend):
        # Has ticker but no news keyword → backend never invoked
        assert news_search("Who are NVDA's competitors?") == []
        assert patch_backend.calls == []

    def test_no_ticker_returns_empty(self, patch_backend, monkeypatch):
        # Has news keyword but no corpus ticker → backend never invoked
        monkeypatch.setattr(
            "semigraph.online._ticker.expand_query",
            lambda q, cfg=None: q,
        )
        assert news_search("latest semiconductor news") == []
        assert patch_backend.calls == []

    def test_single_ticker_dispatches(self, patch_backend):
        out = news_search("NVDA news latest", top_k_chunks=5)
        assert len(patch_backend.calls) == 1
        assert patch_backend.calls[0][1] == ("NVDA",)
        assert len(out) == 1

    def test_multi_ticker_passes_all(self, patch_backend):
        out = news_search("latest news about AMD and NVDA", top_k_chunks=10)
        assert len(patch_backend.calls) == 1
        assert set(patch_backend.calls[0][1]) == {"AMD", "NVDA"}

    def test_thai_query_resolves_via_expansion(self, patch_backend, monkeypatch):
        monkeypatch.setattr(
            "semigraph.online._ticker.expand_query",
            lambda q, cfg=None: f"{q} QCOM",
        )
        out = news_search("ข่าวล่าสุดของ Qualcomm")
        assert len(out) == 1
        assert patch_backend.calls[0][1] == ("QCOM",)

    def test_use_expansion_false_blocks_natural_language(self, patch_backend, monkeypatch):
        called = {"flag": False}
        def fake_expand(q, cfg=None):
            called["flag"] = True
            return f"{q} NVDA"
        monkeypatch.setattr("semigraph.online._ticker.expand_query", fake_expand)

        out = news_search("Nvidia latest news", use_expansion=False)
        assert out == []
        assert called["flag"] is False

    def test_depth_param_passed_to_backend(self, patch_backend):
        news_search("NVDA news latest", depth="full")
        assert patch_backend.calls[0][4] == "full"

    def test_use_cache_param_passed_to_backend(self, patch_backend):
        news_search("NVDA news latest", use_cache=True)
        assert patch_backend.calls[0][5] is True

    def test_days_back_override(self, patch_backend):
        news_search("NVDA news latest", days_back=30)
        assert patch_backend.calls[0][3] == 30

    def test_six_key_shape_enforced(self, patch_backend):
        chunks = news_search("NVDA news latest", top_k_chunks=3)
        required = {"chunk_id", "text", "ticker", "fiscal_year", "section", "score"}
        for c in chunks:
            assert set(c.keys()) == required


# ─────────────────────────────────────────────────────────────────────────────
# Missing API key → graceful error chunk
# ─────────────────────────────────────────────────────────────────────────────


class TestMissingApiKey:
    def test_missing_key_returns_error_chunk(self, monkeypatch):
        def raising_backend(cfg=None):
            raise RuntimeError("FINNHUB_API_KEY is empty")
        monkeypatch.setattr(
            "semigraph.online.news_search._get_backend",
            raising_backend,
        )
        out = news_search("NVDA news latest")
        assert len(out) == 1
        assert out[0]["chunk_id"] == "news_unavailable"
        assert out[0]["section"] == "News_error"
        assert "unavailable" in out[0]["text"].lower()


# ─────────────────────────────────────────────────────────────────────────────
# Protocol contract — drop-in backend
# ─────────────────────────────────────────────────────────────────────────────


class TestProtocolContract:
    def test_fake_backend_satisfies_protocol(self):
        # Structural typing — _FakeBackend implements .search() with right signature
        backend: NewsBackend = _FakeBackend()
        assert hasattr(backend, "search")
        out = backend.search("q", ["NVDA"], top_k=1)
        assert isinstance(out, list)

    def test_finnhub_backend_has_search_method(self):
        assert hasattr(FinnhubNewsBackend, "search")


# ─────────────────────────────────────────────────────────────────────────────
# Module-level invariants
# ─────────────────────────────────────────────────────────────────────────────


def test_default_days_back():
    assert DEFAULT_DAYS_BACK == 90


def test_section_prefix_constant():
    assert SECTION_PREFIX == "News_finnhub"


def test_news_keywords_include_core_terms():
    for kw in ("news", "latest", "recent", "headline", "ข่าว", "ล่าสุด"):
        assert kw in NEWS_KEYWORDS


def test_corpus_tickers_shared_with_financial():
    """News tool uses the same CORPUS_TICKERS as financial — single source of truth,
    now derived from config `tickers:` (synced to Neo4j by pilot.py)."""
    from semigraph.config import get_config
    assert CORPUS_TICKERS == frozenset(t.upper() for t in get_config().tickers)
    assert "NVDA" in CORPUS_TICKERS
