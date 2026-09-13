from types import SimpleNamespace

import pytest

import semigraph.agents.nodes as nodes
from semigraph.agents.contracts import PlannedTask


@pytest.mark.parametrize("tool", ["vector", "graph"])
def test_execute_node_calls_selected_retriever(monkeypatch, tool):
    chunks = [{"id": "chunk-1"}, {"id": "chunk-2"}]
    calls = []
    cfg = SimpleNamespace()

    def fake_retriever(*, query, top_k_chunks, cfg):
        calls.append({
            "query": query,
            "top_k_chunks": top_k_chunks,
            "cfg": cfg,
        })
        return chunks

    monkeypatch.setitem(nodes.RETRIEVERS, tool, fake_retriever)

    result = nodes.execute_node(
        {
            "task": PlannedTask(
                query="What risks did NVIDIA disclose?",
                requirement="Evidence of NVIDIA discloses risks.",
            ),
        },
        tool=tool,
        top_k_chunks=2,
        cfg=cfg,
    )

    assert result == {
        "chunks": chunks,
        "current_query": "What risks did NVIDIA disclose?",
        "current_strategy": None,
    }
    assert calls == [{
        "query": "What risks did NVIDIA disclose?",
        "top_k_chunks": 2,
        "cfg": cfg,
    }]


def test_execute_node_uses_retry_query(monkeypatch):
    calls = []

    def fake_retriever(*, query, top_k_chunks, cfg):
        calls.append(query)
        return []

    monkeypatch.setitem(nodes.RETRIEVERS, "graph", fake_retriever)

    result = nodes.execute_node(
        {
            "task": PlannedTask(
                query="Original query",
                requirement="Evidence requirement",
            ),
            "assessment": {
                "accepted_chunk_ids": [],
                "is_covered": False,
                "retry_query": "Expanded retry query",
                "retry_strategy": "anchor_enrichment",
            },
        },
        tool="graph",
        top_k_chunks=5,
        cfg=SimpleNamespace(),
    )

    assert calls == ["Expanded retry query"]
    assert result["current_query"] == "Expanded retry query"
    assert result["current_strategy"] == "anchor_enrichment"
