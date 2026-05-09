"""
Embed Entity nodes for Phase B2 — Step 1.

Encodes `entity.name` with the BGE embedding model and writes the vector back
to the same node as `embedding` (List[float], dim 768). Idempotent — entities
that already have an embedding are skipped unless `force=True`.

After embedding, ensures the vector index `entity_embedding` exists (cosine,
HNSW). The index lets Phase B2 Step 2 (synonymy) run nearest-neighbor lookups
for cross-checking instead of computing the full pairwise matrix every run.

Why encode just `name` (not name+context):
  Synonymy asks "do these refer to the same real-world thing?" — the answer
  is in the name. Encoding context would make the same name appearing in
  different sections look dissimilar, which defeats the goal.

Why Entity uses the composite key (name, type):
  KGStore.MERGE keys on (name, type). Two nodes with same name but different
  type are intentionally distinct, so we batch-update by both keys.
"""
from __future__ import annotations

import time
from typing import Optional

from neo4j import Driver

from semigraph.config import Config, get_config
from semigraph.connections import get_neo4j_driver
from semigraph.offline.embeddings import EmbeddingModel, get_embedding_model


VECTOR_INDEX_NAME = "entity_embedding"


def ensure_entity_vector_index(driver: Driver, cfg: Optional[Config] = None) -> None:
    """Create cosine vector index on Entity(embedding) if not exists."""
    cfg = cfg or get_config()
    cypher = f"""
    CREATE VECTOR INDEX {VECTOR_INDEX_NAME} IF NOT EXISTS
    FOR (e:Entity) ON (e.embedding)
    OPTIONS {{
      indexConfig: {{
        `vector.dimensions`: {cfg.embed_dim},
        `vector.similarity_function`: 'cosine'
      }}
    }}
    """
    with driver.session() as s:
        s.run(cypher)
    print(f"[embed_nodes] vector index '{VECTOR_INDEX_NAME}' ready (dim={cfg.embed_dim}, cosine)")


def _fetch_entities_to_embed(driver: Driver, force: bool) -> list[dict]:
    """Pull entities needing embedding. Returns list of {name, type}."""
    cypher = (
        "MATCH (e:Entity) "
        "WHERE e.name IS NOT NULL "
        + ("" if force else "AND e.embedding IS NULL ")
        + "RETURN e.name AS name, e.type AS type"
    )
    with driver.session() as s:
        result = s.run(cypher)
        return [dict(r) for r in result]


def _write_entity_embeddings_batch(driver: Driver, batch: list[dict]) -> None:
    """UNWIND-batch update embeddings keyed on composite (name, type)."""
    cypher = """
    UNWIND $rows AS row
    MATCH (e:Entity {name: row.name, type: row.type})
    SET e.embedding = row.embedding
    """
    with driver.session() as s:
        s.run(cypher, rows=batch)


def embed_entities(
    force: bool = False,
    cfg: Optional[Config] = None,
    model: Optional[EmbeddingModel] = None,
    write_batch: int = 200,
) -> dict:
    """
    Encode all (or all-missing) Entity nodes and write embeddings back.

    Args:
        force: re-embed even if `embedding` already set
        cfg:   config; defaults to cached singleton
        model: embedding model; defaults to cached singleton (reuses Phase B1)
        write_batch: how many entities to UNWIND per Neo4j round-trip

    Returns: stats dict with counts + timing
    """
    cfg = cfg or get_config()
    model = model or get_embedding_model()

    driver = get_neo4j_driver(cfg)
    try:
        ensure_entity_vector_index(driver, cfg)

        rows = _fetch_entities_to_embed(driver, force=force)
        if not rows:
            print("[embed_nodes] nothing to embed (use force=True to re-embed)")
            return {"total": 0, "embedded": 0, "elapsed_s": 0.0}

        print(f"[embed_nodes] embedding {len(rows)} entities "
              f"(model={cfg.embed_model}, batch={cfg.embed_batch_size})...")

        t0 = time.time()
        names = [r["name"] for r in rows]
        vectors = model.encode(names)              # (N, 768) float32
        embed_elapsed = time.time() - t0
        print(f"[embed_nodes] encoded {len(rows)} entities in {embed_elapsed:.1f}s "
              f"({len(rows)/embed_elapsed:.1f} entities/s)")

        # Write back in mini-batches for failure isolation
        t1 = time.time()
        for i in range(0, len(rows), write_batch):
            batch = [
                {
                    "name": rows[j]["name"],
                    "type": rows[j]["type"],
                    "embedding": vectors[j].tolist(),
                }
                for j in range(i, min(i + write_batch, len(rows)))
            ]
            _write_entity_embeddings_batch(driver, batch)
            print(f"  [{min(i + write_batch, len(rows))}/{len(rows)}] written")

        write_elapsed = time.time() - t1
        total_elapsed = time.time() - t0
        print(f"[embed_nodes] DONE — embed {embed_elapsed:.1f}s + "
              f"write {write_elapsed:.1f}s = {total_elapsed:.1f}s total")

        return {
            "total": len(rows),
            "embedded": len(rows),
            "elapsed_s": total_elapsed,
        }
    finally:
        driver.close()
