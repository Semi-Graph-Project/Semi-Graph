"""Finalize a published batch and make its corpus revision searchable."""

from __future__ import annotations

from neo4j import Driver

from ..config import SDKConfig
from ..database import _wait_indexes
from ..retrieval.projection import ensure_projection


def _refresh_relation_catalog(session) -> None:
    rows = [
        dict(row)
        for row in session.run(
            "MATCH ()-[r]->() "
            "WHERE r.source_chunk_id IS NOT NULL "
            "WITH type(r) AS id, min(r.relation_description) AS description, "
            "count(r) AS assertion_count "
            "RETURN id, description, assertion_count ORDER BY id"
        )
    ]
    session.run(
        "MATCH (observed:ObservedRelation) SET observed.assertion_count = 0"
    ).consume()
    if not rows:
        return
    session.run(
        "UNWIND $rows AS row "
        "WITH row ORDER BY row.id "
        "MERGE (observed:ObservedRelation {id: row.id}) "
        "ON CREATE SET observed.description = coalesce( "
        "row.description, toLower(replace(row.id, '_', ' '))) "
        "ON MATCH SET observed.description = coalesce(observed.description, "
        "row.description, toLower(replace(row.id, '_', ' '))) "
        "SET observed.assertion_count = row.assertion_count, "
        "observed.updated_at = datetime()",
        rows=rows,
    ).consume()


def _refresh_specificity(session) -> None:
    session.run(
        "MATCH (entity:Entity) "
        "OPTIONAL MATCH (entity)-[relation]-(other:Entity) "
        "WHERE relation.source_chunk_id IS NOT NULL "
        "WITH entity, count(relation) AS degree "
        "SET entity.specificity = CASE WHEN degree = 0 THEN 1.0 "
        "ELSE 1.0 / log(degree + 1.0) END"
    ).consume()


def finalize_batch(driver: Driver, config: SDKConfig) -> dict:
    """Refresh metadata/indexes/projection; only then publish search readiness."""
    database = config.database.name
    try:
        with driver.session(database=database) as session:
            _wait_indexes(session, timeout_seconds=90)
            _refresh_relation_catalog(session)
            _refresh_specificity(session)
            projection = ensure_projection(
                session, config.workspace_id, rebuild=True
            )
            row = session.run(
                "MATCH (m:SDKMeta {key: 'root'}) "
                "SET m.corpus_revision = coalesce(m.corpus_revision, 0) + 1, "
                "m.search_ready = true, m.finalized_at = datetime(), "
                "m.ingestion_started_at = null "
                "RETURN m.corpus_revision AS corpus_revision"
            ).single()
            if row is None:
                raise RuntimeError("SDK metadata record is missing during finalization")
            return {
                "corpus_revision": int(row["corpus_revision"]),
                "projection": projection,
            }
    except Exception as exc:
        # Readiness was cleared before publication; keep it cleared on any failure.
        try:
            with driver.session(database=database) as session:
                session.run(
                    "MATCH (m:SDKMeta {key: 'root'}) SET m.search_ready = false"
                ).consume()
        except Exception:
            pass
        raise RuntimeError(
            f"Ingestion finalization failed: {exc.__class__.__name__}: {exc}"
        ) from exc


def ensure_existing_projection(driver: Driver, config: SDKConfig) -> dict:
    """Restore a projection after restart without changing corpus revision."""
    with driver.session(database=config.database.name) as session:
        return ensure_projection(session, config.workspace_id)
