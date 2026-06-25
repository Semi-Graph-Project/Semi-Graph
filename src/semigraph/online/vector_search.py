"""
Phase C2 — vector_search: vanilla chunk vector retrieval (Homogeneous RAG baseline).

Output shape matches `graph_search()` exactly so Phase E ablation A/B works
without format conversion. No similarity threshold — top-k always returns k.
"""
from __future__ import annotations

from typing import Optional

from neo4j import Driver

from semigraph.config import Config, get_config
from semigraph.connections import get_neo4j_driver
from semigraph.offline.embeddings import get_embedding_model


_CYPHER_VECTOR_SEARCH = """
CALL db.index.vector.queryNodes('chunk_embedding', $top_k, $vec)
YIELD node, score
RETURN node.chunk_id    AS chunk_id,
       node.text        AS text,
       node.ticker      AS ticker,
       node.fiscal_year AS fiscal_year,
       node.section     AS section,
       score
ORDER BY score DESC, chunk_id ASC
"""


def vector_search(
    query: str,
    top_k_chunks: int = 5,
    cfg: Optional[Config] = None,
) -> list[dict]:
    """Top-k chunk cosine search via `chunk_embedding` index.

    Args:
        query: Natural-language question.
        top_k_chunks: Number of chunks to return.
        cfg: Optional Config; defaults to cached singleton.

    Returns:
        `[{chunk_id, text, ticker, fiscal_year, section, score}, ...]` —
        shape identical to `graph_search()`. Empty list if query is blank.
    """
    if not query.strip():
        return []

    cfg = cfg or get_config()
    model = get_embedding_model()
    vec = model.encode([query])[0].tolist()

    driver: Driver = get_neo4j_driver(cfg)
    try:
        with driver.session() as session:
            result = session.run(
                _CYPHER_VECTOR_SEARCH,
                top_k=top_k_chunks,
                vec=vec,
            )
            return result.data()
    finally:
        driver.close()


if __name__ == "__main__":
    for q in [
        "AMD",
        "TSMC supply chain",
        "china semiconductor ban",
        "Hopper data center segment revenue",
        "qwerty zzz random nonsense",
    ]:
        print(f"\n--- Query: {q!r} ---")
        for i, ch in enumerate(vector_search(q, top_k_chunks=3), start=1):
            preview = ch["text"][:120].replace("\n", " ")
            print(f"  #{i}  score={ch['score']:.3f}  "
                  f"[{ch['ticker']} FY{ch['fiscal_year']} {ch['section']}]")
            print(f"      └─ {preview}...")

        print("RAW:", vector_search(q, top_k_chunks=5))
