"""
End-to-end smoke test for the offline pipeline:
  chunker -> kg_extract -> kg_store -> Neo4j

Runs on a few real NVDA chunks, then verifies the graph via Cypher queries.

Usage:
    python scripts/test_kg_store_smoke.py
    python scripts/test_kg_store_smoke.py --section Item_1A --num-chunks 3
"""
from __future__ import annotations

import argparse
import time

from semigraph.config import get_config
from semigraph.connections import get_neo4j_driver
from semigraph.offline.chunker import chunk_section
from semigraph.offline.kg_extract import extract_chunk
from semigraph.offline.kg_store import KGStore, init_schema, store_chunks


def verify_graph(driver, ticker: str, fiscal_year: str, filing_type: str = "10-K"):
    """Query Neo4j to check what was stored for a given filing."""
    with driver.session() as session:
        print("\n=== Verification queries ===")

        # 1. Document → Section → Chunk
        result = session.run(
            """
            MATCH (d:Document {ticker: $ticker, fiscal_year: $fiscal_year})
                  -[:HAS_SECTION]->(s:Section)-[:HAS_CHUNK]->(c:Chunk)
            RETURN s.name AS section, count(c) AS chunks
            ORDER BY section
            """,
            ticker=ticker, fiscal_year=fiscal_year,
        )
        print(f"\n  [provenance hierarchy]")
        for r in result:
            print(f"    {r['section']}: {r['chunks']} chunks")

        # 2. Entity counts by type
        result = session.run(
            """
            MATCH (c:Chunk {ticker: $ticker, fiscal_year: $fiscal_year})-[:MENTIONS]->(e:Entity)
            RETURN e.type AS type, count(DISTINCT e) AS unique_entities
            ORDER BY unique_entities DESC
            """,
            ticker=ticker, fiscal_year=fiscal_year,
        )
        print(f"\n  [entities by type]")
        for r in result:
            print(f"    {r['type']}: {r['unique_entities']}")

        # 3. Sample entities
        result = session.run(
            """
            MATCH (c:Chunk {ticker: $ticker, fiscal_year: $fiscal_year})-[:MENTIONS]->(e:Entity)
            RETURN DISTINCT e.name AS name, e.type AS type
            ORDER BY type, name
            LIMIT 15
            """,
            ticker=ticker, fiscal_year=fiscal_year,
        )
        print(f"\n  [sample entities]")
        for r in result:
            print(f"    [{r['type']}] {r['name']}")

        # 4. Sample relationships
        result = session.run(
            """
            MATCH (c:Chunk {ticker: $ticker, fiscal_year: $fiscal_year})-[:MENTIONS]->(s:Entity)
            MATCH (s)-[r]->(t:Entity)
            WHERE type(r) <> 'MENTIONS'
            RETURN s.name AS src, type(r) AS rel, t.name AS tgt, r.source_chunk AS src_chunk
            LIMIT 10
            """,
            ticker=ticker, fiscal_year=fiscal_year,
        )
        print(f"\n  [sample relationships]")
        for r in result:
            print(f"    ({r['src']}) -[:{r['rel']}]-> ({r['tgt']})  [from {r['src_chunk']}]")

        # 5. Provenance check — every entity must be mentioned in at least one chunk
        result = session.run(
            """
            MATCH (e:Entity)
            WHERE NOT (e)<-[:MENTIONS]-(:Chunk)
            RETURN count(e) AS orphans
            """,
        )
        orphans = result.single()["orphans"]
        print(f"\n  [orphan entities (no provenance)]: {orphans}")
        if orphans > 0:
            print(f"    WARN: should be 0 if pipeline is correct")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", default="NVDA")
    parser.add_argument("--fiscal-year", default="2026")
    parser.add_argument("--section", default="Item_1",
                        choices=["Item_1", "Item_1A", "Item_5", "Item_7", "Item_8"])
    parser.add_argument("--num-chunks", type=int, default=2)
    args = parser.parse_args()

    cfg = get_config()
    driver = get_neo4j_driver()

    try:
        # 1. Init schema (constraints + indexes)
        print("[1/4] init_schema(): creating constraints & indexes...")
        init_schema(driver)
        print("      OK")

        # 2. Load + chunk a section
        section_file = cfg.processed_dir / args.ticker / f"FY{args.fiscal_year}-10K" / f"{args.section}.md"
        text = section_file.read_text(encoding="utf-8")
        chunks = chunk_section(
            text=text,
            ticker=args.ticker,
            fiscal_year=args.fiscal_year,
            section=args.section,
        )
        n = min(args.num_chunks, len(chunks))
        print(f"\n[2/4] chunk_section(): {len(chunks)} total, testing {n}")

        # 3. Extract + store, sequential for simplicity
        print(f"\n[3/4] extract_chunk() + store_extraction() for {n} chunks...")
        t0 = time.time()

        store = KGStore(driver=driver)
        store.reset_filing(args.ticker, args.fiscal_year, "10-K")
        store.ensure_filing(args.ticker, args.fiscal_year, "10-K")

        totals = {"nodes": 0, "relationships": 0}
        for i, chunk in enumerate(chunks[:n]):
            print(f"      [{i + 1}/{n}] extracting chunk {chunk.chunk_id[-12:]}...", end=" ", flush=True)
            result = extract_chunk(chunk.text, section=args.section)
            counts = store.store_extraction(chunk, result)
            totals["nodes"] += counts["nodes"]
            totals["relationships"] += counts["relationships"]
            print(f"{counts['nodes']} nodes, {counts['relationships']} rels")

        elapsed = time.time() - t0
        print(f"\n      Total: {totals['nodes']} nodes, {totals['relationships']} rels  ({elapsed:.1f}s)")

        # 4. Verify
        print(f"\n[4/4] verifying graph state...")
        verify_graph(driver, args.ticker, args.fiscal_year)

        print("\nAll done — open Neo4j Browser at http://localhost:7474 to explore.")
        print(f"Try: MATCH (d:Document {{ticker: '{args.ticker}'}})-[*]-(n) RETURN d, n LIMIT 100")

    finally:
        driver.close()


if __name__ == "__main__":
    main()
