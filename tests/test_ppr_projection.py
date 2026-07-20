from unittest.mock import MagicMock

import pytest

import semigraph.online.ppr as ppr


PROJECTION_INFO = {
    "graphName": "semigraph_ppr_entity_chunk",
    "nodeCount": 12,
    "relationshipCount": 24,
}


def _result(row=None):
    result = MagicMock()
    result.single.return_value = row
    return result


def test_entity_only_projection_excludes_chunks():
    query = ppr._build_node_query("entity_only")
    assert "Entity" in query
    assert "Chunk" not in query


def test_entity_chunk_projection_contains_context_edges():
    node_query = ppr._build_node_query("entity_chunk")
    rel_query = ppr._build_rel_query("entity_chunk")

    assert "Chunk" in node_query
    assert "MENTIONS" in rel_query
    assert "SYNONYM_OF" in rel_query


@pytest.mark.parametrize(
    "function",
    (ppr._build_node_query, ppr._build_rel_query, ppr.projection_name),
)
def test_projection_rejects_unknown_mode(function):
    with pytest.raises(ValueError, match="Unknown PPR graph mode"):
        function("unknown")


def test_top_chunk_rows_filters_before_top_k():
    rows = [
        {"nodeId": 1, "score": 0.99},
        {"nodeId": 2, "score": 0.80},
        {"nodeId": 3, "score": 0.70},
        {"nodeId": 4, "score": 0.60},
    ]
    assert ppr._top_chunk_score_rows(rows, {3, 4}, top_k=1) == [
        {"nodeId": 3, "score": 0.70},
    ]


def test_ensure_projection_creates_then_reuses_named_graph():
    session = MagicMock()
    session.run.side_effect = [
        _result({"exists": False}),
        _result(PROJECTION_INFO),
        _result({"exists": True}),
        _result(PROJECTION_INFO),
    ]

    created = ppr.ensure_projection(session, "entity_chunk")
    reused = ppr.ensure_projection(session, "entity_chunk")

    assert created["status"] == "created"
    assert reused["status"] == "reused"
    assert reused["node_count"] == 12
    queries = [call.args[0] for call in session.run.call_args_list]
    assert queries.count(ppr._CYPHER_PROJECT) == 1


def test_refresh_projection_drops_then_recreates_graph():
    session = MagicMock()
    session.run.side_effect = [
        _result({"exists": True}),
        _result(PROJECTION_INFO),
        _result(),
        _result({"exists": False}),
        _result(PROJECTION_INFO),
    ]

    refreshed = ppr.refresh_projection(session, "entity_chunk")

    assert refreshed["status"] == "refreshed"
    assert refreshed["previous_status"] == "dropped"
    lifecycle = [
        call.args[0]
        for call in session.run.call_args_list
        if call.args[0] in {ppr._CYPHER_DROP, ppr._CYPHER_PROJECT}
    ]
    assert lifecycle == [ppr._CYPHER_DROP, ppr._CYPHER_PROJECT]
