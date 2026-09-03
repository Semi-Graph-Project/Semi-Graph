from unittest.mock import MagicMock

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


def test_projection_contains_entity_and_chunk_context():
    node_query = ppr._build_node_query()
    rel_query = ppr._build_rel_query()

    assert "Entity" in node_query
    assert "Chunk" in node_query
    assert "MENTIONS" in rel_query
    assert "SYNONYM_OF" in rel_query


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


def test_weighted_ppr_passes_weighted_nodes_as_source_ids():
    session = MagicMock()
    session.run.return_value = [{"nodeId": 1, "score": 0.75}]

    rows = ppr._run_ppr_rows(
        session,
        "semigraph_ppr_entity_chunk",
        [(1, 0.75), (2, 0.25)],
        damping=0.5,
        max_iterations=20,
        seed_weight_mode="similarity_specificity",
    )

    assert rows == [{"nodeId": 1, "score": 0.75}]
    assert session.run.call_args.kwargs["source_ids"] == [
        [1, 0.75],
        [2, 0.25],
    ]


def test_passage_seed_resolver_uses_chunk_ids():
    session = MagicMock()
    session.run.return_value = [{"id": 7, "seed_index": 0}]
    seeds = [{"chunk_id": "chunk-1", "similarity": 0.9}]

    rows = ppr._resolve_passage_seed_ids(session, seeds)

    assert rows == [{"id": 7, "seed_index": 0}]
    assert session.run.call_args.args[0] == ppr._CYPHER_RESOLVE_SEED_CHUNK_IDS
    assert session.run.call_args.kwargs["seeds"] == seeds


def test_weighted_seed_ids_use_resolved_seed_position():
    seeds = [
        {"chunk_id": "chunk-1", "similarity": 0.75},
        {"chunk_id": "chunk-2", "similarity": 0.25},
    ]

    weighted = ppr._build_weighted_seed_ids(
        [{"id": 11, "seed_index": 0}, {"id": 22, "seed_index": 1}],
        seeds,
        "similarity",
    )

    assert weighted == [(11, 0.75), (22, 0.25)]


def test_get_projection_creates_then_reuses_named_graph():
    session = MagicMock()
    session.run.side_effect = [
        _result({"exists": False}),
        _result(PROJECTION_INFO),
        _result({"exists": True}),
        _result(PROJECTION_INFO),
    ]

    created = ppr._get_projection(session)
    reused = ppr._get_projection(session)

    assert created["status"] == "created"
    assert reused["status"] == "reused"
    assert reused["node_count"] == 12
    queries = [call.args[0] for call in session.run.call_args_list]
    assert queries.count(ppr._CYPHER_PROJECT) == 1


def test_manage_projection_refreshes_named_graph(monkeypatch):
    session = MagicMock()
    session.run.side_effect = [
        _result({"exists": True}),
        _result(PROJECTION_INFO),
        _result(),
        _result({"exists": False}),
        _result(PROJECTION_INFO),
    ]

    driver = MagicMock()
    driver.session.return_value.__enter__.return_value = session
    monkeypatch.setattr(ppr, "get_neo4j_driver", lambda cfg: driver)

    refreshed = ppr.manage_projection("refresh")

    assert refreshed["status"] == "refreshed"
    assert refreshed["previous_status"] == "dropped"
    lifecycle = [
        call.args[0]
        for call in session.run.call_args_list
        if call.args[0] in {ppr._CYPHER_DROP, ppr._CYPHER_PROJECT}
    ]
    assert lifecycle == [ppr._CYPHER_DROP, ppr._CYPHER_PROJECT]
