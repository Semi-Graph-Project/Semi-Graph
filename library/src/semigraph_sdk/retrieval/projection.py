"""Manage the SDK-owned in-memory GDS graph for one workspace."""

from __future__ import annotations

import hashlib


_EXISTS = "CALL gds.graph.exists($graph_name) YIELD exists RETURN exists"
_DROP = "CALL gds.graph.drop($graph_name, false) YIELD graphName RETURN graphName"
_PROJECT = """
MATCH (source)
WHERE source:Chunk OR source:Entity
OPTIONAL MATCH (source)-[r]->(target)
WHERE (target:Chunk OR target:Entity)
  AND (type(r) = 'MENTIONS' OR r.source_chunk_id IS NOT NULL)
WITH source, target, r,
     CASE WHEN r IS NULL THEN 'ISOLATED' ELSE type(r) END AS projected_type
WITH gds.graph.project(
    $graph_name,
    source,
    target,
    {
        sourceNodeLabels: labels(source),
        targetNodeLabels: CASE WHEN target IS NULL THEN [] ELSE labels(target) END,
        relationshipType: projected_type
    },
    {undirectedRelationshipTypes: ['*']}
) AS graph
RETURN graph.graphName AS graph_name,
       graph.nodeCount AS node_count,
       graph.relationshipCount AS relationship_count
"""


class ProjectionError(RuntimeError):
    """The GDS graph could not be created or inspected."""


def projection_name(workspace_id: str) -> str:
    digest = hashlib.sha256(workspace_id.encode("utf-8")).hexdigest()[:20]
    return f"semigraph_sdk_{digest}"


def _exists(session, name: str) -> bool:
    row = session.run(_EXISTS, graph_name=name).single()
    return bool(row and row["exists"])


def ensure_projection(
    session, workspace_id: str, *, rebuild: bool = False
) -> dict:
    """Return an existing projection or build it; optionally replace it first."""
    name = projection_name(workspace_id)
    try:
        exists = _exists(session, name)
        if exists and rebuild:
            session.run(_DROP, graph_name=name).consume()
            exists = False
        if exists:
            row = session.run(
                "CALL gds.graph.list($graph_name) "
                "YIELD graphName, nodeCount, relationshipCount "
                "RETURN graphName, nodeCount, relationshipCount",
                graph_name=name,
            ).single()
            if row is not None:
                return {
                    "name": row["graphName"],
                    "node_count": int(row["nodeCount"]),
                    "relationship_count": int(row["relationshipCount"]),
                    "created": False,
                }
            # A catalog race or stale name is repaired by rebuilding below.
            session.run(_DROP, graph_name=name).consume()
        row = session.run(_PROJECT, graph_name=name).single()
        if row is None:
            raise ProjectionError("GDS projection returned no result")
        return {
            "name": row["graph_name"],
            "node_count": int(row["node_count"]),
            "relationship_count": int(row["relationship_count"]),
            "created": True,
        }
    except ProjectionError:
        raise
    except Exception as exc:
        raise ProjectionError(
            f"Cannot ensure GDS projection {name!r}: "
            f"{exc.__class__.__name__}: {exc}"
        ) from exc
