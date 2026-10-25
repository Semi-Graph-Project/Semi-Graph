"""Create and validate the schema owned by one SDK knowledge base."""

from __future__ import annotations

import time
from dataclasses import dataclass

from neo4j import Driver

from .config import SDKConfig


SCHEMA_VERSION = 2
REQUIRED_PROCEDURES = frozenset(
    {"apoc.merge.relationship", "gds.graph.project", "gds.pageRank.stream"}
)


class SetupError(RuntimeError):
    """Database connection, capability or schema setup failed."""


class IncompatibleDatabase(SetupError):
    """The selected database belongs to another corpus or has conflicting schema."""


@dataclass(frozen=True)
class SetupReport:
    uri: str
    database: str
    workspace_id: str
    schema_version: int
    embedding_dimension: int
    apoc_version: str
    gds_version: str
    indexes_online: bool
    search_ready: bool


_CONSTRAINTS = {
    "sg_meta_key": (
        "SDKMeta", ("key",),
        "CREATE CONSTRAINT sg_meta_key IF NOT EXISTS "
        "FOR (m:SDKMeta) REQUIRE m.key IS UNIQUE",
    ),
    "sg_chunk_id": (
        "Chunk", ("chunk_id",),
        "CREATE CONSTRAINT sg_chunk_id IF NOT EXISTS "
        "FOR (c:Chunk) REQUIRE c.chunk_id IS UNIQUE",
    ),
    "sg_entity_name_type": (
        "Entity", ("name", "type"),
        "CREATE CONSTRAINT sg_entity_name_type IF NOT EXISTS "
        "FOR (e:Entity) REQUIRE (e.name, e.type) IS UNIQUE",
    ),
    "sg_relation_id": (
        "ObservedRelation", ("id",),
        "CREATE CONSTRAINT sg_relation_id IF NOT EXISTS "
        "FOR (r:ObservedRelation) REQUIRE r.id IS UNIQUE",
    ),
    "sg_ingestion_checkpoint": (
        "IngestionCheckpoint", ("chunk_id",),
        "CREATE CONSTRAINT sg_ingestion_checkpoint IF NOT EXISTS "
        "FOR (c:IngestionCheckpoint) REQUIRE c.chunk_id IS UNIQUE",
    ),
}

_INDEXES = {
    "sg_entity_type": ("RANGE", "Entity", ("type",)),
    "sg_chunk_embedding": ("VECTOR", "Chunk", ("embedding",)),
    "sg_entity_embedding": ("VECTOR", "Entity", ("embedding",)),
}


def _check_capabilities(session) -> tuple[str, str]:
    rows = session.run(
        "SHOW PROCEDURES YIELD name WHERE name IN $names RETURN name",
        names=sorted(REQUIRED_PROCEDURES),
    )
    found = {record["name"] for record in rows}
    missing = REQUIRED_PROCEDURES - found
    if missing:
        raise SetupError(
            "Neo4j is missing required APOC/GDS procedures: "
            + ", ".join(sorted(missing))
        )
    versions = session.run(
        "RETURN apoc.version() AS apoc, gds.version() AS gds"
    ).single()
    return str(versions["apoc"]), str(versions["gds"])


def _check_metadata(session, config: SDKConfig) -> dict | None:
    records = [
        dict(row)
        for row in session.run(
            "MATCH (m:SDKMeta) RETURN m.key AS key, m.owner AS owner, "
            "m.schema_version AS schema_version, "
            "m.embedding_fingerprint AS embedding_fingerprint, "
            "m.search_ready AS search_ready"
        )
    ]
    if len(records) > 1 or (records and records[0]["key"] != "root"):
        raise IncompatibleDatabase("Database has unexpected SDK metadata records")
    if not records:
        count = session.run("MATCH (n) RETURN count(n) AS total").single()["total"]
        if count:
            raise IncompatibleDatabase(
                "Selected database is nonempty and has no compatible SDK metadata; "
                "use an empty dedicated database"
            )
        return None
    meta = records[0]
    if meta["owner"] != config.workspace_id:
        raise IncompatibleDatabase("Database belongs to another SDK workspace")
    if meta["schema_version"] not in {1, SCHEMA_VERSION}:
        raise IncompatibleDatabase("Database schema version differs from this SDK")
    if meta["embedding_fingerprint"] != config.embedding.fingerprint:
        raise IncompatibleDatabase(
            "Embedding model/revision/dimension/normalization differs from the database"
        )
    return meta


def _show_constraints(session) -> list[dict]:
    return [
        dict(row)
        for row in session.run(
            "SHOW CONSTRAINTS YIELD name, type, entityType, labelsOrTypes, properties "
            "RETURN name, type, entityType, labelsOrTypes, properties"
        )
    ]


def _show_indexes(session) -> list[dict]:
    return [
        dict(row)
        for row in session.run(
            "SHOW INDEXES YIELD name, type, entityType, labelsOrTypes, properties, options, state "
            "RETURN name, type, entityType, labelsOrTypes, properties, options, state"
        )
    ]


