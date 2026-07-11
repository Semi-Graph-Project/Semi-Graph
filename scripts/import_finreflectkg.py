#!/usr/bin/env python3
"""Import a bounded FinReflectKG parquet corpus into an isolated Neo4j."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import pyarrow.dataset as ds
from dotenv import load_dotenv
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from semigraph.benchmark.finreflectkg import (  # noqa: E402
    canonical_chunk_id,
    default_dataset_dir,
    normalize_entity_type,
    normalize_name,
    normalize_relation_type,
    question_tickers,
)


SCHEMA_STATEMENTS = (
    "CREATE CONSTRAINT entity_name_type IF NOT EXISTS "
    "FOR (e:Entity) REQUIRE (e.name, e.type) IS UNIQUE",
    "CREATE CONSTRAINT chunk_id_unique IF NOT EXISTS "
    "FOR (c:Chunk) REQUIRE c.chunk_id IS UNIQUE",
    "CREATE CONSTRAINT document_unique IF NOT EXISTS "
    "FOR (d:Document) REQUIRE (d.ticker, d.fiscal_year, d.filing_type) IS UNIQUE",
    "CREATE CONSTRAINT section_unique IF NOT EXISTS "
    "FOR (s:Section) REQUIRE (s.doc_key, s.name) IS UNIQUE",
    "CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type)",
)

CHUNK_CYPHER = """
UNWIND $rows AS row
MERGE (d:Document {
    ticker: row.ticker,
    fiscal_year: row.fiscal_year,
    filing_type: '10-K'
})
SET d.doc_key = row.doc_key,
    d.source_file = row.source_file,
    d.dataset = 'FinReflectKG'
MERGE (s:Section {doc_key: row.doc_key, name: row.page_id})
SET s.page_id = row.page_id,
    s.source_file = row.source_file
MERGE (d)-[:HAS_SECTION]->(s)
MERGE (c:Chunk {chunk_id: row.chunk_id})
SET c.text = row.text,
    c.char_count = size(row.text),
    c.token_estimate = toInteger(size(row.text) / 4),
    c.section = row.page_id,
    c.page_id = row.page_id,
    c.raw_chunk_id = row.raw_chunk_id,
    c.source_file = row.source_file,
    c.ticker = row.ticker,
    c.fiscal_year = row.fiscal_year,
    c.filing_type = '10-K',
    c.dataset = 'FinReflectKG'
