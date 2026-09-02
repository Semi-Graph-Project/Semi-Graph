#!/usr/bin/env python3
"""Sample non-Gold FinReflectKG Chunks from Neo4j and write JSONL."""

from pathlib import Path
import json
import random
import sys

from dotenv import load_dotenv
import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from semigraph.config import get_config  # noqa: E402
from semigraph.connections import get_neo4j_driver  # noqa: E402


SAMPLE_SIZE = 500
RANDOM_SEED = 42
DATASET_FILE = ROOT / "benchmark/freezes/sox74_retrieval_ablation_v1/inputs/finreflectkg_sox_strict74.yaml"
OUTPUT_FILE = ROOT / "data/neo4j/finreflectkg_distractor_500_chunks.jsonl"


def load_gold_ids() -> set[str]:
    """Load every Gold Chunk ID from the SOX benchmark YAML."""
    dataset = yaml.safe_load(DATASET_FILE.read_text(encoding="utf-8"))
    return {
        chunk_id
        for query in dataset["queries"]
        for chunk_id in query["gold_chunks"]
    }


def fetch_non_gold_chunks(gold_ids: set[str]) -> list[dict]:
    """Fetch all Chunk properties whose IDs are not Gold IDs."""
    cfg = get_config()
    cfg.neo4j_uri = cfg.finreflectkg_neo4j_uri
    driver = get_neo4j_driver(cfg)
    try:
        with driver.session() as session:
            rows = session.run(
                """
                MATCH (c:Chunk)
                WHERE NOT c.chunk_id IN $gold_ids
                RETURN properties(c) AS chunk
                ORDER BY c.chunk_id
                """,
                gold_ids=sorted(gold_ids),
            ).data()
    finally:
        driver.close()
    return [row["chunk"] for row in rows]


def write_jsonl(chunks: list[dict]) -> None:
    """Write one Chunk object per JSONL line."""
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        for chunk in chunks:
            file.write(json.dumps(chunk, ensure_ascii=False) + "\n")


def main() -> None:
    load_dotenv(ROOT / ".env")
    gold_ids = load_gold_ids()
    candidates = fetch_non_gold_chunks(gold_ids)
    if len(candidates) < SAMPLE_SIZE:
        raise ValueError(
            f"Only {len(candidates)} non-Gold Chunks available; "
            f"cannot sample {SAMPLE_SIZE}"
        )

    sampled = random.Random(RANDOM_SEED).sample(candidates, SAMPLE_SIZE)
    sampled.sort(key=lambda chunk: chunk["chunk_id"])
    write_jsonl(sampled)
    print(
        f"Wrote {len(sampled)} distractor Chunks to {OUTPUT_FILE} "
        f"(seed={RANDOM_SEED}, gold_ids={len(gold_ids)})"
    )


if __name__ == "__main__":
    main()
