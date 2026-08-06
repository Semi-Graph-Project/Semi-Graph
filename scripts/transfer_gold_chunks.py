#!/usr/bin/env python3
"""Load Gold Chunk JSONL records into the controlled Neo4j database."""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase


ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = ROOT / "data/neo4j/finreflectkg_gold_chunks.jsonl"
NEO4J_URI = "bolt://localhost:7690"


def load_jsonl(path: Path) -> list[dict]:
    """Read one Chunk record from each non-empty JSONL line."""
    with path.open(encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def write_chunks_to_neo4j(chunks: list[dict]) -> None:
    """Merge Chunk records into the controlled Neo4j database."""
    query = """
    UNWIND $chunks AS chunk
    MERGE (c:Chunk {chunk_id: chunk.chunk_id})
    SET c += chunk
    """

    with GraphDatabase.driver(
        NEO4J_URI,
        auth=(os.getenv("NEO4J_USER", "neo4j"), os.environ["NEO4J_PASSWORD"]),
    ) as driver:
        with driver.session() as session:
            session.run(query, chunks=chunks).consume()


def main() -> None:
    load_dotenv(ROOT / ".env")
    chunks = load_jsonl(INPUT_FILE)
    write_chunks_to_neo4j(chunks)
    print(f"Loaded {len(chunks)} Chunks into {NEO4J_URI}")


if __name__ == "__main__":
    main()