MERGE (s)-[:HAS_CHUNK]->(c)
"""

MENTION_CYPHER = """
UNWIND $rows AS row
MATCH (c:Chunk {chunk_id: row.chunk_id})
MERGE (e:Entity {name: row.name, type: row.type})
SET e.dataset = 'FinReflectKG'
MERGE (c)-[:MENTIONS]->(e)
"""


def _load_questions(path: Path, limit: int | None) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    questions = list(payload["questions"])
    return questions[:limit] if limit is not None else questions


def _parse_tickers(raw: str | None, qa_file: Path, question_limit: int | None) -> list[str]:
    if raw:
        return sorted({value.strip().upper() for value in raw.split(",") if value.strip()})
    return sorted(question_tickers(_load_questions(qa_file, question_limit)))


def _relationship_cypher(relation_type: str) -> str:
    if not re.fullmatch(r"[A-Z][A-Z0-9_]*", relation_type):
        raise ValueError(f"Unsafe relationship type: {relation_type!r}")
    return f"""
    UNWIND $rows AS row
    MATCH (source:Entity {{name: row.source_name, type: row.source_type}})
    MATCH (target:Entity {{name: row.target_name, type: row.target_type}})
    MERGE (source)-[r:{relation_type} {{triplet_id: row.triplet_id}}]->(target)
    SET r.source_chunk = row.chunk_id,
        r.source_file = row.source_file,
        r.page_id = row.page_id,
        r.raw_chunk_id = row.raw_chunk_id,
        r.ticker = row.ticker,
        r.fiscal_year = row.fiscal_year,
        r.start_date = row.start_date,
        r.end_date = row.end_date,
        r.extraction_type = row.extraction_type,
        r.dataset = 'FinReflectKG'
    """


def _clear_database(session) -> None:
    session.run("MATCH (n) DETACH DELETE n").consume()


def _init_schema(session) -> None:
    for statement in SCHEMA_STATEMENTS:
        session.run(statement).consume()


def _flush(session, chunks: dict, mentions: set, relationships: dict) -> None:
    if chunks:
        session.run(CHUNK_CYPHER, rows=list(chunks.values())).consume()
    if mentions:
        session.run(
            MENTION_CYPHER,
            rows=[
                {"chunk_id": chunk_id, "name": name, "type": entity_type}
                for chunk_id, name, entity_type in mentions
            ],
        ).consume()
    for relation_type, rows in relationships.items():
        if rows:
            session.run(_relationship_cypher(relation_type), rows=rows).consume()


def _summary(session) -> dict:
    row = session.run("""
        MATCH (n)
        WITH count(n) AS nodes
        MATCH ()-[r]->()
        RETURN nodes, count(r) AS relationships
    """).single()
    labels = {
        record["label"]: record["n"]
        for record in session.run("""
            MATCH (n)
            UNWIND labels(n) AS label
            RETURN label, count(*) AS n
            ORDER BY label
        """)
    }
    rel_types = {
        record["type"]: record["n"]
        for record in session.run("""
            MATCH ()-[r]->()
            RETURN type(r) AS type, count(*) AS n
            ORDER BY type
        """)
    }
    return {
        "nodes": int(row["nodes"]),
        "relationships": int(row["relationships"]),
        "labels": labels,
        "relationship_types": rel_types,
    }


def main() -> None:
    load_dotenv(ROOT / ".env")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=default_dataset_dir())
    parser.add_argument(
        "--qa-file",
        type=Path,
        default=Path("/home/kantinan/Documents/book/paper/project/final_master_dataset.json"),
    )
    parser.add_argument("--question-limit", type=int)
    parser.add_argument("--tickers", help="Comma-separated override; defaults to tickers in QA selection")
    parser.add_argument("--years", default="2022,2023,2024")
    parser.add_argument("--batch-size", type=int, default=2000)
    parser.add_argument("--neo4j-uri", default=os.getenv("FINREFLECTKG_NEO4J_URI", "bolt://localhost:7688"))
    parser.add_argument("--neo4j-user", default=os.getenv("NEO4J_USER", "neo4j"))
    parser.add_argument("--neo4j-password", default=os.getenv("NEO4J_PASSWORD", ""))
    parser.add_argument("--clear", action="store_true")
    parser.add_argument(
        "--manifest",
        type=Path,
        # Keep metadata outside the Docker-owned volume mount.
        default=ROOT / "data" / "neo4j" / "finreflectkg_import_manifest.json",
    )
    args = parser.parse_args()
    if not args.neo4j_password:
        parser.error("NEO4J_PASSWORD is required")
    if not args.data_dir.exists():
        parser.error(f"Dataset directory does not exist: {args.data_dir}")

    tickers = _parse_tickers(args.tickers, args.qa_file, args.question_limit)
    years = sorted({int(value) for value in args.years.split(",") if value.strip()})
    print(f"[import] tickers={tickers}")
    print(f"[import] years={years} target={args.neo4j_uri}")

    dataset = ds.dataset(args.data_dir, format="parquet")
    corpus_filter = ds.field("ticker").isin(tickers) & ds.field("year").isin(years)
    scanner = dataset.scanner(filter=corpus_filter, batch_size=args.batch_size)

    driver = GraphDatabase.driver(
        args.neo4j_uri,
        auth=(args.neo4j_user, args.neo4j_password),
    )
    stats = Counter()
    started = time.time()
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            if args.clear:
                print("[import] clearing isolated benchmark database")
                _clear_database(session)
            _init_schema(session)

            for batch_number, batch in enumerate(scanner.to_batches(), start=1):
                chunks: dict[str, dict] = {}
                mentions: set[tuple[str, str, str]] = set()
                relationships: dict[str, list[dict]] = defaultdict(list)
                for row in batch.to_pylist():
                    stats["rows_seen"] += 1
                    text = str(row.get("chunk_text") or "").strip()
                    if not text:
                        stats["rows_without_context"] += 1
                        continue

                    chunk_id = canonical_chunk_id(
                        row["source_file"], row["page_id"], row["chunk_id"]
                    )
                    ticker = str(row["ticker"]).upper()
                    fiscal_year = int(row["year"])
                    doc_key = f"{ticker}_{fiscal_year}_10-K"
                    chunks[chunk_id] = {
                        "chunk_id": chunk_id,
                        "raw_chunk_id": str(row["chunk_id"]),
                        "text": text,
                        "ticker": ticker,
                        "fiscal_year": fiscal_year,
                        "doc_key": doc_key,
                        "source_file": str(row["source_file"]),
                        "page_id": str(row["page_id"]),
                    }

                    source_name = normalize_name(row.get("entity"))
                    source_type = normalize_entity_type(row.get("entity_type"))
                    target_name = normalize_name(row.get("target"))
                    target_type = normalize_entity_type(row.get("target_type"))
                    if source_name and source_type:
                        mentions.add((chunk_id, source_name, source_type))
                    else:
                        stats["invalid_source_entities"] += 1
                    if target_name and target_type:
                        mentions.add((chunk_id, target_name, target_type))
                    else:
                        stats["invalid_target_entities"] += 1

                    relation_type = normalize_relation_type(row.get("relationship"))
                    if not relation_type:
                        stats["filtered_relationships"] += 1
                        continue
                    if not (source_name and source_type and target_name and target_type):
                        stats["relationships_with_invalid_endpoint"] += 1
                        continue
                    relationships[relation_type].append({
                        "triplet_id": str(row["triplet_id"]),
                        "source_name": source_name,
                        "source_type": source_type,
                        "target_name": target_name,
                        "target_type": target_type,
                        "chunk_id": chunk_id,
                        "source_file": str(row["source_file"]),
                        "page_id": str(row["page_id"]),
                        "raw_chunk_id": str(row["chunk_id"]),
                        "ticker": ticker,
                        "fiscal_year": fiscal_year,
                        "start_date": row.get("start_date"),
                        "end_date": row.get("end_date"),
                        "extraction_type": row.get("extraction_type"),
                    })
                    stats["accepted_relationships"] += 1

                _flush(session, chunks, mentions, relationships)
                stats["chunk_rows_written"] += len(chunks)
                stats["mention_rows_written"] += len(mentions)
                if batch_number % 10 == 0:
                    print(
                        f"[import] batches={batch_number} rows={stats['rows_seen']} "
                        f"accepted_rels={stats['accepted_relationships']}"
                    )

            graph_summary = _summary(session)
    finally:
        driver.close()

    manifest = {
        "dataset_revision": "81819dfb4c95a96963c9a1848466cdf9612d47c0",
        "data_dir": str(args.data_dir),
        "qa_file": str(args.qa_file),
        "question_limit": args.question_limit,
        "tickers": tickers,
        "years": years,
        "elapsed_seconds": round(time.time() - started, 3),
        "import_stats": dict(stats),
        "graph": graph_summary,
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    print(f"[import] manifest={args.manifest}")


if __name__ == "__main__":
    main()
