import pytest

from semigraph.online.ppr import (
    _build_node_query,
    _build_rel_query,
    _top_chunk_score_rows,
)


def test_entity_only_projection_excludes_chunks():
    query = _build_node_query("entity_only")
    assert "Entity" in query
    assert "Chunk" not in query


def test_entity_chunk_projection_contains_context_edges():
    node_query = _build_node_query("entity_chunk")
    rel_query = _build_rel_query("entity_chunk")

    assert "Chunk" in node_query
    assert "MENTIONS" in rel_query
    assert "SYNONYM_OF" in rel_query


def test_projection_rejects_unknown_mode():
    with pytest.raises(ValueError, match="Unknown PPR graph mode"):
        _build_node_query("unknown")

    with pytest.raises(ValueError, match="Unknown PPR graph mode"):
        _build_rel_query("unknown")


def test_top_chunk_rows_filters_before_top_k():
    ppr_rows = [
        {"nodeId": 1, "score": 0.99},
        {"nodeId": 2, "score": 0.80},
        {"nodeId": 3, "score": 0.70},
        {"nodeId": 4, "score": 0.60},
    ]

    assert _top_chunk_score_rows(ppr_rows, {3, 4}, top_k=1) == [
        {"nodeId": 3, "score": 0.70},
    ]
