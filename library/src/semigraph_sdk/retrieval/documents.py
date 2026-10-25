"""Hydrate selected chunks with their stored text and extraction provenance."""

from __future__ import annotations

from typing import Any


_LOAD_DOCUMENTS = """
UNWIND $chunk_ids AS requested_id
MATCH (chunk:Chunk {chunk_id: requested_id})
OPTIONAL MATCH (chunk)-[mention:MENTIONS]->(entity:Entity)
WITH chunk, collect(CASE WHEN entity IS NULL THEN null ELSE {
    name: entity.name,
    type: entity.type,
    evidence_quote: mention.evidence_quote,
    evidence_start: mention.evidence_start,
    evidence_end: mention.evidence_end
} END) AS entities
OPTIONAL MATCH (head:Entity)-[assertion]->(tail:Entity)
WHERE assertion.source_chunk_id = chunk.chunk_id
RETURN chunk.chunk_id AS chunk_id,
       chunk.text AS text,
       entities,
       collect(CASE WHEN assertion IS NULL THEN null ELSE {
           assertion_id: assertion.assertion_id,
           head: head.name,
           head_type: head.type,
           relation: type(assertion),
           relation_description: assertion.relation_description,
           tail: tail.name,
           tail_type: tail.type,
           evidence_quote: assertion.evidence_quote,
           evidence_start: assertion.evidence_start,
           evidence_end: assertion.evidence_end,
           triple_text: assertion.triple_text
       } END) AS assertions
"""


def load_documents(session, chunk_ids: list[str]) -> dict[str, dict[str, Any]]:
    """Return only requested passages; never transfer vector properties."""
    if not chunk_ids:
        return {}
    rows = session.run(_LOAD_DOCUMENTS, chunk_ids=chunk_ids)
    documents: dict[str, dict[str, Any]] = {}
    for row in rows:
        entities = [item for item in (row["entities"] or []) if item is not None]
        assertions = [item for item in (row["assertions"] or []) if item is not None]
        entities.sort(key=lambda item: (item["type"] or "", item["name"] or ""))
        assertions.sort(key=lambda item: item["assertion_id"] or "")
        documents[row["chunk_id"]] = {
            "chunk_id": row["chunk_id"],
            "text": row["text"],
            "entities": entities,
            "assertions": assertions,
        }
    return documents


def attach_documents(session, ranked: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep retrieval rank and score while adding stored passage provenance."""
    documents = load_documents(session, [row["chunk_id"] for row in ranked])
    return [
        {**documents[row["chunk_id"]], **row}
        for row in ranked
        if row["chunk_id"] in documents
    ]
