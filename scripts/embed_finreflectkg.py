#!/usr/bin/env python3
"""Batch-embed FinReflectKG Chunk and Entity nodes in the isolated database."""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from semigraph.config import get_config  # noqa: E402
from semigraph.offline.embeddings import get_embedding_model  # noqa: E402


FETCH = {
    "chunks": """
        MATCH (n:Chunk)
        WHERE n.text IS NOT NULL AND n.embedding IS NULL
        RETURN n.chunk_id AS key, n.text AS text
        LIMIT $limit
    """,
    "entities": """
        MATCH (n:Entity)
        WHERE n.name IS NOT NULL AND n.embedding IS NULL
        RETURN n.name AS name, n.type AS type, n.name AS text
        LIMIT $limit
    """,
}

WRITE = {
    "chunks": """
        UNWIND $rows AS row
        MATCH (n:Chunk {chunk_id: row.key})
        SET n.embedding = row.embedding,
            n.embedding_model = $model
    """,
    "entities": """
        UNWIND $rows AS row
        MATCH (n:Entity {name: row.name, type: row.type})
        SET n.embedding = row.embedding,
            n.embedding_model = $model
    """,
}


def _ensure_indexes(session, dimensions: int) -> None:
    session.run(f"""
        CREATE VECTOR INDEX chunk_embedding IF NOT EXISTS
        FOR (c:Chunk) ON (c.embedding)
        OPTIONS {{indexConfig: {{
          `vector.dimensions`: {dimensions},
          `vector.similarity_function`: 'cosine'
        }}}}
    """).consume()
    session.run(f"""
        CREATE VECTOR INDEX entity_embedding IF NOT EXISTS
        FOR (e:Entity) ON (e.embedding)
        OPTIONS {{indexConfig: {{
          `vector.dimensions`: {dimensions},
          `vector.similarity_function`: 'cosine'
        }}}}
    """).consume()


def _embed_kind(session, kind: str, model, model_name: str, batch_size: int) -> int:
    total = 0
    while True:
        rows = session.run(FETCH[kind], limit=batch_size).data()
        if not rows:
            break
        vectors = model.encode([row["text"] for row in rows])
        if kind == "chunks":
            payload = [
                {"key": row["key"], "embedding": vectors[index].tolist()}
                for index, row in enumerate(rows)
            ]
        else:
            payload = [
                {
                    "name": row["name"],
                    "type": row["type"],
                    "embedding": vectors[index].tolist(),
                }
                for index, row in enumerate(rows)
            ]
        session.run(WRITE[kind], rows=payload, model=model_name).consume()
        total += len(rows)
        print(f"[embed] {kind}={total}")
    return total


def main() -> None:
    load_dotenv(ROOT / ".env")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--neo4j-uri", default=os.getenv("FINREFLECTKG_NEO4J_URI", "bolt://localhost:7688"))
    parser.add_argument("--neo4j-user", default=os.getenv("NEO4J_USER", "neo4j"))
    parser.add_argument("--neo4j-password", default=os.getenv("NEO4J_PASSWORD", ""))
    parser.add_argument("--kinds", nargs="+", choices=("chunks", "entities"), default=["chunks", "entities"])
    parser.add_argument("--chunk-batch-size", type=int, default=32)
    parser.add_argument("--entity-batch-size", type=int, default=512)
    args = parser.parse_args()
    if not args.neo4j_password:
        parser.error("NEO4J_PASSWORD is required")

    cfg = get_config()
    model = get_embedding_model()
    driver = GraphDatabase.driver(
        args.neo4j_uri,
        auth=(args.neo4j_user, args.neo4j_password),
    )
    started = time.time()
    totals = {}
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            for kind in args.kinds:
                batch_size = (
                    args.chunk_batch_size if kind == "chunks" else args.entity_batch_size
                )
                totals[kind] = _embed_kind(
                    session,
                    kind,
                    model,
                    cfg.embed_model,
                    batch_size,
                )
            _ensure_indexes(session, cfg.embed_dim)
            session.run("CALL db.awaitIndexes(300)").consume()
            status = session.run("""
                MATCH (c:Chunk)
                WITH count(c) AS chunks, count(c.embedding) AS chunk_embeddings
                MATCH (e:Entity)
                RETURN chunks, chunk_embeddings,
                       count(e) AS entities, count(e.embedding) AS entity_embeddings
            """).single().data()
    finally:
        driver.close()

    print({
        "embedded": totals,
        "status": status,
        "model": cfg.embed_model,
        "dimensions": cfg.embed_dim,
        "elapsed_seconds": round(time.time() - started, 3),
    })


if __name__ == "__main__":
    main()
