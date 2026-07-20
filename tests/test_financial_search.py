"""Unit tests for the financial_search compatibility wrapper.

Focus: orchestrator pure-function logic + Protocol contract. Backend API calls
are mocked — real Finnhub hits live in integration scripts, not unit tests.
"""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from semigraph.financial.backend import FinancialQueryResult
from semigraph.financial.query_spec import FinancialQuerySpec
from semigraph.online._ticker import CORPUS_TICKERS, extract_tickers, resolve_tickers
from semigraph.online.financial_search import (
    SNAPSHOT_KINDS,
    FinancialBackend,
    FinancialIntentParseError,
    UnsupportedFinancialQuery,
    _build_financial_query_spec,
    _get_backend,
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

    def test_all_corpus_tickers_detected(self):
        q = " ".join(sorted(CORPUS_TICKERS))
        out = extract_tickers(q)
        assert set(out) == CORPUS_TICKERS


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

    @pytest.mark.parametrize("ticker", ["AAPL", "ARM", "ASML"])
    def test_explicit_out_of_corpus_ticker_skips_expansion(
        self,
        ticker: str,
        monkeypatch,
    ):
        called = {"flag": False}

        def fake_expand(q, cfg=None):
            called["flag"] = True
            return f"{q} QCOM AVGO"

        monkeypatch.setattr(
            "semigraph.online._ticker.expand_query",
            fake_expand,
        )

        assert resolve_tickers(f"What was {ticker}'s revenue in FY2025?") == []
        assert called["flag"] is False

    def test_out_of_corpus_ticker_blocks_partial_comparison(self, monkeypatch):
        called = {"flag": False}

        def fake_expand(q, cfg=None):
            called["flag"] = True
            return q

        monkeypatch.setattr(
            "semigraph.online._ticker.expand_query",
            fake_expand,
        )

        assert resolve_tickers("Compare AAPL and NVDA revenue") == []
        assert called["flag"] is False

    def test_financial_acronyms_do_not_look_like_unknown_tickers(self):
        assert resolve_tickers("NVDA ROA and EPS in FY2025 USD") == ["NVDA"]

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
    """Concrete v2 `FinancialBackend` with no PostgreSQL dependency."""

    def __init__(self, chunks_per_ticker: int = 3):
        self.chunks_per_ticker = chunks_per_ticker
        self.calls: list[FinancialQuerySpec] = []

    def query(
        self,
        spec: FinancialQuerySpec,
        *,
        top_k: int = 5,
    ) -> FinancialQueryResult:
        self.calls.append(spec)
        out: list[dict] = []
        for t in spec.tickers:
            for kind in SNAPSHOT_KINDS[: self.chunks_per_ticker]:
                out.append(_make_chunk(t, kind, f"{t} {kind} fake", 2025))
        chunks = out[:top_k]
        return FinancialQueryResult(
            chunks=chunks,
            trace={"profile": "fake", "returned_count": len(chunks)},
        )


@pytest.fixture
def patch_backend(monkeypatch):
    """Replace the parser and backend so tests call neither LLM nor Postgres."""
    fake = FakeBackend()
    monkeypatch.setattr(
        "semigraph.online.financial_search._get_backend",
        lambda cfg=None: fake,
    )

    def fake_parser(query, *, tickers, cfg):
        return FinancialQuerySpec(
            query=query,
            tickers=tickers,
            metrics=["revenue"],
            frequency="annual",
            operation="compare" if len(tickers) > 1 else "lookup",
        )

    monkeypatch.setattr(
        "semigraph.online.financial_search._build_financial_query_spec",
        fake_parser,
    )
    return fake


class TestOrchestrator:
    def test_empty_query_returns_empty(self):
        assert financial_search("")["chunks"] == []
        assert financial_search("   ")["chunks"] == []
        assert financial_search("")["trace"]["reason"] == "empty_query"

    def test_query_with_ticker_is_not_keyword_gated(self, patch_backend):
        out = financial_search("What were NVDA's total assets in FY2025?")

        assert out["chunks"]
        assert len(patch_backend.calls) == 1

    def test_unsupported_metric_skips_backend(
        self,
        patch_backend,
        monkeypatch,
    ):
        def unsupported_parser(query, *, tickers, cfg):
            raise UnsupportedFinancialQuery("EBITDA is not supported")

        monkeypatch.setattr(
            "semigraph.online.financial_search._build_financial_query_spec",
            unsupported_parser,
        )

        result = financial_search("What was NVDA's EBITDA in FY2025?")

        assert result["chunks"] == []
        assert result["trace"]["status"] == "skipped"
        assert result["trace"]["reason"] == "unsupported_metric"
        assert result["trace"]["unsupported_reason"] == "EBITDA is not supported"
        assert patch_backend.calls == []

    def test_no_ticker_returns_empty(self, patch_backend, monkeypatch):
        # Has keyword but no corpus ticker → expand fails → backend never invoked
        # Patch expand_query to return original (simulating LLM finding nothing relevant)
        monkeypatch.setattr(
            "semigraph.online._ticker.expand_query",
            lambda q, cfg=None: q,
        )
        result = financial_search("What is the market revenue trend?")
        assert result["chunks"] == []
        assert result["trace"]["reason"] == "no_corpus_ticker"
        assert patch_backend.calls == []

    def test_natural_language_ticker_via_expansion(self, patch_backend, monkeypatch):
        """End-to-end: natural name resolves to NVDA before backend query."""
        monkeypatch.setattr(
            "semigraph.online._ticker.expand_query",
            lambda q, cfg=None: f"{q} NVDA",
        )
        out = financial_search("What is Nvidia's revenue?", top_k_chunks=5)
        assert len(patch_backend.calls) == 1
        assert patch_backend.calls[0].tickers == ["NVDA"]
        assert len(out["chunks"]) == 3

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
        assert out["chunks"] == []
        assert called["flag"] is False

    def test_single_ticker_dispatches_backend(self, patch_backend):
        out = financial_search("What is NVDA latest revenue?", top_k_chunks=5)
        assert len(patch_backend.calls) == 1
        assert patch_backend.calls[0].tickers == ["NVDA"]
        assert len(out["chunks"]) == 3  # 3 snapshot kinds

    def test_multi_ticker_passes_all(self, patch_backend):
        out = financial_search("Compare AMD and NVDA gross margin", top_k_chunks=10)
        assert patch_backend.calls[0].tickers == ["AMD", "NVDA"]
        assert len(out["chunks"]) == 6  # 2 tickers × 3 kinds

    def test_top_k_truncation_applied(self, patch_backend):
        out = financial_search("Compare AMD and NVDA revenue", top_k_chunks=4)
        # Backend returns 6, orchestrator should truncate to 4
        assert len(out["chunks"]) == 4

    def test_six_key_shape_enforced(self, patch_backend):
        out = financial_search("NVDA revenue", top_k_chunks=5)
        required = {"chunk_id", "text", "ticker", "fiscal_year", "section", "score"}
        for c in out["chunks"]:
            assert required <= set(c.keys())

    def test_legacy_finnhub_branch_is_kept_as_fallback(self, monkeypatch):
        class FakeLegacyBackend:
            def search(self, query, tickers, top_k=5):
                return [_make_chunk(tickers[0], "quote", "fake quote", 0)]

        cfg = SimpleNamespace(
            financial_backend="finnhub",
            tickers=["NVDA"],
        )
        monkeypatch.setattr(
            "semigraph.online.financial_search._get_backend",
            lambda cfg=None: FakeLegacyBackend(),
        )
        monkeypatch.setattr(
            "semigraph.online.financial_search._build_financial_query_spec",
            lambda query, *, tickers, cfg: FinancialQuerySpec(
                query=query,
                tickers=tickers,
                metrics=["current_price"],
                frequency="snapshot",
                operation="lookup",
            ),
        )

        out = financial_search(
            "NVDA stock price",
            cfg=cfg,
        )

        assert len(out["chunks"]) == 1
        assert out["trace"]["profile"] == "finnhub_legacy_v1"


class TestFinancialToolSpecBuilder:
    @staticmethod
    def _valid_json():
        return """{
            "supported": true,
            "metrics": ["revenue"],
            "frequency": "annual",
            "operation": "trend",
            "limit": 10
        }"""

    def test_valid_json_becomes_typed_spec(self, monkeypatch):
        class FakeLLM:
            def invoke(self, messages):
                assert "Never write SQL" in messages[0]["content"]
                assert "Financial Tool owns them" in messages[0]["content"]
                return SimpleNamespace(
                    content=TestFinancialToolSpecBuilder._valid_json()
                )

        monkeypatch.setattr(
            "semigraph.online.financial_search.get_llm",
            lambda cfg: FakeLLM(),
        )

        spec = _build_financial_query_spec(
            "NVDA annual revenue trend",
            tickers=["NVDA"],
            cfg=SimpleNamespace(),
        )

        assert spec.query == "NVDA annual revenue trend"
        assert spec.tickers == ["NVDA"]
        assert spec.operation.value == "trend"
        assert spec.metrics == ["revenue"]

    def test_invalid_first_response_is_retried_with_feedback(self, monkeypatch):
        class FakeLLM:
            def __init__(self):
                self.calls = []

            def invoke(self, messages):
                self.calls.append(messages)
                content = (
                    "{\"supported\": true, \"tickers\": [\"AMD\"], "
                    "\"metrics\": [\"revenue\"], "
                    "\"frequency\": \"annual\", \"operation\": \"trend\"}"
                    if len(self.calls) == 1
                    else TestFinancialToolSpecBuilder._valid_json()
                )
                return SimpleNamespace(content=content)

        fake = FakeLLM()
        monkeypatch.setattr(
            "semigraph.online.financial_search.get_llm",
            lambda cfg: fake,
        )

        spec = _build_financial_query_spec(
            "NVDA annual revenue trend",
            tickers=["NVDA"],
            cfg=SimpleNamespace(),
        )

        # The LLM attempted to replace NVDA with AMD, but the tool stayed owner.
        assert spec.tickers == ["NVDA"]
        assert len(fake.calls) == 2
        assert "previous output failed validation" in fake.calls[1][0]["content"]

    def test_single_year_lookup_retries_until_both_bounds_are_set(
        self,
        monkeypatch,
    ):
        class FakeLLM:
            def __init__(self):
                self.calls = []

            def invoke(self, messages):
                self.calls.append(messages)
                end_year = "null" if len(self.calls) == 1 else "2025"
                return SimpleNamespace(content=f"""{{
                    "supported": true,
                    "metrics": ["stockholders_equity"],
                    "frequency": "annual",
                    "operation": "lookup",
                    "start_year": 2025,
                    "end_year": {end_year},
                    "limit": 5
                }}""")

        fake = FakeLLM()
        monkeypatch.setattr(
            "semigraph.online.financial_search.get_llm",
            lambda cfg: fake,
        )

        spec = _build_financial_query_spec(
            "What was LRCX stockholders equity in FY2025?",
            tickers=["LRCX"],
            cfg=SimpleNamespace(),
        )

        assert spec.start_year == spec.end_year == 2025
        assert len(fake.calls) == 2
        assert "both start_year and end_year" in fake.calls[1][0]["content"]

    @pytest.mark.parametrize(
        ("query", "reason"),
        [
            ("What was NVDA's EBITDA in FY2025?", "EBITDA is not supported"),
            (
                "What was NVDA's debt-to-equity ratio in FY2025?",
                "debt-to-equity is not supported",
            ),
        ],
    )
    def test_unsupported_metric_returns_structured_decision(
        self,
        query: str,
        reason: str,
        monkeypatch,
    ):
        class FakeLLM:
            def invoke(self, messages):
                assert '"supported"' in messages[0]["content"]
                assert "Never substitute" in messages[0]["content"]
                return SimpleNamespace(
                    content=json.dumps(
                        {
                            "supported": False,
                            "unsupported_reason": reason,
                        }
                    )
                )

        monkeypatch.setattr(
            "semigraph.online.financial_search.get_llm",
            lambda cfg: FakeLLM(),
        )

        with pytest.raises(UnsupportedFinancialQuery, match=reason):
            _build_financial_query_spec(
                query,
                tickers=["NVDA"],
                cfg=SimpleNamespace(),
            )

    def test_two_invalid_responses_raise_clear_error(self, monkeypatch):
        class FakeLLM:
            def invoke(self, messages):
                return SimpleNamespace(content="not json")

        monkeypatch.setattr(
            "semigraph.online.financial_search.get_llm",
            lambda cfg: FakeLLM(),
        )

        with pytest.raises(FinancialIntentParseError, match="2 attempts"):
            _build_financial_query_spec(
                "NVDA revenue",
                tickers=["NVDA"],
                cfg=SimpleNamespace(),
            )


# ─────────────────────────────────────────────────────────────────────────────
# Protocol contract — structural typing sanity
# ─────────────────────────────────────────────────────────────────────────────


class TestProtocolContract:
    def test_fake_backend_satisfies_protocol(self):
        # Protocol is structural; assignment catches drift during type checking.
        backend: FinancialBackend = FakeBackend()
        result = backend.query(
            FinancialQuerySpec(
                query="NVDA revenue",
                tickers=["NVDA"],
                metrics=["revenue"],
                frequency="annual",
                operation="lookup",
            ),
            top_k=5,
        )
        assert isinstance(result, FinancialQueryResult)

    def test_finnhub_backend_has_search_method(self):
        # Don't instantiate (needs real API key) — just verify class shape
        from semigraph.online.financial_search import FinnhubAPIBackend
        assert hasattr(FinnhubAPIBackend, "search")
        assert callable(FinnhubAPIBackend.search)

    def test_factory_defaults_to_postgresql_backend(self):
        from semigraph.financial.backend import PostgreSQLBackend

        cfg = SimpleNamespace(financial_backend="postgresql")
        assert isinstance(_get_backend(cfg), PostgreSQLBackend)


# ─────────────────────────────────────────────────────────────────────────────
# Constants sanity (catches accidental shrinkage of corpus)
# ─────────────────────────────────────────────────────────────────────────────


def test_corpus_tickers_derive_from_config():
    # CORPUS_TICKERS is no longer hard-coded — it derives from config `tickers:`
    # (which pilot.py keeps synced to Neo4j). Assert the derivation, not a count.
    from semigraph.config import get_config
    assert CORPUS_TICKERS == frozenset(t.upper() for t in get_config().tickers)
    assert CORPUS_TICKERS, "corpus tickers must be non-empty"


def test_snapshot_kinds_are_three():
    assert len(SNAPSHOT_KINDS) == 3
    assert SNAPSHOT_KINDS == ("financials_annual", "key_metrics", "quote")
