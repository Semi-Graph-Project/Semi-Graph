#!/usr/bin/env python3
"""Import the selected FinReflectKG corpus into its Neo4j database."""
from __future__ import annotations

import json
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import pyarrow.dataset as ds
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from semigraph.benchmark.finreflectkg import ( 
    canonical_chunk_id,
    default_dataset_dir,
    normalize_entity_type,
    normalize_name,
    normalize_relation_type,
    question_tickers,
)
from semigraph.config import get_config  

QA_FILE = Path.home() / "Documents/book/paper/project/final_master_dataset.json"
DATA_DIR = default_dataset_dir()
YEARS = [2022, 2023, 2024]
BATCH_SIZE = 2000
DATASET_REVISION = "81819dfb4c95a96963c9a1848466cdf9612d47c0"
MANIFEST_PATH = ROOT / "data/neo4j/finreflectkg_import_manifest.json"

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


def relationship_cypher(relation_type: str) -> str:
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


def write_batch(session, chunks: dict, mentions: set, relationships: dict) -> None:
    if chunks:
        session.run(CHUNK_CYPHER, rows=list(chunks.values())).consume()

    if mentions:
        rows = [
            {"chunk_id": chunk_id, "name": name, "type": entity_type}
            for chunk_id, name, entity_type in mentions
        ]
        session.run(MENTION_CYPHER, rows=rows).consume()

    for relation_type, rows in relationships.items():
        if rows:
            session.run(relationship_cypher(relation_type), rows=rows).consume()


def graph_summary(session) -> dict:
    counts = session.run("""
        MATCH (n)
        WITH count(n) AS nodes
        MATCH ()-[r]->()
        RETURN nodes, count(r) AS relationships
    """).single()

    labels = {
        row["label"]: row["count"]
        for row in session.run("""
            MATCH (n)
            UNWIND labels(n) AS label
            RETURN label, count(*) AS count
            ORDER BY label
        """)
    }
    relationship_types = {
        row["type"]: row["count"]
        for row in session.run("""
            MATCH ()-[r]->()
            RETURN type(r) AS type, count(*) AS count
            ORDER BY type
        """)
    }

    return {
        "nodes": int(counts["nodes"]),
        "relationships": int(counts["relationships"]),
        "labels": labels,
        "relationship_types": relationship_types,
    }


def main() -> None:
    if not QA_FILE.exists():
        raise FileNotFoundError(f"QA file not found: {QA_FILE}")
    if not DATA_DIR.exists():
        raise FileNotFoundError(f"FinReflectKG data not found: {DATA_DIR}")

    questions = json.loads(QA_FILE.read_text(encoding="utf-8"))["questions"]
    tickers = sorted(question_tickers(questions))
    print(f"[import] tickers={tickers}")
    print(f"[import] years={YEARS}")

    dataset = ds.dataset(DATA_DIR, format="parquet")
    data_filter = (
        ds.field("ticker").isin(tickers)
        & ds.field("year").isin(YEARS)
    )
    batches = dataset.scanner(
        filter=data_filter,
        batch_size=BATCH_SIZE,
    ).to_batches()

    config = get_config()
    if not config.neo4j_password:
        raise RuntimeError("NEO4J_PASSWORD is required")

    target_uri = config.finreflectkg_neo4j_uri
    print(f"[import] target={target_uri}")
    driver = GraphDatabase.driver(
        target_uri,
        auth=(config.neo4j_user, config.neo4j_password),
    )

    stats = Counter()
    started = time.time()

    try:
        driver.verify_connectivity()
        with driver.session() as session:
            for statement in SCHEMA_STATEMENTS:
                session.run(statement).consume()

            for batch_number, batch in enumerate(batches, start=1):
                chunks = {}
                mentions = set()
                relationships = defaultdict(list)

                for row in batch.to_pylist():
                    stats["rows_seen"] += 1
                    text = str(row.get("chunk_text") or "").strip()
                    if not text:
                        stats["rows_without_context"] += 1
                        continue

                    chunk_id = canonical_chunk_id(
                        row["source_file"],
                        row["page_id"],
                        row["chunk_id"],
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

                write_batch(session, chunks, mentions, relationships)
                stats["chunk_rows_written"] += len(chunks)
                stats["mention_rows_written"] += len(mentions)

                if batch_number % 10 == 0:
                    print(
                        f"[import] batches={batch_number} "
                        f"rows={stats['rows_seen']} "
                        f"accepted_rels={stats['accepted_relationships']}"
                    )

            summary = graph_summary(session)
    finally:
        driver.close()

    manifest = {
        "dataset_revision": DATASET_REVISION,
        "data_dir": str(DATA_DIR),
        "qa_file": str(QA_FILE),
        "question_limit": None,
        "tickers": tickers,
        "years": YEARS,
        "elapsed_seconds": round(time.time() - started, 3),
        "import_stats": dict(stats),
        "graph": summary,
    }

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    print(f"[import] manifest={MANIFEST_PATH}")


if __name__ == "__main__":
    main()
