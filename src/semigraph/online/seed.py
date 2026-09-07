
from __future__ import annotations

from typing import Optional, TypedDict

import numpy as np
from neo4j import Driver

from semigraph.config import Config, get_config
from semigraph.connections import get_neo4j_driver
from semigraph.offline.embeddings import get_embedding_model
from semigraph.online.vector_search import DEFAULT_VECTOR_INDEX, vector_search


_CYPHER_SEED_QUERY = """
CALL db.index.vector.queryNodes('entity_embedding', $top_k, $vec)
YIELD node, score
WHERE score >= $min_sim
  AND ($types IS NULL OR node.type IN $types)
RETURN node.name AS name,
       node.type AS type,
       node.specificity AS specificity,
       score AS similarity
ORDER BY score DESC
"""

class TripleCandidate(TypedDict):
    candidate_id: int
    head: str
    head_type: str
    relation: str
    tail: str
    tail_type: str
    similarity: float
    head_specificity: float
    tail_specificity: float

def triple_candidates_to_seeds(
    candidates: list[TripleCandidate],
) -> list[dict]:
    seeds: dict[tuple[str, str], dict] = {}

    for candidate in candidates:
        for role in ("head", "tail"):
            name = candidate[role]
            entity_type = candidate[f"{role}_type"]
            specificity = candidate[f"{role}_specificity"]
            key = (name, entity_type)

            current = seeds.get(key)
            if current is None:
                seeds[key] = {
                    "name": name,
                    "type": entity_type,
                    "similarity": candidate["similarity"],
                    "specificity": specificity,
                    "triple_similarities": [candidate["similarity"]],
                }
                continue

            current["triple_similarities"].append(candidate["similarity"])
            if current["similarity"] < candidate["similarity"]:
                current["similarity"] = candidate["similarity"]
                current["specificity"] = specificity

    return sorted(seeds.values(), key=lambda seed: -seed["similarity"])


def query_to_triple_candidates(
        query: str,
        top_k_candidates: int = 10,
        min_similarity: float = 0.6,
        cfg: Optional[Config] = None,
    ) -> list[TripleCandidate]:

    if not query.strip():
        return []

    cfg = cfg or get_config()
    model = get_embedding_model()
    q_vec = model.encode([query])[0].astype(np.float32)

    vectors, metadata = _load_triple_index(cfg)
    
    if vectors.shape[0] == 0:
        return []

    sims = vectors @ q_vec  # (N,) cosine similarities
    order = np.argsort(-sims)

    candidates: list[TripleCandidate] = []
    seen_triples: set[tuple[str, str, str, str, str]] = set()
    for idx in order:
        sim = float(sims[idx])
        if sim < min_similarity:
            break  # sorted desc — can stop
        if len(candidates) >= top_k_candidates:
            break
        m = metadata[idx]
        triple_key = (
            m["head"],
            m["head_type"],
            m["rel_type"],
            m["tail"],
            m["tail_type"],
        )
        if triple_key in seen_triples:
            continue
        seen_triples.add(triple_key)

        candidates.append({
            "candidate_id": len(candidates),
            "head": m["head"],
            "head_type": m["head_type"],
            "relation": m["rel_type"],
            "tail": m["tail"],
            "tail_type": m["tail_type"],
            "similarity": sim,
            "head_specificity": m["head_spec"],
            "tail_specificity": m["tail_spec"],
        })
    return candidates



def query_to_seeds(
    query: str,
    top_k: int = 5,
    min_similarity: float = 0.6,
    entity_types: Optional[list[str]] = None,
    cfg: Optional[Config] = None,
) -> list[dict]:
    """Find top-k entities most semantically similar to `query
    """
    if not query.strip():
        return []

    cfg = cfg or get_config()
    model = get_embedding_model()

    # BGE returns shape (1, 768) numpy; index 0 + tolist() to satisfy Bolt protocol.
    vec_list = model.encode([query])[0].tolist()

    # Empty list is treated the same as None — pass NULL so the Cypher
    # short-circuit branch hits and the planner skips the IN check entirely.
    types_param = entity_types if entity_types else None

    driver: Driver = get_neo4j_driver(cfg)
    try:
        print(f"[seed] query='{query}' top_k={top_k} min_sim={min_similarity} "
              f"types={types_param}")
        with driver.session() as session:
            result = session.run(
                _CYPHER_SEED_QUERY,
                top_k=top_k,
                vec=vec_list,
                min_sim=min_similarity,
                types=types_param,
            )
            return result.data()
    finally:
        driver.close()


