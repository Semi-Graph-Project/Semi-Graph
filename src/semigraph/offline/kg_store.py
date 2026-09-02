"""
Idempotent storage layer for the knowledge graph.

Writes a `GraphExtractionResult` (output of `extract_chunk`) into Neo4j with a
provenance hierarchy:

    (:Document {ticker, fiscal_year, filing_type})
        -[:HAS_SECTION]-> (:Section {name})
            -[:HAS_CHUNK]-> (:Chunk {chunk_id, text, char_count})
                -[:MENTIONS]-> (:Entity {name, type, ...})

Domain relationships between entities are stored with a `source_chunk` property
so every fact can be traced back to the chunk it was extracted from. This is
the layer that the online Graph Search Tool (PPR) reads from.

Idempotency: every write uses MERGE keyed by deterministic identifiers, so
re-running the pipeline does not duplicate anything.

Dynamic relationship types use APOC's `apoc.merge.relationship` since plain
Cypher MERGE cannot parameterize the relationship type.
"""
from __future__ import annotations

from neo4j import Driver

from semigraph.connections import get_neo4j_driver
from semigraph.offline.chunker import Chunk
from semigraph.ontology.nodes import GraphExtractionResult


# ===========================================================================
# Schema initialization — run once per fresh database
# ===========================================================================


_CONSTRAINTS = [
    # Composite uniqueness on (name, type) for entities so MERGE is fast and
    # safe. Same string with different type stays distinct (e.g. "China" as
    # GPE vs as ORG_GOV).
    """
    CREATE CONSTRAINT entity_name_type IF NOT EXISTS
    FOR (e:Entity) REQUIRE (e.name, e.type) IS UNIQUE
    """,
    """
    CREATE CONSTRAINT chunk_id_unique IF NOT EXISTS
    FOR (c:Chunk) REQUIRE c.chunk_id IS UNIQUE
    """,
    """
    CREATE CONSTRAINT document_unique IF NOT EXISTS
    FOR (d:Document) REQUIRE (d.ticker, d.fiscal_year, d.filing_type) IS UNIQUE
    """,
    """
    CREATE CONSTRAINT section_unique IF NOT EXISTS
    FOR (s:Section) REQUIRE (s.doc_key, s.name) IS UNIQUE
    """,
]

_INDEXES = [
    "CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type)",
]


def init_schema(driver: Driver | None = None) -> None:
    """Create constraints and indexes. Idempotent — safe to run repeatedly."""
    close_after = driver is None
    driver = driver or get_neo4j_driver()
    try:
        with driver.session() as session:
            for stmt in _CONSTRAINTS + _INDEXES:
                session.run(stmt)
    finally:
        if close_after:
            driver.close()


# ===========================================================================
# KGStore — write extraction results
# ===========================================================================


def _doc_key(ticker: str, fiscal_year: str, filing_type: str) -> str:
    """Deterministic key for a Document — used to scope :Section uniqueness."""
    return f"{ticker}_{fiscal_year}_{filing_type}"


