from types import SimpleNamespace

import pytest
import yaml

from eval_scripts import evaluate
from eval_scripts.evaluate import (
    _reciprocal_rank,
    _requires_llm,
    _select_queries,
    write_yaml_trace,
)


def test_reciprocal_rank_uses_first_gold_chunk():
    assert _reciprocal_rank(
        ["non-gold", "gold-b", "gold-a"],
        {"gold-a", "gold-b"},
    ) == 0.5
    assert _reciprocal_rank(["non-gold"], {"gold-a"}) == 0.0


def test_write_yaml_trace_reports_mrr(tmp_path):
    output_path = tmp_path / "trace.yaml"
    write_yaml_trace(
        [
            {"hit": 1, "recall": 1.0, "reciprocal_rank": 1.0, "latency_ms": 10.0},
            {"hit": 1, "recall": 0.5, "reciprocal_rank": 0.5, "latency_ms": 20.0},
        ],
        output_path,
    )

    summary = yaml.safe_load(output_path.read_text(encoding="utf-8"))["summary"]
    assert summary["mrr"] == 0.75


def test_select_queries_supports_smoke_limit_without_changing_full_set():
    queries = [{"id": "Q1"}, {"id": "Q2"}, {"id": "Q3"}]

    assert _select_queries(queries, None) is queries
    assert _select_queries(queries, 2) == queries[:2]
    with pytest.raises(ValueError, match="greater than zero"):
        _select_queries(queries, 0)
    with pytest.raises(ValueError, match="must not exceed"):
        _select_queries(queries, 4)


def test_requires_llm_matches_eval_tool_and_mode_contract():
    cfg = SimpleNamespace(
        agent_retrieval={"graph": {"triple_filter": "llm"}}
    )

    assert not _requires_llm("vector", "retrieve_only", cfg)
    assert _requires_llm("vector", "full_answer", cfg)
    assert _requires_llm("graph", "retrieve_only", cfg)
    assert _requires_llm("agent_vector", "retrieve_only", cfg)

    cfg.agent_retrieval["graph"]["triple_filter"] = "none"
    assert not _requires_llm("graph", "retrieve_only", cfg)


def test_validate_runtime_fails_before_llm_eval_without_provider_key(monkeypatch):
    cfg = SimpleNamespace(
        agent_retrieval={"graph": {"triple_filter": "llm"}},
        llm_api_key="",
        llm_provider="openrouter",
    )
    monkeypatch.setattr(evaluate, "get_config", lambda: cfg)

    with pytest.raises(RuntimeError, match="set it in .env"):
        evaluate._validate_runtime("graph", "retrieve_only")
