#!/usr/bin/env python3
"""Convert FinReflectKG-MultiHop JSON into SemiGraph evaluator YAML."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from semigraph.benchmark.finreflectkg import (  
    convert_question,
    gold_entity_aliases,
    strict_ticker_questions,
)


def main() -> None:
    load_dotenv(ROOT / ".env")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("/home/kantinan/Documents/book/paper/project/final_master_dataset.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data" / "evaluate" / "finreflectkg_multihop.yaml",
    )
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--strict-tickers",
        help=(
            "Keep only questions whose every evidence source belongs to this "
            "comma-separated ticker set. Applied before --limit."
        ),
    )
    parser.add_argument("--neo4j-uri", default=os.getenv("FINREFLECTKG_NEO4J_URI", "bolt://localhost:7688"))
    parser.add_argument("--neo4j-user", default=os.getenv("NEO4J_USER", "neo4j"))
    parser.add_argument("--neo4j-password", default=os.getenv("NEO4J_PASSWORD", ""))
    args = parser.parse_args()
    if not args.neo4j_password:
        parser.error("NEO4J_PASSWORD is required")

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    questions = list(payload["questions"])
    strict_tickers = None
    if args.strict_tickers:
        strict_tickers = {
            ticker.strip().upper()
            for ticker in args.strict_tickers.split(",")
            if ticker.strip()
        }
        questions = strict_ticker_questions(questions, strict_tickers)
    if args.limit is not None:
        questions = questions[:args.limit]

    driver = GraphDatabase.driver(
        args.neo4j_uri,
        auth=(args.neo4j_user, args.neo4j_password),
    )
    try:
        with driver.session() as session:
            available = {
                str(row["chunk_id"])
                for row in session.run("MATCH (c:Chunk) RETURN c.chunk_id AS chunk_id")
            }
            entities_by_chunk: dict[str, set[tuple[str, str]]] = {}
            for row in session.run("""
                MATCH (c:Chunk)-[:MENTIONS]->(e:Entity)
                RETURN c.chunk_id AS chunk_id, e.name AS name, e.type AS type
            """):
                entities_by_chunk.setdefault(str(row["chunk_id"]), set()).add(
                    (str(row["name"]), str(row["type"]))
                )
    finally:
        driver.close()

    all_graph_entities = {
        entity
        for entities in entities_by_chunk.values()
        for entity in entities
    }

    converted = []
    skipped = []
    for question in questions:
        item = convert_question(question, available)
        if item is None:
            skipped.append(int(question["question_id"]))
        else:
            aliases = gold_entity_aliases(
                question,
                item["gold_chunks"],
                entities_by_chunk,
                all_graph_entities,
            )
            if aliases:
                item["gold_entity_aliases"] = aliases
            converted.append(item)

    alias_pair_count = sum(
        len(aliases)
        for item in converted
        for aliases in item.get("gold_entity_aliases", {}).values()
    )

    output = {
        "metadata": {
            "source": str(args.input),
            "source_question_count": len(questions),
            "strict_tickers": sorted(strict_tickers) if strict_tickers else None,
            "converted_question_count": len(converted),
            "skipped_missing_evidence": skipped,
            "questions_with_gold_entity_aliases": sum(
                bool(item.get("gold_entity_aliases")) for item in converted
            ),
            "gold_entity_alias_pair_count": alias_pair_count,
            "gold_entity_alias_policy": (
                "exists in Neo4j + compatible type + conservative morphology/company alias"
            ),
            "chunk_id_format": "source_file::page_id::chunk_id",
            "evidence_group_semantics": "Each hop is one required evidence group.",
        },
        "queries": converted,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        yaml.safe_dump(output, sort_keys=False, allow_unicode=False, width=120),
        encoding="utf-8",
    )
    print(json.dumps(output["metadata"], indent=2))
    print(f"[convert] output={args.output}")


if __name__ == "__main__":
    main()
