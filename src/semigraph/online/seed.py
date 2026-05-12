"""
Query → seed entities via vector index — Phase C1a.

Embed a natural-language query with the same BGE model used in Phase B2,
then look up nearest entities in the `entity_embedding` vector index.
Output is the input layer for Personalized PageRank (Phase C1b): each seed
carries its own `specificity` (from Phase B3) so the walker can weight
initial mass without an extra round-trip.

Only handles vector-based seeding. Synonym expansion via `:SYNONYM_OF`
edges is the responsibility of the downstream PPR step, not this module.
"""
from __future__ import annotations

from typing import Optional

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


if __name__ == "__main__":
    def _show(label: str, seeds: list[dict]) -> None:
        print(f"\n{label} → {len(seeds)} seeds:")
        for s in seeds:
            print(f"  sim={s['similarity']:.4f}  spec={s['specificity']:.3f}  "
                  f"{s['name']:30s} ({s['type']})")

    _show("query='AMD' (no filter)", query_to_seeds("AMD"))
    _show("query='AMD' types=['PRODUCT']",
          query_to_seeds("AMD", entity_types=["PRODUCT"]))
    _show("query='AMD' types=['ORG']",
          query_to_seeds("AMD", entity_types=["ORG"]))
    _show("query='random xyz noise' (off-topic, expect empty)",
          query_to_seeds("random xyz noise qwerty zzz"))