def _check_schema(session, dimension: int) -> None:
    constraints = _show_constraints(session)
    indexes = _show_indexes(session)
    for name, (label, properties, _) in _CONSTRAINTS.items():
        for row in constraints:
            same_name = row["name"] == name
            same_schema = (
                row["entityType"] == "NODE"
                and row["labelsOrTypes"] == [label]
                and tuple(row["properties"]) == properties
            )
            constraint_type = str(row["type"]).upper().replace(" ", "_")
            if same_name or same_schema:
                if not (
                    same_name
                    and same_schema
                    and constraint_type in {"UNIQUENESS", "NODE_PROPERTY_UNIQUENESS"}
                ):
                    raise IncompatibleDatabase(f"Conflicting constraint: {name}")
        if any(row["name"] == name for row in indexes):
            # A unique constraint owns a backing range index with the same name.
            if not any(row["name"] == name for row in constraints):
                raise IncompatibleDatabase(f"Index name conflicts with constraint: {name}")
    for name, (kind, label, properties) in _INDEXES.items():
        if any(row["name"] == name for row in constraints):
            raise IncompatibleDatabase(f"Constraint name conflicts with index: {name}")
        for row in indexes:
            same_name = row["name"] == name
            same_schema = (
                row["entityType"] == "NODE"
                and row["labelsOrTypes"] == [label]
                and tuple(row["properties"]) == properties
                and row["type"] == kind
            )
            if not (same_name or same_schema):
                continue
            if not (same_name and same_schema):
                raise IncompatibleDatabase(f"Conflicting index: {name}")
            if kind == "VECTOR":
                options = row["options"] or {}
                index_config = options.get("indexConfig", {})
                if (
                    index_config.get("vector.dimensions") != dimension
                    or str(index_config.get("vector.similarity_function", "")).lower()
                    != "cosine"
                ):
                    raise IncompatibleDatabase(
                        f"Vector index {name} has incompatible dimension or similarity"
                    )


def _create_schema(session, dimension: int) -> None:
    for _, _, statement in _CONSTRAINTS.values():
        session.run(statement).consume()
    session.run(
        "CREATE INDEX sg_entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type)"
    ).consume()
    for name, label, variable in (
        ("sg_chunk_embedding", "Chunk", "c"),
        ("sg_entity_embedding", "Entity", "e"),
    ):
        session.run(
            f"CREATE VECTOR INDEX {name} IF NOT EXISTS "
            f"FOR ({variable}:{label}) ON ({variable}.embedding) "
            f"OPTIONS {{indexConfig: {{`vector.dimensions`: {dimension}, "
            "`vector.similarity_function`: 'cosine'}}"
        ).consume()


def _wait_indexes(session, timeout_seconds: float) -> None:
    deadline = time.monotonic() + timeout_seconds
    while True:
        rows = {row["name"]: row for row in _show_indexes(session)}
        missing = set(_INDEXES) - rows.keys()
        if missing:
            raise SetupError(f"Missing SDK indexes after creation: {sorted(missing)}")
        pending = [name for name in _INDEXES if rows[name]["state"] != "ONLINE"]
        if not pending:
            return
        if time.monotonic() >= deadline:
            raise SetupError(f"SDK indexes did not become ONLINE: {pending}")
        time.sleep(0.5)


def setup_database(
    config: SDKConfig, driver: Driver, *, timeout_seconds: float = 90
) -> SetupReport:
    """Validate plugins and ownership before creating idempotent SDK schema."""
    try:
        driver.verify_connectivity()
        with driver.session(database=config.database.name) as session:
            apoc_version, gds_version = _check_capabilities(session)
            meta = _check_metadata(session, config)
            _check_schema(session, config.embedding.dimension)
            _create_schema(session, config.embedding.dimension)
            _wait_indexes(session, timeout_seconds)
            # Metadata is created last, so an interrupted setup can resume safely.
            session.run(
                "MERGE (m:SDKMeta {key: 'root'}) "
                "ON CREATE SET m.owner = $owner, m.schema_version = $version, "
                "m.embedding_fingerprint = $fingerprint, m.corpus_revision = 0, "
                "m.search_ready = false, m.created_at = datetime()",
                owner=config.workspace_id,
                version=SCHEMA_VERSION,
                fingerprint=config.embedding.fingerprint,
            ).consume()
            # Version 2 only adds the checkpoint uniqueness constraint. Keep this
            # migration additive so existing version-1 workspaces retain data.
            session.run(
                "MATCH (m:SDKMeta {key: 'root'}) SET m.schema_version = $version",
                version=SCHEMA_VERSION,
            ).consume()
            return SetupReport(
                uri=config.database.uri,
                database=config.database.name,
                workspace_id=config.workspace_id,
                schema_version=SCHEMA_VERSION,
                embedding_dimension=config.embedding.dimension,
                apoc_version=apoc_version,
                gds_version=gds_version,
                indexes_online=True,
                search_ready=bool(meta and meta["search_ready"]),
            )
    except SetupError:
        raise
    except Exception as exc:
        raise SetupError(
            f"Cannot set up database {config.database.name} at {config.database.uri}: "
            f"{exc.__class__.__name__}: {exc}"
        ) from exc
