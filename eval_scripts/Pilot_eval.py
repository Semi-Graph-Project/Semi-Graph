#!/usr/bin/env python3
"""Controlled-corpus pilot: load Chunks from Neo4j and extract KG data.

This pilot reads the controlled corpus, sends each Chunk to ``extract_chunk``
with the complete FinReflectKG domain ontology, and writes only the extracted
Entity nodes and ``MENTIONS`` edges from the existing Chunk.

Usage:
    # Confirm that all controlled Chunks can be loaded from Neo4j 7690
    python eval_scripts/Pilot_eval.py --load-only

    # Extract and store every Chunk (LLM calls + graph writes)
    python eval_scripts/Pilot_eval.py

    # Re-extract only Gold Chunks missing MENTIONS or a domain relation
    python eval_scripts/Pilot_eval.py --problem-gold

    # Run a small pilot before the full corpus
    python eval_scripts/Pilot_eval.py --limit 5

    # Extract without writing to Neo4j
    python eval_scripts/Pilot_eval.py --limit 5 --extract-only
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv
import yaml


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from semigraph.config import get_config  # noqa: E402
from semigraph.connections import get_llm, get_neo4j_driver  # noqa: E402
from semigraph.offline.chunker import Chunk  # noqa: E402
from semigraph.offline.kg_extract import extract_chunk  # noqa: E402
from semigraph.offline.kg_store import KGStore, init_schema  # noqa: E402
from semigraph.ontology.nodes import GraphExtractionResult  # noqa: E402
from semigraph.ontology.schema import FULL_ONTOLOGY  # noqa: E402


SOX_DATASET = ROOT / "benchmark/freezes/sox74_retrieval_ablation_v1/inputs/finreflectkg_sox_strict74.yaml"


def load_gold_chunk_ids() -> list[str]:
    """Return the unique Gold Chunk IDs from the frozen SOX dataset."""
    with SOX_DATASET.open(encoding="utf-8") as file:
        dataset = yaml.safe_load(file)

    return sorted({
        str(chunk_id)
        for query in dataset["queries"]
        for chunk_id in query.get("gold_chunks", [])
    })


def load_chunks(
    limit: int | None = None,
    problem_gold: bool = False,
) -> list[Chunk]:
    """Load unprocessed Chunks or Gold Chunks with incomplete graph output."""
    cfg = controlled_config()

    if problem_gold:
        query = """
        MATCH (c:Chunk)
        WHERE c.chunk_id IN $gold_ids
          AND (
            NOT (c)-[:MENTIONS]->(:Entity)
            OR NOT EXISTS {
              MATCH (:Entity)-[r]->(:Entity)
              WHERE r.source_chunk = c.chunk_id
                AND type(r) <> 'SYNONYM_OF'
            }
          )
        """
        params = {"gold_ids": load_gold_chunk_ids()}
    else:
        query = """
        MATCH (c:Chunk)
        WHERE NOT (c)-[:MENTIONS]->(:Entity)
        """
        params = {}

    query += """
    RETURN c.chunk_id AS chunk_id,
           c.ticker AS ticker,
           toString(c.fiscal_year) AS fiscal_year,
           c.filing_type AS filing_type,
           c.section AS section,
           c.text AS text,
           c.char_count AS char_count,
           c.token_estimate AS token_estimate
    ORDER BY c.chunk_id
    """
    if limit is not None:
        query += "LIMIT $limit"
        params["limit"] = limit

    driver = get_neo4j_driver(cfg)
    try:
        with driver.session() as session:
            rows = session.run(query, **params).data()
    finally:
        driver.close()

    return [Chunk(**row) for row in rows]


def controlled_config():
    """Return the project config pointed explicitly at the controlled database."""
    cfg = get_config()
    cfg.neo4j_uri = cfg.controlled_neo4j_uri
    return cfg


def extract_chunks(
    chunks: list[Chunk],
    llm,
    store: KGStore | None = None,
) -> list[tuple[Chunk, GraphExtractionResult]]:
    """Extract each Chunk and optionally store chunk-level graph output."""
    extracted: list[tuple[Chunk, GraphExtractionResult]] = []

    for position, chunk in enumerate(chunks, start=1):
        try:
            result = extract_chunk(
                text=chunk.text,
                section=FULL_ONTOLOGY,
                llm=llm,
                chunk_id=chunk.chunk_id,
                filer_ticker=chunk.ticker,
            )
        except Exception as exc:
            print(f"[{position}/{len(chunks)}] {chunk.chunk_id} | error={type(exc).__name__}")
            continue
        extracted.append((chunk, result))

        stored = ""
        if store is not None:
            if result.nodes:
                counts = store.store_chunk_extraction(chunk, result)
                stored = (
                    f" stored_mentions={counts['mentions']}"
                    f" stored_relationships={counts['relationships']}"
                )
            else:
                stored = " skipped_store_empty_result"

        print(
            f"[{position}/{len(chunks)}] {chunk.chunk_id} | "
            f"nodes={len(result.nodes)} relationships={len(result.relationships)}{stored}"
        )

    return extracted


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Load controlled Chunks from Neo4j and run KG extraction"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Load only the first N Chunks for a small pilot",
    )
    parser.add_argument(
        "--load-only",
        action="store_true",
        help="Load and count Chunks without making LLM calls",
    )
    parser.add_argument(
        "--extract-only",
        action="store_true",
        help="Extract Chunks but do not write graph/provenance data",
    )
    parser.add_argument(
        "--problem-gold",
        action="store_true",
        help="Load only Gold Chunks missing MENTIONS or a domain relation",
    )
    args = parser.parse_args()

    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be greater than zero")

    load_dotenv(ROOT / ".env")
    chunks = load_chunks(limit=args.limit, problem_gold=args.problem_gold)
    print(f"Loaded {len(chunks)} Chunks from {controlled_config().neo4j_uri}")

    if args.load_only:
        return 0

    cfg = controlled_config()
    llm = get_llm(cfg)

    driver = None
    store = None
    if not args.extract_only:
        driver = get_neo4j_driver(cfg)
        init_schema(driver)
        store = KGStore(driver=driver)

    try:
        extracted = extract_chunks(chunks, llm, store=store)
    finally:
        if store is not None:
            store.close()
        if driver is not None:
            driver.close()

    total_nodes = sum(len(result.nodes) for _, result in extracted)
    total_relationships = sum(len(result.relationships) for _, result in extracted)
    print(
        f"Extracted {len(extracted)} Chunks | "
        f"nodes={total_nodes} relationships={total_relationships}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
