#!/usr/bin/env python3
"""Minimal Question -> Embedding -> Neo4j Vector Search workbench."""

from pathlib import Path
import sys

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from semigraph.config import get_config  # noqa: E402
from semigraph.online.vector_search import vector_search as production_vector_search  # noqa: E402


NEO4J_URI = "bolt://localhost:7690"
VECTOR_INDEX = "gold_chunk_embedding"
TOP_K = 5


def vector_search(question: str, top_k: int = TOP_K) -> list[dict]:
    """Use the production vector_search implementation for Gold Chunks."""
    cfg = get_config()
    cfg.neo4j_uri = NEO4J_URI
    return production_vector_search(
        question,
        top_k_chunks=top_k,
        cfg=cfg,
        vector_index=VECTOR_INDEX,
    )


def main() -> None:
    load_dotenv(ROOT / ".env")
    question = input("Question: ").strip()
    if not question:
        return

    results = vector_search(question)
    print(f"\nTop-{len(results)} Chunks from {NEO4J_URI}\n")
    for rank, result in enumerate(results, start=1):
        print(f"#{rank} score={result['score']:.4f}")
        print(result["chunk_id"])
        print(result["text"])
        print("-" * 80)


if __name__ == "__main__":
    main()
