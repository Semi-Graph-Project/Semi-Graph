"""
Embed relationship triples for Phase C1b+ — HippoRAG v2 alignment.

For each informative Entity-Entity relationship, build a natural-language
triple string "<head> <rel humanized> <tail>" and embed with the BGE model.
The embedding is stored as relationship property `triple_embedding`.

At query time, `online.seed.query_to_triple_seeds()` loads all triples into
memory and does numpy cosine search — see that module for the online path.

Why no Neo4j vector index on relationships:
  Neo4j 5.26 requires explicit relationship TYPE in the index spec
  (`FOR ()-[r:TYPE]-() ...`) and rejects wildcards. Creating 21 separate
  indexes (one per informative type) would force UNION queries across all
  of them at query time — uglier than the in-memory alternative. At 4290
  triples × 768 dims × 4 bytes ≈ 13 MB, a single in-memory matrix + numpy
  dot product is sub-millisecond and infrastructurally simpler.

Why informative-only:
  Provenance edges (MENTIONS, HAS_CHUNK, HAS_SECTION) and SYNONYM_OF carry
  no domain claim — embedding them would only add noise to the triple
  vector space. Same 21 types used by Phase B3 specificity (re-exported).

Why directed match in fetch:
  All FinReflectKG informative relationships are directed (PRODUCES,
  SUPPLIES, COMPETES_WITH...). `(s)-[r]->(t)` returns each rel once;
  `(s)-[r]-(t)` would double-count.

Why text format "head rel tail" (lowercase, spaces):
  BGE-base-en-v1.5 was trained on natural English. Underscore-separated
  enum-style strings like "COMPETES_WITH" sit far from training distribution.
  "competes with" places the relation closer to where a real query lands.
"""
from __future__ import annotations

import time
from typing import Optional

from neo4j import Driver

from semigraph.config import Config, get_config
from semigraph.connections import get_neo4j_driver
from semigraph.offline.embeddings import EmbeddingModel, get_embedding_model
from semigraph.offline.specificity import INFORMATIVE_REL_TYPES


def _fetch_triples_to_embed(driver: Driver, force: bool) -> list[dict]:
    """Pull informative-relationship rows needing embedding.

    Each row: {rid, head, rel_type, tail}. Directed match so each
    relationship is returned exactly once.
    """
    cypher = (
        "MATCH (s:Entity)-[r]->(t:Entity) "
        "WHERE type(r) IN $rel_types "
        "  AND s.name IS NOT NULL "
        "  AND t.name IS NOT NULL "
        + ("" if force else "  AND r.triple_embedding IS NULL ")
        + "RETURN id(r) AS rid, "
          "       s.name AS head, "
          "       type(r) AS rel_type, "
          "       t.name AS tail"
    )
    with driver.session() as s:
        result = s.run(cypher, rel_types=INFORMATIVE_REL_TYPES)
        return [dict(r) for r in result]


def _humanize_rel(rel_type: str) -> str:
    """`COMPETES_WITH` → `'competes with'` — friendlier for BGE."""
    return rel_type.lower().replace("_", " ")


def _build_triple_text(row: dict) -> str:
    return f"{row['head']} {_humanize_rel(row['rel_type'])} {row['tail']}"


def _write_triple_embeddings_batch(driver: Driver, batch: list[dict]) -> None:
    """UNWIND-batch update embeddings keyed on internal relationship id."""
    cypher = """
    UNWIND $rows AS row
    MATCH ()-[r]->()
    WHERE id(r) = row.rid
    SET r.triple_embedding = row.embedding
    """
    with driver.session() as s:
        s.run(cypher, rows=batch)


def embed_triples(
    force: bool = False,
    cfg: Optional[Config] = None,
    model: Optional[EmbeddingModel] = None,
    write_batch: int = 200,
) -> dict:
    """Encode all (or all-missing) informative triples and write back.

    Args:
        force: re-embed even if `triple_embedding` already set
        cfg:   config; defaults to cached singleton
        model: embedding model; defaults to cached singleton (reuses Phase B)
        write_batch: how many triples to UNWIND per Neo4j round-trip

    Returns: stats dict with counts + timing
    """
    cfg = cfg or get_config()
    model = model or get_embedding_model()

    driver = get_neo4j_driver(cfg)
    try:
        rows = _fetch_triples_to_embed(driver, force=force)
        if not rows:
            print("[embed_triples] nothing to embed (use force=True to re-embed)")
            return {"total": 0, "embedded": 0, "elapsed_s": 0.0}

        print(f"[embed_triples] embedding {len(rows)} triples "
              f"(model={cfg.embed_model}, batch={cfg.embed_batch_size})...")

        t0 = time.time()
        texts = [_build_triple_text(r) for r in rows]
        vectors = model.encode(texts)
        embed_elapsed = time.time() - t0
        print(f"[embed_triples] encoded {len(rows)} triples in {embed_elapsed:.1f}s "
              f"({len(rows)/embed_elapsed:.1f} triples/s)")

        t1 = time.time()
        for i in range(0, len(rows), write_batch):
            batch = [
                {"rid": rows[j]["rid"], "embedding": vectors[j].tolist()}
                for j in range(i, min(i + write_batch, len(rows)))
            ]
            _write_triple_embeddings_batch(driver, batch)
            print(f"  [{min(i + write_batch, len(rows))}/{len(rows)}] written")

        write_elapsed = time.time() - t1
        total_elapsed = time.time() - t0
        print(f"[embed_triples] DONE — embed {embed_elapsed:.1f}s + "
              f"write {write_elapsed:.1f}s = {total_elapsed:.1f}s total")

        return {
            "total": len(rows),
            "embedded": len(rows),
            "elapsed_s": total_elapsed,
        }
    finally:
        driver.close()