def query_to_chunk_seeds(
    query: str,
    top_k: int = 5,
    vector_index: str = DEFAULT_VECTOR_INDEX,
    cfg: Optional[Config] = None,
) -> list[dict]:
    """Use vector-ranked Chunks as the starting nodes for passage PPR."""
    if not query.strip() or top_k <= 0:
        return []

    chunks = vector_search(
        query,
        top_k_chunks=top_k,
        candidate_pool_k=top_k,
        vector_index=vector_index,
        cfg=cfg,
    )
    return [
        {
            "chunk_id": chunk["chunk_id"],
            "similarity": float(chunk["score"]),
            "specificity": 1.0,
        }
        for chunk in chunks
    ]


_CYPHER_LOAD_TRIPLES = """
MATCH (s:Entity)-[r]->(t:Entity)
WHERE r.triple_embedding IS NOT NULL
RETURN s.name AS head,
       s.type AS head_type,
       s.specificity AS head_spec,
       type(r) AS rel_type,
       t.name AS tail,
       t.type AS tail_type,
       t.specificity AS tail_spec,
       r.triple_embedding AS embedding
"""


_TRIPLE_INDEX_CACHE: dict[
    tuple[str, str, int], tuple[np.ndarray, list[dict]]
] = {}


def _load_triple_index(cfg: Optional[Config] = None) -> tuple[np.ndarray, list[dict]]:
    """Load relationship triples once per Neo4j backend in this process.

    Returns:
        (vectors, metadata) where:
          vectors  — (N, 768) float32, L2-normalized (BGE output)
          metadata — list[dict] aligned with vectors, no `embedding` key
    """
    cfg = cfg or get_config()
    cache_key = (cfg.neo4j_uri, cfg.neo4j_user, cfg.embed_dim)
    cached = _TRIPLE_INDEX_CACHE.get(cache_key)
    if cached is not None:
        return cached

    driver = get_neo4j_driver(cfg)
    try:
        with driver.session() as session:
            rows = list(session.run(_CYPHER_LOAD_TRIPLES))
        if not rows:
            print("[triple_index] EMPTY — run `python scripts/embed_triples.py` first")
            result = (np.empty((0, cfg.embed_dim), dtype=np.float32), [])
            _TRIPLE_INDEX_CACHE[cache_key] = result
            return result

        vectors = np.asarray(
            [row["embedding"] for row in rows], dtype=np.float32
        )
        metadata = [
            {
                "head": row["head"],
                "head_type": row["head_type"],
                "head_spec": row["head_spec"] if row["head_spec"] is not None else 1.0,
                "rel_type": row["rel_type"],
                "tail": row["tail"],
                "tail_type": row["tail_type"],
                "tail_spec": row["tail_spec"] if row["tail_spec"] is not None else 1.0,
            }
            for row in rows
        ]
        mb = vectors.nbytes / (1024 * 1024)
        print(f"[triple_index] loaded {len(rows)} triples ({mb:.1f} MB)")
        result = (vectors, metadata)
        _TRIPLE_INDEX_CACHE[cache_key] = result
        return result
    finally:
        driver.close()


def query_to_triple_seeds(
    query: str,
    top_k_candidates: int = 10,
    min_similarity: float = 0.6,
    cfg: Optional[Config] = None,
) -> list[dict]:
    candidates = query_to_triple_candidates(
        query, 
        top_k_candidates=top_k_candidates, 
        min_similarity=min_similarity, 
        cfg=cfg
    )
    return triple_candidates_to_seeds(candidates)