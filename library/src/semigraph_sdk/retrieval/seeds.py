"""Select graph seeds from triple, entity, or chunk vector similarity."""

from __future__ import annotations

from typing import Any

from ..config import SDKConfig
from .triple_cache import TripleVectorCache


_ENTITY_QUERY = """
CALL db.index.vector.queryNodes('sg_entity_embedding', $top_k, $query_vector)
YIELD node, score
WHERE node:Entity AND ($min_score IS NULL OR score >= $min_score)
RETURN node.name AS name, node.type AS type, score
ORDER BY score DESC, name, type
LIMIT $top_k
"""


_CHUNK_QUERY = """
CALL db.index.vector.queryNodes('sg_chunk_embedding', $top_k, $query_vector)
YIELD node, score
WHERE node:Chunk AND ($min_score IS NULL OR score >= $min_score)
RETURN node.chunk_id AS chunk_id, score
ORDER BY score DESC, chunk_id
LIMIT $top_k
"""


def select_seeds(
    session,
    config: SDKConfig,
    *,
    query_vector: list[float],
    corpus_revision: int,
    cache: TripleVectorCache,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    graph = config.retrieval.graph
    mode = graph.seed_mode
    min_score = graph.min_seed_score
    cache_hit = None
    if mode == "triple":
        selected, cache_hit = cache.select(
            session,
            workspace_id=config.workspace_id,
            database_name=config.database.name,
            corpus_revision=corpus_revision,
            embedding_fingerprint=config.embedding.fingerprint,
            query_vector=query_vector,
            top_k=graph.seed_k,
            min_score=min_score,
        )
        seed_refs = []
        seen = set()
        for item in selected:
            for name, entity_type in (
                (item["head"], item["head_type"]),
                (item["tail"], item["tail_type"]),
            ):
                key = (name, entity_type)
                if key not in seen:
                    seen.add(key)
                    seed_refs.append({
                        "kind": "entity", "name": name, "type": entity_type,
                    })
        return seed_refs, {
            "mode": mode,
            "cache_hit": cache_hit,
            "selected": [
                {
                    "assertion_id": item["assertion_id"],
                    "relation": item["relation"],
                    "head": item["head"],
                    "tail": item["tail"],
                    "rank": item["rank"],
                    "score": item["score"],
                }
                for item in selected
            ],
        }

    index_query = _ENTITY_QUERY if mode == "entity" else _CHUNK_QUERY
    rows = session.run(
        index_query,
        top_k=graph.seed_k,
        query_vector=query_vector,
        min_score=min_score,
    )
    selected = []
    seed_refs = []
    for rank, row in enumerate(rows, start=1):
        item = {
            "name": row.get("name"),
            "type": row.get("type"),
            "chunk_id": row.get("chunk_id"),
            "score": float(row["score"]),
            "rank": rank,
        }
        selected.append(item)
        if mode == "entity":
            seed_refs.append({
                "kind": "entity", "name": item["name"], "type": item["type"],
            })
        else:
            seed_refs.append({"kind": "chunk", "chunk_id": item["chunk_id"]})
    return seed_refs, {
        "mode": mode,
        "cache_hit": None,
        "selected": [
            (
                {"name": item["name"], "type": item["type"]}
                if mode == "entity"
                else {"chunk_id": item["chunk_id"]}
            ) | {"score": item["score"], "rank": item["rank"]}
            for item in selected
        ],
    }
