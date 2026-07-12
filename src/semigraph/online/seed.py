
from __future__ import annotations

from functools import lru_cache
from typing import Optional, TypedDict

import numpy as np
from neo4j import Driver

from semigraph.config import Config, get_config
from semigraph.connections import get_neo4j_driver
from semigraph.offline.embeddings import get_embedding_model


# Cypher: $types is either NULL (no filter) or a non-empty LIST<STRING> from
# the FinReflectKG ontology (e.g. ['ORG', 'PRODUCT']). The NULL branch short-
# circuits the IN check so we still get one query plan covering both cases.
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
            if current is None or current["similarity"] < candidate["similarity"]:
                seeds[key] = {
                    "name": name,
                    "type": entity_type,
                    "similarity": candidate["similarity"],
                    "specificity": specificity,
                }

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

    vectors, metadata = _load_triple_index() 
    
    if vectors.shape[0] == 0:
        return []

    sims = vectors @ q_vec  # (N,) cosine similarities
    order = np.argsort(-sims)

    candidates: list[TripleCandidate] = []
    # Dedup head/tail across selected triples, keeping max similarity.
    seeds: dict[tuple[str, str], dict] = {}


    triples_kept = 0
    for idx in order:
        sim = float(sims[idx])
        if sim < min_similarity:
            break  # sorted desc — can stop
        if triples_kept >= top_k_candidates:
            break
        triples_kept += 1
        m = metadata[idx]

        candidates.append({
            "candidate_id": len(candidates),
            "head": metadata[idx]["head"],
            "head_type": metadata[idx]["head_type"],
            "relation": metadata[idx]["rel_type"],
            "tail": metadata[idx]["tail"],
            "tail_type": metadata[idx]["tail_type"],
            "similarity": float(sims[idx]),
            "head_specificity": metadata[idx]["head_spec"],
            "tail_specificity": metadata[idx]["tail_spec"],
        })
    return candidates



def query_to_seeds(
    query: str,
    top_k: int = 5,
    min_similarity: float = 0.6,
    entity_types: Optional[list[str]] = None,
    cfg: Optional[Config] = None,
) -> list[dict]:
    """Find top-k entities most semantically similar to `query`.

    Args:
        query: Natural-language input (typically the user's question).
        top_k: Number of nearest neighbors to fetch from the index.
        min_similarity: Cosine threshold; entities below this are dropped.
        entity_types: Optional whitelist of ontology types (e.g.
            `["ORG", "PRODUCT"]`). Must match graph casing — types in
            FinReflectKG are uppercase. `None` or `[]` means no filter.
        cfg: Optional config override; defaults to the cached singleton.

    Returns:
        List of dicts sorted by similarity descending, each with keys:
        `name`, `type`, `specificity`, `similarity`. Empty list if
        `query` is blank or no entity passes the threshold/filter.

    Raises:
        neo4j.exceptions.* — DB errors propagate so the caller decides
        whether to retry, fallback, or surface to the user.
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


@lru_cache(maxsize=1)
def _load_triple_index(cfg_id: int = 0) -> tuple[np.ndarray, list[dict]]:
    """Load all relationship triples + embeddings into memory once per process.

    Returns:
        (vectors, metadata) where:
          vectors  — (N, 768) float32, L2-normalized (BGE output)
          metadata — list[dict] aligned with vectors, no `embedding` key
    """
    cfg = get_config()
    driver = get_neo4j_driver(cfg)
    try:
        with driver.session() as session:
            rows = list(session.run(_CYPHER_LOAD_TRIPLES))
        if not rows:
            print("[triple_index] EMPTY — run `python scripts/embed_triples.py` first")
            return np.empty((0, cfg.embed_dim), dtype=np.float32), []

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
        return vectors, metadata
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




def query_to_hybrid_seeds(
    query: str,
    top_k_nodes: int = 5,
    top_k_triples: int = 5,
    min_similarity: float = 0.6,
    cfg: Optional[Config] = None,
) -> list[dict]:
    """Union of Query-to-Node (Phase C1a) and Query-to-Triple (Phase C1b+) seeds.

    HippoRAG v2 paper ablation (Table 4) reports Query-to-Triple alone beats
    Query-to-Node by +12.5% R@5 on multi-hop QA, but acknowledges both paths
    surface complementary signal: node embeddings catch entities whose
    descriptive name matches the query verbatim, triple embeddings catch
    entities embedded in relational context. Merging recovers both — at the
    cost of running two index lookups per query.

    For abstract queries where the answer entity has a short, undescriptive
    name (e.g. "tsmc" vs query "leading pure-play semiconductor foundry"),
    neither path may surface the target directly, but the union still gives
    PPR a richer starting distribution than either path alone.

    Args:
        query: Natural-language input.
        top_k_nodes:   Top-k entities from `query_to_seeds`.
        top_k_triples: Top-k triples from `query_to_triple_seeds`.
        min_similarity: Cosine threshold applied to both paths.
        cfg: Optional config override.

    Returns:
        Deduplicated seed list `[{name, type, specificity, similarity}, ...]`,
        sorted by similarity descending. Same shape as the two source
        functions — drop-in for `run_ppr`.
    """
    if not query.strip():
        return []

    node_seeds = query_to_seeds(
        query, top_k=top_k_nodes, min_similarity=min_similarity, cfg=cfg
    )
    triple_seeds = query_to_triple_seeds(
        query, top_k_triples=top_k_triples, min_similarity=min_similarity, cfg=cfg
    )

    merged: dict[tuple[str, str], dict] = {}
    for s in node_seeds + triple_seeds:
        key = (s["name"], s["type"])
        existing = merged.get(key)
        if existing is None or existing["similarity"] < s["similarity"]:
            merged[key] = s

    print(f"[hybrid_seed] {len(node_seeds)} node + {len(triple_seeds)} triple "
          f"-> {len(merged)} unique seeds")
    return sorted(merged.values(), key=lambda s: -s["similarity"])


if __name__ == "__main__":
    def _show(label: str, seeds: list[dict]) -> None:
        print(f"\n{label} → {len(seeds)} seeds:")
        for s in seeds:
            print(f"  sim={s['similarity']:.4f}  spec={s['specificity']:.3f}  "
                  f"{s['name']:30s} ({s['type']})")

    _show("[node-mode] query='AMD' (no filter)", query_to_seeds("AMD"))
    _show("[node-mode] query='AMD' types=['ORG']",
          query_to_seeds("AMD", entity_types=["ORG"]))
    _show("[node-mode] query='random xyz noise' (off-topic, expect empty)",
          query_to_seeds("random xyz noise qwerty zzz"))

    print("\n" + "=" * 50)
    _show("[triple-mode] query='AMD'", query_to_triple_seeds("AMD"))
    _show("[triple-mode] query='TSMC supply chain'",
          query_to_triple_seeds("TSMC supply chain"))
    _show("[triple-mode] query='china semiconductor ban'",
          query_to_triple_seeds("china semiconductor ban"))
    _show("[triple-mode] query='random xyz noise' (off-topic, expect empty)",
          query_to_triple_seeds("random xyz noise qwerty zzz"))
