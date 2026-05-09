"""
Embed Chunk nodes and create the Neo4j vector index.

Reads `text` from Chunk nodes, encodes with `EmbeddingModel`, writes back to
the same node as `embedding` (list[float], dim 768 by default). Idempotent —
chunks that already have an embedding are skipped unless `force=True`.

After embedding, ensures the vector index exists for cosine similarity search.

Used by `scripts/embed_chunks.py` (CLI) and importable for tests.
"""
from __future__ import annotations

import time
from typing import Optional

from neo4j import Driver

from semigraph.config import Config, get_config
from semigraph.connections import get_neo4j_driver
from semigraph.offline.embeddings import EmbeddingModel, get_embedding_model


VECTOR_INDEX_NAME = "chunk_embedding"


def ensure_chunk_vector_index(driver: Driver, cfg: Optional[Config] = None) -> None:
    """Create the cosine vector index on Chunk(embedding) if it doesn't exist."""
    cfg = cfg or get_config()
    cypher = f"""
    CREATE VECTOR INDEX {VECTOR_INDEX_NAME} IF NOT EXISTS
    FOR (c:Chunk) ON (c.embedding)
    OPTIONS {{
      indexConfig: {{
        `vector.dimensions`: {cfg.embed_dim},
        `vector.similarity_function`: 'cosine'
      }}
    }}
    """
    with driver.session() as s:
        s.run(cypher)
    print(f"[embed_chunks] vector index '{VECTOR_INDEX_NAME}' ready (dim={cfg.embed_dim}, cosine)")


def _fetch_chunks_to_embed(driver: Driver, force: bool, batch_size: int) -> list[dict]:
    """Pull chunks needing embedding. Returns list of {chunk_id, text}."""
    cypher = (
        "MATCH (c:Chunk) "
        "WHERE c.text IS NOT NULL "
        + ("" if force else "AND c.embedding IS NULL ")
        + "RETURN c.chunk_id AS chunk_id, c.text AS text"
    )
    with driver.session() as s:
        result = s.run(cypher)
        return [dict(r) for r in result]


def _write_embeddings_batch(driver: Driver, batch: list[dict]) -> None:
    """UNWIND-batch update embeddings on the matching chunks."""
    cypher = """
    UNWIND $rows AS row
    MATCH (c:Chunk {chunk_id: row.chunk_id})
    SET c.embedding = row.embedding
    """
    with driver.session() as s:
        s.run(cypher, rows=batch)


def embed_chunks(
    force: bool = False,
    cfg: Optional[Config] = None,
    model: Optional[EmbeddingModel] = None,
    write_batch: int = 100,
) -> dict:
    """
    Encode all (or all-missing) Chunk nodes and write embeddings back.

    Args:
        force: re-embed even if `embedding` already set
        cfg:   config; defaults to cached singleton
        model: embedding model; defaults to cached singleton
        write_batch: how many chunks to UNWIND per Neo4j round-trip

    Returns: stats dict with counts + timing
    """
    cfg = cfg or get_config()
    model = model or get_embedding_model()

    driver = get_neo4j_driver(cfg)
    try:
        ensure_chunk_vector_index(driver, cfg)

        rows = _fetch_chunks_to_embed(driver, force=force, batch_size=write_batch)
        if not rows:
            print("[embed_chunks] nothing to embed (use force=True to re-embed)")
            return {"total": 0, "embedded": 0, "elapsed_s": 0.0}

        print(f"[embed_chunks] embedding {len(rows)} chunks "
              f"(model={cfg.embed_model}, batch={cfg.embed_batch_size})...")

        t0 = time.time()
        texts = [r["text"] for r in rows]
        vectors = model.encode(texts)              # (N, 768) float32

        embed_elapsed = time.time() - t0
        print(f"[embed_chunks] encoded {len(rows)} chunks in {embed_elapsed:.1f}s "
              f"({len(rows)/embed_elapsed:.1f} chunks/s)")

        # Write back in mini-batches so a single failure doesn't lose everything
        t1 = time.time()
        for i in range(0, len(rows), write_batch):
            batch = [
                {"chunk_id": rows[j]["chunk_id"], "embedding": vectors[j].tolist()}
                for j in range(i, min(i + write_batch, len(rows)))
            ]
            _write_embeddings_batch(driver, batch)
            print(f"  [{min(i + write_batch, len(rows))}/{len(rows)}] written")

        write_elapsed = time.time() - t1
        total_elapsed = time.time() - t0
        print(f"[embed_chunks] DONE — embed {embed_elapsed:.1f}s + "
              f"write {write_elapsed:.1f}s = {total_elapsed:.1f}s total")

        return {
            "total": len(rows),
            "embedded": len(rows),
            "elapsed_s": total_elapsed,
        }
    finally:
        driver.close()
