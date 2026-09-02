#!/usr/bin/env python3
"""Load Gold Chunk JSONL records into the controlled Neo4j database."""

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from semigraph.config import get_config  # noqa: E402
from semigraph.connections import get_neo4j_driver  # noqa: E402


INPUT_FILE = ROOT / "data/neo4j/finreflectkg_gold_chunks.jsonl"
DISTRACTOR_INPUT_FILE = ROOT / "data/neo4j/finreflectkg_distractor_820_chunks.jsonl"


def controlled_driver():
    """Return a driver pointed at the controlled evaluation database."""
    cfg = get_config()
    cfg.neo4j_uri = cfg.controlled_neo4j_uri
    return get_neo4j_driver(cfg)


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

    with controlled_driver() as driver:
        with driver.session() as session:
            session.run(query, chunks=chunks).consume()


def write_distractor() -> int:
    """Load Distractor Chunks and mark them before writing to Neo4j."""
    chunks = load_jsonl(DISTRACTOR_INPUT_FILE)
    query = """
    UNWIND $chunks AS chunk
    MERGE (c:Chunk {chunk_id: chunk.chunk_id})
    SET c += chunk,
        c.is_distractor = true
    """

    with controlled_driver() as driver:
        with driver.session() as session:
            session.run(query, chunks=chunks).consume()
    return len(chunks)


def main() -> None:
    chunks = load_jsonl(INPUT_FILE)
    write_chunks_to_neo4j(chunks)
    distractor_count = write_distractor()
    uri = get_config().controlled_neo4j_uri
    print(f"Loaded {len(chunks)} Gold Chunks into {uri}")
    print(f"Loaded {distractor_count} Distractor Chunks into {uri}")


if __name__ == "__main__":
    main()
