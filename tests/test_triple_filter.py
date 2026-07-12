import json

import pytest

from semigraph.online import triple_filter


def _candidate(candidate_id, similarity):
    return {
        "candidate_id": candidate_id,
        "head": "intel",
        "head_type": "COMP",
        "relation": "PRODUCES",
        "tail": f"product-{candidate_id}",
        "tail_type": "PRODUCT",
        "similarity": similarity,
        "head_specificity": 0.8,
        "tail_specificity": 0.7,
    }


def test_filter_selects_valid_ids_in_embedding_order(monkeypatch):
    class FakeLLM:
        def invoke(self, messages):
            payload = json.loads(messages[1]["content"])
            assert payload["query"] == "intel products"
            return type("Response", (), {
                "content": '{"selected_candidate_ids": [2, 0, 99]}'
            })()

    monkeypatch.setattr(triple_filter, "get_llm", lambda cfg: FakeLLM())
    candidates = [_candidate(0, 0.9), _candidate(1, 0.8), _candidate(2, 0.7)]

    selected, trace = triple_filter.filter_triple_candidates(
        "intel products",
        candidates,
        cfg="cfg-sentinel",
    )

    assert [candidate["candidate_id"] for candidate in selected] == [0, 2]
    assert trace["selected_candidate_ids"] == [0, 2]
    assert trace["rejected_candidate_ids"] == [1]
    assert trace["fallback"] is False
    assert trace["reason"] == "llm_selection"
    assert trace["attempts"] == 1


def test_filter_retries_then_falls_back_to_top_candidates(monkeypatch):
    calls = {"count": 0}

    class FailingLLM:
        def invoke(self, messages):
            calls["count"] += 1
            return type("Response", (), {"content": "not json"})()

    monkeypatch.setattr(triple_filter, "get_llm", lambda cfg: FailingLLM())
    candidates = [_candidate(0, 0.9), _candidate(1, 0.8), _candidate(2, 0.7)]

    selected, trace = triple_filter.filter_triple_candidates(
        "intel products",
        candidates,
        max_selected=2,
        cfg="cfg-sentinel",
    )

    assert calls["count"] == 2
    assert [candidate["candidate_id"] for candidate in selected] == [0, 1]
    assert trace["fallback"] is True
    assert trace["reason"] == "llm_error"
    assert trace["attempts"] == 2
    assert "JSONDecodeError" in trace["parse_error"]


def test_filter_empty_llm_selection_uses_embedding_fallback(monkeypatch):
    class EmptyLLM:
        def invoke(self, messages):
            return type("Response", (), {
                "content": '{"selected_candidate_ids": []}'
            })()

    monkeypatch.setattr(triple_filter, "get_llm", lambda cfg: EmptyLLM())
    candidates = [_candidate(0, 0.9), _candidate(1, 0.8)]

    selected, trace = triple_filter.filter_triple_candidates(
        "unrelated query",
        candidates,
        cfg="cfg-sentinel",
    )

    assert selected == candidates
    assert trace["fallback"] is True
    assert trace["reason"] == "empty_selection"


def test_filter_empty_candidates_does_not_call_llm(monkeypatch):
    monkeypatch.setattr(
        triple_filter,
        "get_llm",
        lambda cfg: pytest.fail("LLM must not be called"),
    )

    selected, trace = triple_filter.filter_triple_candidates(
        "intel products",
        [],
    )

    assert selected == []
    assert trace["fallback"] is False
    assert trace["reason"] == "no_candidates"
    assert trace["attempts"] == 0