class KGStore:
    """Thin wrapper around the neo4j Driver with the upsert helpers we need.

    Caller pattern:
        store = KGStore()              # opens driver
        store.ensure_filing(...)       # once per filing
        for chunk, result in pairs:
            store.store_extraction(chunk, result)
        store.close()
    """

    def __init__(self, driver: Driver | None = None) -> None:
        self._owns_driver = driver is None
        self.driver = driver or get_neo4j_driver()

    def close(self) -> None:
        if self._owns_driver:
            self.driver.close()

    def reset_filing(
        self, ticker: str, fiscal_year: str, filing_type: str = "10-K"
    ) -> None:
        """Remove every graph element previously written for one filing.

        This makes reruns idempotent at the filing level: old chunks, section
        nodes, provenance edges, and chunk-scoped domain relationships are
        cleared before the filing is written again. Shared Entity nodes are
        pruned only when they no longer have any MENTIONS provenance left.
        """
        doc_key = _doc_key(ticker, fiscal_year, filing_type)

        with self.driver.session() as session:
            def _tx(tx):
                row = tx.run(
                    """
                    MATCH (s:Section {doc_key: $doc_key})-[:HAS_CHUNK]->(c:Chunk)
                    RETURN collect(DISTINCT c.chunk_id) AS chunk_ids
                    """,
                    doc_key=doc_key,
                ).single()

                chunk_ids = [cid for cid in (row["chunk_ids"] or []) if cid]

                if chunk_ids:
                    tx.run(
                        """
                        MATCH ()-[r]->()
                        WHERE r.source_chunk IN $chunk_ids
                        DELETE r
                        """,
                        chunk_ids=chunk_ids,
                    )
                    tx.run(
                        """
                        MATCH (c:Chunk)
                        WHERE c.chunk_id IN $chunk_ids
                        DETACH DELETE c
                        """,
                        chunk_ids=chunk_ids,
                    )

                tx.run(
                    """
                    MATCH (s:Section {doc_key: $doc_key})
                    DETACH DELETE s
                    """,
                    doc_key=doc_key,
                )
                tx.run(
                    """
                    MATCH (d:Document {doc_key: $doc_key})
                    DETACH DELETE d
                    """,
                    doc_key=doc_key,
                )

                tx.run(
                    """
                    MATCH (e:Entity)
                    WHERE NOT (e)<-[:MENTIONS]-(:Chunk)
                    DETACH DELETE e
                    """
                )

            session.execute_write(_tx)

    # ------------------------------------------------------------------
    # Provenance hierarchy: Document → Section → Chunk
    # ------------------------------------------------------------------

    def ensure_filing(
        self, ticker: str, fiscal_year: str, filing_type: str = "10-K"
    ) -> str:
        """Upsert a Document node. Returns its doc_key."""
        doc_key = _doc_key(ticker, fiscal_year, filing_type)
        with self.driver.session() as session:
            session.run(
                """
                MERGE (d:Document {
                    ticker: $ticker,
                    fiscal_year: $fiscal_year,
                    filing_type: $filing_type
                })
                ON CREATE SET d.created_at = timestamp(), d.doc_key = $doc_key
                """,
                ticker=ticker,
                fiscal_year=fiscal_year,
                filing_type=filing_type,
                doc_key=doc_key,
            )
        return doc_key

    def _ensure_section(self, tx, doc_key: str, section_name: str) -> None:
        tx.run(
            """
            MATCH (d:Document {doc_key: $doc_key})
            MERGE (s:Section {doc_key: $doc_key, name: $name})
            MERGE (d)-[:HAS_SECTION]->(s)
            """,
            doc_key=doc_key,
            name=section_name,
        )

    def _ensure_chunk(self, tx, doc_key: str, chunk: Chunk) -> None:
        tx.run(
            """
            MATCH (s:Section {doc_key: $doc_key, name: $section_name})
            MERGE (c:Chunk {chunk_id: $chunk_id})
            ON CREATE SET
                c.text = $text,
                c.char_count = $char_count,
                c.token_estimate = $token_estimate,
                c.section = $section_name,
                c.ticker = $ticker,
                c.fiscal_year = $fiscal_year,
                c.filing_type = $filing_type
            SET c.filing_type = coalesce(c.filing_type, $filing_type)
            MERGE (s)-[:HAS_CHUNK]->(c)
            """,
            doc_key=doc_key,
            section_name=chunk.section,
            chunk_id=chunk.chunk_id,
            text=chunk.text,
            char_count=chunk.char_count,
            token_estimate=chunk.token_estimate,
            ticker=chunk.ticker,
            fiscal_year=chunk.fiscal_year,
            filing_type=chunk.filing_type,
        )

    # ------------------------------------------------------------------
    # Entities + relationships
    # ------------------------------------------------------------------

    def _clear_chunk_extraction(self, tx, chunk_id: str) -> None:
        """Remove previous extraction output for one chunk before rewriting it.

        Chunk text/provenance and embeddings stay intact; only extracted
        MENTIONS and chunk-scoped domain facts are replaced. This prevents
        partial reprocessing from accumulating stale entities on the same
        chunk, which would otherwise inflate graph retrieval scores.
        """
        tx.run(
            """
            MATCH ()-[r]->()
            WHERE r.source_chunk = $chunk_id
            DELETE r
            """,
            chunk_id=chunk_id,
        )
        tx.run(
            """
            MATCH (:Chunk {chunk_id: $chunk_id})-[m:MENTIONS]->(:Entity)
            DELETE m
            """,
            chunk_id=chunk_id,
        )
        tx.run(
            """
            MATCH (e:Entity)
            WHERE NOT (e)<-[:MENTIONS]-(:Chunk)
            DETACH DELETE e
            """
        )

    def _upsert_entities_and_mentions(
        self, tx, chunk_id: str, nodes: list
    ) -> int:
        """MERGE every entity and link it to the chunk via :MENTIONS."""
        if not nodes:
            return 0
        # Strip 'name' from properties so MERGE-key (lowercased id) is the
        # canonical name. Otherwise an uppercase 'name' from the LLM would
        # overwrite our normalized name via `e += node.properties`.
        payload = [
            {
                "name": n.id,
                "type": n.type,
                "properties": {
                    k: v for k, v in (n.properties or {}).items() if k != "name"
                },
            }
            for n in nodes
        ]
        tx.run(
            """
            MATCH (c:Chunk {chunk_id: $chunk_id})
            UNWIND $nodes AS node
            MERGE (e:Entity {name: node.name, type: node.type})
            ON CREATE SET e += node.properties, e.name = node.name, e.type = node.type
            ON MATCH SET e += node.properties, e.name = node.name, e.type = node.type
            MERGE (c)-[:MENTIONS]->(e)
            """,
            chunk_id=chunk_id,
            nodes=payload,
        )
        return len(payload)

    def _upsert_relationships(self, tx, chunk_id: str, rels: list) -> int:
        """MERGE domain relationships using APOC for dynamic rel-type."""
        if not rels:
            return 0
        count = 0
        for r in rels:
            tx.run(
                """
                MATCH (s:Entity {name: $src_name, type: $src_type})
                MATCH (t:Entity {name: $tgt_name, type: $tgt_type})
                CALL apoc.merge.relationship(
                    s,
                    $rel_type,
                    {source_chunk: $chunk_id},
                    $properties,
                    t
                ) YIELD rel
                RETURN rel
                """,
                src_name=r.source,
                src_type=r.source_type,
                tgt_name=r.target,
                tgt_type=r.target_type,
                rel_type=r.type.upper(),
                chunk_id=chunk_id,
                properties=r.properties or {},
            )
            count += 1
        return count

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def store_extraction(
        self,
        chunk: Chunk,
        result: GraphExtractionResult,
    ) -> dict:
        """
        Upsert one chunk's extraction result. Caller must have called
        `ensure_filing(...)` for the parent filing already.

        Returns counts for logging:
            {"nodes": int, "relationships": int}
        """
        doc_key = _doc_key(chunk.ticker, chunk.fiscal_year, chunk.filing_type)

        with self.driver.session() as session:
            # All writes for one chunk happen in a single transaction so a
            # failure mid-chunk leaves the graph in a consistent state.
            def _tx(tx):
                self._ensure_section(tx, doc_key, chunk.section)
                self._ensure_chunk(tx, doc_key, chunk)
                self._clear_chunk_extraction(tx, chunk.chunk_id)
                n_count = self._upsert_entities_and_mentions(tx, chunk.chunk_id, result.nodes)
                r_count = self._upsert_relationships(tx, chunk.chunk_id, result.relationships)
                return n_count, r_count

            n_count, r_count = session.execute_write(_tx)

        return {"nodes": n_count, "relationships": r_count}

    def store_chunk_extraction(
        self,
        chunk: Chunk,
        result: GraphExtractionResult,
    ) -> dict:
        """Store Entity, MENTIONS, and domain relations from an existing Chunk.

        This controlled-evaluation mode does not create filing provenance.
        """
        with self.driver.session() as session:
            def _tx(tx):
                self._clear_chunk_extraction(tx, chunk.chunk_id)
                mention_count = self._upsert_entities_and_mentions(
                    tx, chunk.chunk_id, result.nodes
                )
                relationship_count = self._upsert_relationships(
                    tx, chunk.chunk_id, result.relationships
                )
                return mention_count, relationship_count

            mention_count, relationship_count = session.execute_write(_tx)

        return {
            "mentions": mention_count,
            "relationships": relationship_count,
        }
