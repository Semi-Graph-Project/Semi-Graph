"""Configured Neo4j vector-index search for SDK chunks."""

from __future__ import annotations

from typing import Any, Callable

from ..config import SDKConfig
from .documents import attach_documents


_VECTOR_QUERY = """
CALL db.index.vector.queryNodes($index_name, $top_k, $query_vector)
YIELD node, score
WHERE node:Chunk
  AND ($min_score IS NULL OR score >= $min_score)
RETURN node.chunk_id AS chunk_id, score
ORDER BY score DESC, chunk_id
LIMIT $top_k
"""


def vector_retrieve(
    session,
    config: SDKConfig,
    *,
    query: str,
    top_k: int,
    encode: Callable[[str], list[float]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Encode once, use the configured index, then hydrate selected documents."""
    vector = encode(query)
    rows = session.run(
        _VECTOR_QUERY,
        index_name="sg_chunk_embedding",
        top_k=top_k,
        query_vector=vector,
        min_score=config.retrieval.vector.min_score,
    )
    ranked = [
        {
            "chunk_id": row["chunk_id"],
            "rank": rank,
            "score": float(row["score"]),
            "score_kind": "cosine",
        }
        for rank, row in enumerate(rows, start=1)
    ]
    return attach_documents(session, ranked), {
        "tool": "vector",
        "query": query,
        "index": "sg_chunk_embedding",
        "candidate_count": len(ranked),
        "score_kind": "cosine",
    }
