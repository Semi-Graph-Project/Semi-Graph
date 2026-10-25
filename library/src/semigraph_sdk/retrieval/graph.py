"""Coordinate generic graph seeds, workspace projection, and PPR ranking."""

from __future__ import annotations

from typing import Any, Callable

from ..config import SDKConfig
from .documents import attach_documents
from .ppr import rank_chunks, rank_entities
from .projection import ProjectionError, ensure_projection, projection_name
from .seeds import select_seeds
from .triple_cache import TripleVectorCache


def graph_retrieve(
    session,
    config: SDKConfig,
    *,
    query: str,
    top_k: int,
    corpus_revision: int,
    encode: Callable[[str], list[float]],
    triple_cache: TripleVectorCache,
    projection_lock,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Run one Graph search. Relation types come from the SDK-owned projection."""
    query_vector = encode(query)
    seed_refs, seed_trace = select_seeds(
        session,
        config,
        query_vector=query_vector,
        corpus_revision=corpus_revision,
        cache=triple_cache,
    )
    trace: dict[str, Any] = {
        "tool": "graph",
        "query": query,
        "seed": seed_trace,
        "seed_node_count": len(seed_refs),
    }
    if not seed_refs:
        trace["abort_reason"] = "no_seeds"
        trace["projection"] = None
        trace["ppr_entities"] = []
        return [], trace

    with projection_lock:
        projection = _ensure_projection(session, config.workspace_id)
    trace["projection"] = projection
    graph_config = config.retrieval.graph
    ranked = rank_chunks(
        session,
        graph_name=projection["name"],
        source_refs=seed_refs,
        damping=graph_config.damping,
        max_iterations=graph_config.max_iterations,
        top_k=top_k,
    )
    entities = rank_entities(
        session,
        graph_name=projection["name"],
        source_refs=seed_refs,
        damping=graph_config.damping,
        max_iterations=graph_config.max_iterations,
        top_k=graph_config.top_k_entities_in_trace,
    )
    trace["ppr_entities"] = entities
    trace["chunk_ppr"] = [
        {"chunk_id": row["chunk_id"], "rank": row["rank"], "score": row["score"]}
        for row in ranked
    ]
    trace["candidate_count"] = len(ranked)
    return attach_documents(session, ranked), trace


def _ensure_projection(session, workspace_id: str) -> dict[str, Any]:
    """Recover if another Engine created the same projection concurrently."""
    try:
        return ensure_projection(session, workspace_id)
    except ProjectionError:
        name = projection_name(workspace_id)
        exists = session.run(
            "CALL gds.graph.exists($graph_name) YIELD exists RETURN exists",
            graph_name=name,
        ).single()
        if not exists or not exists["exists"]:
            raise
        row = session.run(
            "CALL gds.graph.list($graph_name) "
            "YIELD graphName, nodeCount, relationshipCount "
            "RETURN graphName, nodeCount, relationshipCount",
            graph_name=name,
        ).single()
        if row is None:
            raise
        return {
            "name": row["graphName"],
            "node_count": int(row["nodeCount"]),
            "relationship_count": int(row["relationshipCount"]),
            "created": False,
        }
