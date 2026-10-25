"""Checkpoint and atomically publish validated chunk graph data."""

from __future__ import annotations

import json

from neo4j import Driver

from .models import ValidatedExtraction


def load_checkpoint(
    driver: Driver, database: str, chunk_id: str
) -> dict | None:
    query = """
    MATCH (cp:IngestionCheckpoint {chunk_id: $chunk_id})
    OPTIONAL MATCH (chunk:Chunk {chunk_id: $chunk_id})
    RETURN cp.pipeline_fingerprint AS fingerprint,
           cp.status AS status,
           cp.extraction_json AS extraction_json,
           chunk IS NOT NULL AS chunk_exists
    """
    with driver.session(database=database) as session:
        row = session.run(query, chunk_id=chunk_id).single()
    return dict(row) if row is not None else None


def save_validated_checkpoint(
    driver: Driver,
    database: str,
    chunk_id: str,
    fingerprint: str,
    extraction: ValidatedExtraction,
) -> None:
    payload = json.dumps(
        extraction.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    query = """
    MERGE (cp:IngestionCheckpoint {chunk_id: $chunk_id})
    SET cp.pipeline_fingerprint = $fingerprint,
        cp.status = 'VALIDATED',
        cp.extraction_json = $extraction_json,
        cp.updated_at = datetime()
    """
    with driver.session(database=database) as session:
        session.run(
            query,
            chunk_id=chunk_id,
            fingerprint=fingerprint,
            extraction_json=payload,
        ).consume()


def decode_checkpoint(payload: str) -> ValidatedExtraction:
    return ValidatedExtraction.model_validate_json(payload)


def mark_search_not_ready(driver: Driver, database: str) -> None:
    with driver.session(database=database) as session:
        session.run(
            "MATCH (m:SDKMeta {key: 'root'}) "
            "SET m.search_ready = false, m.ingestion_started_at = datetime()"
        ).consume()


def publish_chunk(
    driver: Driver,
    database: str,
    *,
    chunk_id: str,
    text: str,
    chunk_embedding: list[float],
    pipeline_fingerprint: str,
    extraction: ValidatedExtraction,
    embeddings_by_text: dict[str, list[float]],
) -> None:
    """Replace one chunk's extraction and checkpoint in one Neo4j transaction."""
    entities = sorted(extraction.entities, key=lambda item: item.entity_key)
    assertions = sorted(extraction.assertions, key=lambda item: item.assertion_id)
    entity_rows = [
        {
            "name": entity.name,
            "type": entity.type,
            "entity_key": entity.entity_key,
            "embedding": embeddings_by_text[f"entity\0{entity.name}\0{entity.type}"],
            "evidence_quote": entity.evidence_quote,
            "evidence_start": entity.start,
            "evidence_end": entity.end,
        }
        for entity in entities
    ]
    entity_by_key = {entity.entity_key: entity for entity in entities}
    assertion_rows = []
    for assertion in assertions:
        head = entity_by_key[assertion.head_key]
        tail = entity_by_key[assertion.tail_key]
        assertion_rows.append(
            {
                "assertion_id": assertion.assertion_id,
                "head_name": head.name,
                "head_type": head.type,
                "tail_name": tail.name,
                "tail_type": tail.type,
                "relation_type": assertion.relation_type,
                "relation_description": assertion.relation_description,
                "evidence_quote": assertion.evidence_quote,
                "evidence_start": assertion.start,
                "evidence_end": assertion.end,
                "triple_text": assertion.triple_text,
                "triple_embedding": embeddings_by_text[
                    f"triple\0{assertion.triple_text}"
                ],
                "source_chunk_id": chunk_id,
                "pipeline_fingerprint": pipeline_fingerprint,
            }
        )

    def write_transaction(tx) -> None:
        tx.run(
            "MERGE (c:Chunk {chunk_id: $chunk_id}) "
            "ON CREATE SET c.created_at = datetime() "
            "SET c.text = $text, c.embedding = $embedding, "
            "c.content_hash = $chunk_id, c.pipeline_fingerprint = $fingerprint, "
            "c.updated_at = datetime()",
            chunk_id=chunk_id,
            text=text,
            embedding=chunk_embedding,
            fingerprint=pipeline_fingerprint,
        ).consume()
        tx.run(
            "MATCH (c:Chunk {chunk_id: $chunk_id}) "
            "OPTIONAL MATCH (c)-[mention:MENTIONS]->() "
            "WITH c, collect(mention) AS mentions "
            "FOREACH (m IN mentions | DELETE m) "
            "WITH c "
            "OPTIONAL MATCH (:Entity)-[old]->(:Entity) "
            "WHERE old.source_chunk_id = $chunk_id "
            "WITH c, collect(old) AS old_assertions "
            "FOREACH (r IN old_assertions | DELETE r)",
            chunk_id=chunk_id,
        ).consume()
        tx.run(
            "MATCH (e:Entity) "
            "WHERE NOT (e)<-[:MENTIONS]-(:Chunk) "
            "AND NOT (e)-[]-(:Entity) "
            "DETACH DELETE e"
        ).consume()
        if entity_rows:
            tx.run(
                "UNWIND $rows AS row "
                "WITH row ORDER BY row.entity_key "
                "MATCH (c:Chunk {chunk_id: $chunk_id}) "
                "MERGE (e:Entity {name: row.name, type: row.type}) "
                "ON CREATE SET e.embedding = row.embedding, e.specificity = 1.0, "
                "e.created_at = datetime() "
                "ON MATCH SET e.embedding = coalesce(e.embedding, row.embedding), "
                "e.specificity = coalesce(e.specificity, 1.0) "
                "MERGE (c)-[m:MENTIONS]->(e) "
                "SET m.evidence_quote = row.evidence_quote, "
                "m.evidence_start = row.evidence_start, "
                "m.evidence_end = row.evidence_end",
                chunk_id=chunk_id,
                rows=entity_rows,
            ).consume()
        if assertion_rows:
            tx.run(
                "UNWIND $rows AS row "
                "WITH row ORDER BY row.assertion_id "
                "MATCH (head:Entity {name: row.head_name, type: row.head_type}) "
                "MATCH (tail:Entity {name: row.tail_name, type: row.tail_type}) "
                "CALL apoc.merge.relationship( "
                "head, row.relation_type, "
                "{source_chunk_id: row.source_chunk_id, assertion_id: row.assertion_id}, "
                "{evidence_quote: row.evidence_quote, "
                " evidence_start: row.evidence_start, evidence_end: row.evidence_end, "
                " relation_description: row.relation_description, "
                " triple_text: row.triple_text, "
                " triple_embedding: row.triple_embedding, "
                " pipeline_fingerprint: row.pipeline_fingerprint}, tail "
                ") YIELD rel "
                "RETURN count(rel) AS written",
                rows=assertion_rows,
            ).consume()
        extraction_json = json.dumps(
            extraction.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        tx.run(
            "MERGE (cp:IngestionCheckpoint {chunk_id: $chunk_id}) "
            "SET cp.pipeline_fingerprint = $fingerprint, cp.status = 'COMPLETE', "
            "cp.extraction_json = $extraction_json, cp.updated_at = datetime()",
            chunk_id=chunk_id,
            fingerprint=pipeline_fingerprint,
            extraction_json=extraction_json,
        ).consume()

    with driver.session(database=database) as session:
        session.execute_write(write_transaction)


def corpus_state(driver: Driver, database: str) -> dict:
    query = """
    OPTIONAL MATCH (m:SDKMeta {key: 'root'})
    WITH m
    OPTIONAL MATCH (c:Chunk)
    RETURN coalesce(m.search_ready, false) AS search_ready,
           coalesce(m.corpus_revision, 0) AS corpus_revision,
           count(c) AS chunk_count
    """
    with driver.session(database=database) as session:
        row = session.run(query).single()
    return {
        "search_ready": bool(row["search_ready"]),
        "corpus_revision": int(row["corpus_revision"]),
        "chunk_count": int(row["chunk_count"]),
    }
