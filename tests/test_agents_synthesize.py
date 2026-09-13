import json
from types import SimpleNamespace

import pytest

import semigraph.agents.nodes as nodes
from semigraph.agents.prompts import SYNTHESIZE_ATTEMPTS_SYSTEM_PROMPT


def _worker(task_index, *chunk_ids):
    return {
        "task_index": task_index,
        "accepted_chunks": [
            {"chunk_id": chunk_id, "text": f"Evidence {chunk_id}"}
            for chunk_id in chunk_ids
        ],
    }


def test_collector_keeps_all_chunks_within_limit():
    state = {
        "original_query": "Original question",
        "worker_results": [
            _worker(1, "b1"),
            _worker(0, "a1", "a2"),
        ],
    }
    cfg = SimpleNamespace(agent_max_synthesis_chunks=3)

    result = nodes.collector_node(state, cfg=cfg)

    assert result["synthesis_input"]["original_query"] == "Original question"
    assert [
        chunk["chunk_id"]
        for chunk in result["synthesis_input"]["accepted_chunks"]
    ] == ["a1", "a2", "b1"]


def test_collector_keeps_one_per_task_then_fills_in_order():
    state = {
        "original_query": "Original question",
        "worker_results": [
            _worker(0, "a1", "a2", "a3"),
            _worker(1, "b1", "b2"),
            _worker(2, "c1"),
        ],
    }
    cfg = SimpleNamespace(agent_max_synthesis_chunks=5)

    result = nodes.collector_node(state, cfg=cfg)

    assert [
        chunk["chunk_id"]
        for chunk in result["synthesis_input"]["accepted_chunks"]
    ] == ["a1", "b1", "c1", "a2", "a3"]


def test_collector_rejects_limit_smaller_than_tasks_with_evidence():
    state = {
        "original_query": "Original question",
        "worker_results": [
            _worker(0, "a1"),
            _worker(1, "b1"),
            _worker(2, "c1"),
        ],
    }
    cfg = SimpleNamespace(agent_max_synthesis_chunks=2)

    with pytest.raises(ValueError, match="one chunk per task"):
        nodes.collector_node(state, cfg=cfg)


def test_synthesize_generates_answer_with_indexed_evidence(monkeypatch):
    calls = []
    answer = "**Answer**\n\nNVIDIA relied on TSMC [1].\n\n**Key evidence**\n\n- NVIDIA relied on TSMC [1]."

    def invoke(messages):
        calls.append(messages)
        return SimpleNamespace(content=answer)

    monkeypatch.setattr(
        nodes,
        "get_llm",
        lambda cfg: SimpleNamespace(invoke=invoke),
    )
    state = {
        "synthesis_input": {
            "original_query": "Who manufactured NVIDIA chips?",
            "accepted_chunks": [
                {"chunk_id": "c1", "text": "NVIDIA relied on TSMC."},
                {"chunk_id": "c2", "text": "TSMC manufactured the chips."},
            ],
        }
    }

    result = nodes.synthesize_node(state, cfg=SimpleNamespace())

    assert result["final_answer"] == answer
    assert result["synthesis_latency_ms"] >= 0.0
    assert calls[0][0]["content"] == SYNTHESIZE_ATTEMPTS_SYSTEM_PROMPT
    payload = json.loads(calls[0][1]["content"])
    assert payload["original_query"] == "Who manufactured NVIDIA chips?"
    assert [item["citation"] for item in payload["selected_evidence"]] == [
        "[1]",
        "[2]",
    ]


def test_synthesize_rejects_empty_answer(monkeypatch):
    monkeypatch.setattr(
        nodes,
        "get_llm",
        lambda cfg: SimpleNamespace(
            invoke=lambda messages: SimpleNamespace(content="   ")
        ),
    )
    state = {
        "synthesis_input": {
            "original_query": "Original question",
            "accepted_chunks": [],
        }
    }

    with pytest.raises(ValueError, match="empty answer"):
        nodes.synthesize_node(state, cfg=SimpleNamespace())
