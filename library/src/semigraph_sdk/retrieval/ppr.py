"""Run PageRank in GDS and return only ranked SDK nodes."""

from __future__ import annotations

from typing import Any


_PPR_CHUNKS = """
UNWIND $source_refs AS source_ref
CALL (source_ref) {
    MATCH (seed:Entity {name: source_ref.name, type: source_ref.type})
    RETURN seed
    UNION
    MATCH (seed:Chunk {chunk_id: source_ref.chunk_id})
    RETURN seed
}
WITH collect(DISTINCT seed) AS source_nodes
CALL gds.pageRank.stream($graph_name, {
    sourceNodes: source_nodes,
    dampingFactor: $damping,
    maxIterations: $max_iterations
})
YIELD nodeId, score
WITH gds.util.asNode(nodeId) AS node, score
WHERE node:Chunk AND score > 0
RETURN node.chunk_id AS chunk_id, score
ORDER BY score DESC, chunk_id
LIMIT $top_k
"""


_PPR_ENTITIES = """
UNWIND $source_refs AS source_ref
CALL (source_ref) {
    MATCH (seed:Entity {name: source_ref.name, type: source_ref.type})
    RETURN seed
    UNION
    MATCH (seed:Chunk {chunk_id: source_ref.chunk_id})
    RETURN seed
}
WITH collect(DISTINCT seed) AS source_nodes
CALL gds.pageRank.stream($graph_name, {
    sourceNodes: source_nodes,
    dampingFactor: $damping,
    maxIterations: $max_iterations
})
YIELD nodeId, score
WITH gds.util.asNode(nodeId) AS node, score
WHERE node:Entity AND score > 0
RETURN node.name AS name, node.type AS type, score
ORDER BY score DESC, name, type
LIMIT $top_k
"""


def rank_chunks(
    session,
    *,
    graph_name: str,
    source_refs: list[dict[str, str]],
    damping: float,
    max_iterations: int,
    top_k: int,
) -> list[dict[str, Any]]:
    rows = session.run(
        _PPR_CHUNKS,
        graph_name=graph_name,
        source_refs=source_refs,
        damping=damping,
        max_iterations=max_iterations,
        top_k=top_k,
    )
    return [
        {
            "chunk_id": row["chunk_id"],
            "score": float(row["score"]),
            "score_kind": "ppr",
            "rank": rank,
        }
        for rank, row in enumerate(rows, start=1)
    ]


def rank_entities(
    session,
    *,
    graph_name: str,
    source_refs: list[dict[str, str]],
    damping: float,
    max_iterations: int,
    top_k: int,
) -> list[dict[str, Any]]:
    if top_k <= 0:
        return []
    rows = session.run(
        _PPR_ENTITIES,
        graph_name=graph_name,
        source_refs=source_refs,
        damping=damping,
        max_iterations=max_iterations,
        top_k=top_k,
    )
    return [
        {
            "name": row["name"],
            "type": row["type"],
            "score": float(row["score"]),
            "rank": rank,
        }
        for rank, row in enumerate(rows, start=1)
    ]
