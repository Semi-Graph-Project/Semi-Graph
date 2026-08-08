
from __future__ import annotations

import time
from typing import Literal, Optional

from neo4j import Driver

from semigraph.config import Config, get_config
from semigraph.connections import get_neo4j_driver
from semigraph.offline.specificity import INFORMATIVE_REL_TYPES
from semigraph.online.seed import query_to_seeds


# Re-export the YAML-backed graph configuration from the shared module.
PPR_REL_TYPES: list[str] = INFORMATIVE_REL_TYPES


_CYPHER_SANITY_CHECK = """
MATCH ()-[r]-()
WHERE type(r) IN $rels
RETURN type(r) AS rel_type, count(*) AS cnt
ORDER BY cnt DESC
"""

_CYPHER_RESOLVE_SEED_ENTITY_IDS = """
UNWIND range(0, size($seeds) - 1) AS seed_index
WITH seed_index, $seeds[seed_index] AS seed
MATCH (e:Entity)
WHERE e.name = seed.name AND e.type = seed.type
RETURN id(e) AS id,
       seed_index
"""

_CYPHER_RESOLVE_SEED_CHUNK_IDS = """
UNWIND range(0, size($seeds) - 1) AS seed_index
WITH seed_index, $seeds[seed_index] AS seed
MATCH (c:Chunk {chunk_id: seed.chunk_id})
RETURN id(c) AS id,
       seed_index
"""


_CYPHER_MAP_NAME = """
MATCH (e:Entity)
WHERE id(e) IN $ids
RETURN id(e) AS id, e.name AS name, e.type AS type
"""

_CYPHER_PROJECT = """
CALL gds.graph.project.cypher(
    $graph_name,
    $node_query,
    $rel_query
)
YIELD graphName, nodeCount, relationshipCount
RETURN graphName, nodeCount, relationshipCount
"""

_CYPHER_PROJECTION_EXISTS = """
CALL gds.graph.exists($graph_name)
YIELD exists
RETURN exists
"""

_CYPHER_PROJECTION_INFO = """
CALL gds.graph.list($graph_name)
YIELD graphName, nodeCount, relationshipCount
RETURN graphName, nodeCount, relationshipCount
"""

_CYPHER_PPR = """
CALL gds.pageRank.stream($graph_name, {
    sourceNodes: $source_ids,
    dampingFactor: $damping,
    maxIterations: $max_iter,
    relationshipWeightProperty: 'weight'
})
YIELD nodeId, score
RETURN nodeId, score
ORDER BY score DESC
"""

_CYPHER_DROP = """
CALL gds.graph.drop($graph_name, false)
YIELD graphName
RETURN graphName
"""


_CYPHER_CHUNK_NODE_IDS = """
MATCH (c:Chunk)
RETURN id(c) AS id
"""

_CYPHER_MAP_CHUNKS = """
MATCH (c:Chunk)
WHERE id(c) IN $ids
RETURN id(c) AS id,
       c.chunk_id AS chunk_id,
       c.text AS text,
       c.ticker AS ticker,
       c.fiscal_year AS fiscal_year,
       c.section AS section
"""

SeedWeightMode = Literal[
    "uniform",
    "similarity",
    "similarity_specificity",
]

PPRGraphMode = Literal[
    "entity_only",
    "entity_chunk",
]

PPR_PROJECTION_PREFIX = "semigraph_ppr"


def projection_name(mode: PPRGraphMode) -> str:
    """Return the stable GDS catalog name for one projection topology."""
    if mode not in {"entity_only", "entity_chunk"}:
        raise ValueError(f"Unknown PPR graph mode: {mode}")
    return f"{PPR_PROJECTION_PREFIX}_{mode}"


def _projection_info(session, name: str, mode: PPRGraphMode) -> dict | None:
    exists_row = session.run(
        _CYPHER_PROJECTION_EXISTS,
        graph_name=name,
    ).single()
    if not exists_row or not exists_row["exists"]:
        return None

    info = session.run(
        _CYPHER_PROJECTION_INFO,
        graph_name=name,
    ).single()
    if info is None:
        return None
    return {
        "name": info["graphName"],
        "mode": mode,
        "node_count": int(info["nodeCount"]),
        "relationship_count": int(info["relationshipCount"]),
    }


def projection_status(
    session,
    mode: PPRGraphMode,
) -> dict:
    """Inspect a reusable GDS projection without creating it."""
    name = projection_name(mode)
    info = _projection_info(session, name, mode)
    if info is None:
        return {
            "name": name,
            "mode": mode,
            "status": "missing",
            "node_count": 0,
            "relationship_count": 0,
        }
    return {**info, "status": "ready"}


def ensure_projection(
    session,
    mode: PPRGraphMode,
) -> dict:
    """Create a named GDS projection once, then reuse it across PPR calls."""
    started = time.perf_counter()
    name = projection_name(mode)
    existing = _projection_info(session, name, mode)
    if existing is not None:
        return {
            **existing,
            "status": "reused",
            "ensure_latency_sec": round(time.perf_counter() - started, 3),
        }

    try:
        projection = session.run(
            _CYPHER_PROJECT,
            graph_name=name,
            node_query=_build_node_query(mode),
            rel_query=_build_rel_query(mode),
        ).single()
    except Exception:
        # Another worker may have created the same named projection between
        # the existence check and project call. Reuse it only when it now
        # exists; otherwise preserve the original database error.
        existing = _projection_info(session, name, mode)
        if existing is None:
            raise
        return {
            **existing,
            "status": "reused",
            "ensure_latency_sec": round(time.perf_counter() - started, 3),
        }

    if projection is None:
        raise RuntimeError(f"GDS did not return projection metadata for '{name}'")
    return {
        "name": projection["graphName"],
        "mode": mode,
        "status": "created",
        "node_count": int(projection["nodeCount"]),
        "relationship_count": int(projection["relationshipCount"]),
        "ensure_latency_sec": round(time.perf_counter() - started, 3),
    }


def drop_projection(
    session,
    mode: PPRGraphMode,
) -> dict:
    """Drop a named projection explicitly; never called per query."""
    name = projection_name(mode)
    existing = _projection_info(session, name, mode)
    if existing is None:
        return {
            "name": name,
            "mode": mode,
            "status": "missing",
            "node_count": 0,
            "relationship_count": 0,
        }

    session.run(_CYPHER_DROP, graph_name=name).consume()
    return {**existing, "status": "dropped"}


def refresh_projection(
    session,
    mode: PPRGraphMode,
) -> dict:
    """Rebuild a projection after the underlying Neo4j graph changes."""
    previous = drop_projection(session, mode)
    current = ensure_projection(session, mode)
    return {
        **current,
        "status": "refreshed",
        "previous_status": previous["status"],
    }


def manage_projection(
    action: Literal["status", "prepare", "refresh", "drop"],
    mode: PPRGraphMode,
    cfg: Optional[Config] = None,
) -> dict:
    """Manage one projection using a short-lived Neo4j driver."""
    cfg = cfg or get_config()
    driver: Driver = get_neo4j_driver(cfg)
    try:
        with driver.session() as session:
            if action == "status":
                return projection_status(session, mode)
            if action == "prepare":
                return ensure_projection(session, mode)
            if action == "refresh":
                return refresh_projection(session, mode)
            if action == "drop":
                return drop_projection(session, mode)
            raise ValueError(f"Unknown projection action: {action}")
    finally:
        driver.close()


def _empty_passage_result() -> dict:
    return {
        "chunks": [],
        "ppr_entities": [],
        "seeds": [],
        "projection": {"node_count": 0, "relationship_count": 0},
    }


def ranking5seed(seeds: list[dict]) -> list[dict]:
    """Rank entity seeds by mean triple similarity and specificity."""
    ranked = []
    for seed in seeds:
        similarities = seed.get("triple_similarities") or [
            seed.get("similarity", 0.0)
        ]
        average_similarity = sum(float(score) for score in similarities) / len(
            similarities
        )
        ranked.append({**seed, "similarity": average_similarity})

    return sorted(
        ranked,
        key=lambda seed: (
            -float(seed["similarity"]) * float(seed.get("specificity", 1.0)),
            str(seed["name"]),
            str(seed["type"]),
        ),
    )[:5]


def _build_weighted_seed_ids(
    id_rows: list[dict],
    seeds: list[dict],
    mode: SeedWeightMode,
) -> list[tuple[int, float]]:
    weighted_seed_ids = []
    for row in id_rows:
        seed = seeds[int(row["seed_index"])]
        similarity = max(float(seed.get("similarity", 0)), 0.0)
        specificity = max(float(seed.get("specificity", 1.0)), 0.0)

        if mode == "uniform":
            weight = 1.0
        elif mode == "similarity":
            weight = similarity
        elif mode == "similarity_specificity":
            weight = similarity * specificity
        else:
            raise ValueError(f"Unknown seed weight mode: {mode}")

        weighted_seed_ids.append((row["id"], weight))

    if not weighted_seed_ids:
        return []

    total_weight = sum(weight for _, weight in weighted_seed_ids)

    if total_weight <= 0:
        uniform = 1.0 / len(weighted_seed_ids)
        return [
            (node_id, uniform)
            for node_id, _ in weighted_seed_ids
        ]

    return [
        (node_id, weight / total_weight)
        for node_id, weight in weighted_seed_ids
    ]


def _resolve_passage_seed_ids(session, seeds: list[dict]) -> list[dict]:
    """Resolve either Entity seeds or Chunk seeds to Neo4j node IDs."""
    if all("chunk_id" in seed for seed in seeds):
        query = _CYPHER_RESOLVE_SEED_CHUNK_IDS
    elif all("name" in seed and "type" in seed for seed in seeds):
        query = _CYPHER_RESOLVE_SEED_ENTITY_IDS
    else:
        raise ValueError(
            "Passage PPR seeds must all be Entity or all be Chunk seeds"
        )

    return list(session.run(query, seeds=seeds))


def _run_ppr_rows(
    session,
    graph_name: str,
    weighted_seed_ids: list[tuple[int, float]],
    *,
    damping: float,
    max_iterations: int,
    seed_weight_mode: SeedWeightMode,
) -> list[dict]:
    """Run the unchanged PPR calculation against a reusable projection."""
    if seed_weight_mode == "uniform":
        source_ids = [node_id for node_id, _ in weighted_seed_ids]
        return [
            {"nodeId": row["nodeId"], "score": float(row["score"])}
            for row in session.run(
                _CYPHER_PPR,
                graph_name=graph_name,
                source_ids=source_ids,
                damping=damping,
                max_iter=max_iterations,
            )
        ]

    rows = session.run(
        _CYPHER_PPR,
        graph_name=graph_name,
        source_ids=[
            [node_id, weight]
            for node_id, weight in weighted_seed_ids
        ],
        damping=damping,
        max_iter=max_iterations,
    )
    return [
        {"nodeId": row["nodeId"], "score": float(row["score"])}
        for row in rows
    ]


def _top_chunk_score_rows(
    ppr_rows: list[dict],
    chunk_node_ids: set[int],
    top_k: int,
) -> list[dict]:
    """Filter PPR results to Chunk nodes before selecting top-k."""
    chunk_rows = [
        row for row in ppr_rows
        if row["nodeId"] in chunk_node_ids
    ]
    return sorted(
        chunk_rows,
        key=lambda row: row["score"],
        reverse=True,
    )[:top_k]


def _sanity_check_rel_types(cfg: Optional[Config] = None) -> None:
    """Verify every PPR_REL_TYPE actually exists in the graph.

    Catches typos and ontology drift at module load time — without this,
    a missing type would silently reduce PPR connectivity and the bug
    would only surface as low recall in C2 ranking.
    """
    cfg = cfg or get_config()
    driver: Driver = get_neo4j_driver(cfg)
    try:
        with driver.session() as session:
            rows = list(session.run(_CYPHER_SANITY_CHECK, rels=PPR_REL_TYPES))

        seen = {row["rel_type"] for row in rows}
        missing = sorted(set(PPR_REL_TYPES) - seen)

        print(f"[sanity] PPR_REL_TYPES = {len(PPR_REL_TYPES)} types "
              f"({len(seen)} present, {len(missing)} missing)\n")
        print(f"  {'rel_type':28s} {'count':>10s}")
        print(f"  {'-' * 28} {'-' * 10}")
        for row in rows:
            print(f"  {row['rel_type']:28s} {row['cnt']:>10d}")

        if missing:
            print(f"\n  missing in graph: {missing}")
        else:
            print(f"\n  all types present")
    finally:
        driver.close()


def _build_rel_query(graph_mode: PPRGraphMode) -> str:
    # Inner Cypher of `gds.graph.project.cypher` is parsed in its own context
    # and cannot reference outer parameters, so rel types are inlined.
    # PPR_REL_TYPES is a module constant (not user input) — safe.
    rels_inline = ", ".join(f'"{t}"' for t in PPR_REL_TYPES)
    entity_edges = (
        "MATCH (s:Entity)-[r]->(t:Entity) "
        f"WHERE type(r) IN [{rels_inline}] "
        "RETURN id(s) AS source, id(t) AS target, 1.0 AS weight "
        "UNION ALL "
        "MATCH (s:Entity)-[r]->(t:Entity) "
        f"WHERE type(r) IN [{rels_inline}] "
        "RETURN id(t) AS source, id(s) AS target, 1.0 AS weight"
    )

    if graph_mode == "entity_only":
        return entity_edges

    if graph_mode != "entity_chunk":
        raise ValueError(f"Unknown PPR graph mode: {graph_mode}")

    context_edges = (
        " UNION ALL "
        "MATCH (c:Chunk)-[:MENTIONS]->(e:Entity) "
        "RETURN id(c) AS source, id(e) AS target, 1.0 AS weight "
        "UNION ALL "
        "MATCH (c:Chunk)-[:MENTIONS]->(e:Entity) "
        "RETURN id(e) AS source, id(c) AS target, 1.0 AS weight "
        "UNION ALL "
        "MATCH (a:Entity)-[r:SYNONYM_OF]->(b:Entity) "
        "RETURN id(a) AS source, id(b) AS target, "
        "       coalesce(r.score, 1.0) AS weight "
        "UNION ALL "
        "MATCH (a:Entity)-[r:SYNONYM_OF]->(b:Entity) "
        "RETURN id(b) AS source, id(a) AS target, "
        "       coalesce(r.score, 1.0) AS weight"
    )
    return entity_edges + context_edges


def _build_node_query(graph_mode: PPRGraphMode) -> str:
    """Build the node projection query for the requested graph mode."""
    if graph_mode == "entity_only":
        return "MATCH (n:Entity) RETURN id(n) AS id"

    if graph_mode == "entity_chunk":
        return (
            "MATCH (n) "
            "WHERE n:Entity OR n:Chunk "
            "RETURN id(n) AS id"
        )
    raise ValueError(f"Unknown PPR graph mode: {graph_mode}")


def run_passage_ppr(
    seeds: list[dict],
    top_k_chunks: int = 5,
    top_k_entities: int = 40,
    damping: float = 0.5,
    max_iterations: int = 20,
    seed_weight_mode: SeedWeightMode = "uniform",
    cfg: Optional[Config] = None,
) -> dict:
    """Run PPR over Entity+Chunk nodes from either Entity or Chunk seeds."""
    if not seeds:
        print("[run_passage_ppr] No seeds provided.")
        return _empty_passage_result()

    # seeds = ranking5seed(seeds)
    cfg = cfg or get_config()
    driver: Driver = get_neo4j_driver(cfg)
    try:
        with driver.session() as session:
            id_rows = _resolve_passage_seed_ids(session, seeds)

            weighted_seed_ids = _build_weighted_seed_ids(
                id_rows,
                seeds,
                seed_weight_mode,
            )

            if not weighted_seed_ids:
                print("[run_passage_ppr] No valid seed IDs - aborting walk.")
                return _empty_passage_result()

            projection = ensure_projection(
                session,
                "entity_chunk",
            )
            graph_name = projection["name"]
            ppr_started = time.perf_counter()
            ppr_rows = _run_ppr_rows(
                session,
                graph_name,
                weighted_seed_ids,
                damping=damping,
                max_iterations=max_iterations,
                seed_weight_mode=seed_weight_mode,
            )
            projection["ppr_latency_sec"] = round(
                time.perf_counter() - ppr_started,
                3,
            )

            chunk_node_ids = {
                row["id"]
                for row in session.run(_CYPHER_CHUNK_NODE_IDS)
            }


            entity_score_rows = sorted(
                (
                    row for row in ppr_rows
                    if row["nodeId"] not in chunk_node_ids
                ),
                key=lambda row: row["score"],
                reverse=True,
            )[:top_k_entities]
            entity_ids = [row["nodeId"] for row in entity_score_rows]
            entity_property_rows = list(session.run(
                _CYPHER_MAP_NAME,
                ids=entity_ids,
            ))
            id_to_entity = {
                row["id"]: {"name": row["name"], "type": row["type"]}
                for row in entity_property_rows
            }
            top_entities = [
                {
                    **id_to_entity[row["nodeId"]],
                    "score": float(row["score"]),
                }
                for row in entity_score_rows
                if row["nodeId"] in id_to_entity
            ]

            # ============= Chunk Query ===============
            top_chunk_rows = _top_chunk_score_rows(
                ppr_rows,
                chunk_node_ids,
                top_k_chunks,
            )
            chunk_by_id = {
                row["id"]: dict(row)
                for row in session.run(
                    _CYPHER_MAP_CHUNKS,
                    ids=[row["nodeId"] for row in top_chunk_rows],
                )
            }

            chunks = []
            for row in top_chunk_rows:
                chunk = chunk_by_id.get(row["nodeId"])
                if chunk is None:
                    continue

                chunks.append({
                    "chunk_id": chunk["chunk_id"],
                    "text": chunk["text"],
                    "ticker": chunk["ticker"],
                    "fiscal_year": chunk["fiscal_year"],
                    "section": chunk["section"],
                    "score": float(row["score"]),
                })

            return {
                "chunks": chunks,
                "ppr_entities": top_entities,
                "seeds": seeds,
                "projection": projection,
            }
    finally:
        driver.close()


def run_ppr(
    seeds: list[dict],
    top_k: int = 20,
    damping: float = 0.85,
    max_iterations: int = 20,
    seed_weight_mode: SeedWeightMode = "uniform",
    cfg: Optional[Config] = None,
) -> list[dict]:
    """Run Personalized PageRank over a reusable Entity-only projection.

    Args:
        seeds: Output of `query_to_seeds()` / `query_to_triple_seeds()`.
               Each dict requires `name`.
        top_k: Number of top-scoring entities to return.
        damping: PageRank damping factor (0.85 = HippoRAG default).
        max_iterations: Power-iteration cap.
        cfg: Optional Config; defaults to cached singleton.

    Returns:
        List of dicts sorted by PPR score desc, each: [`{name, type, score}`, ...].
        Empty list if seeds is empty or no seed name maps to a graph entity.

    The named GDS projection is retained between calls. Call
    `refresh_projection()` after the underlying Neo4j graph changes.
    """
    if not seeds:
        print("[run_ppr] No seeds provided.")
        return []

    cfg = cfg or get_config()
    driver: Driver = get_neo4j_driver(cfg)
    try:
        with driver.session() as session:
            id_rows = list(session.run(
                _CYPHER_RESOLVE_SEED_ENTITY_IDS,
                seeds=seeds,
            ))
            weighted_seed_ids = _build_weighted_seed_ids(
                id_rows,
                seeds,
                seed_weight_mode,
            )

            if not weighted_seed_ids:
                print("[run_ppr] No valid seed IDs - aborting walk.")
                return []

            projection = ensure_projection(
                session,
                "entity_only",
            )
            ppr_rows = _run_ppr_rows(
                session,
                projection["name"],
                weighted_seed_ids,
                damping=damping,
                max_iterations=max_iterations,
                seed_weight_mode=seed_weight_mode,
            )

            top_rows = ppr_rows[:top_k]
            node_ids = [row["nodeId"] for row in top_rows]
            prop_rows = list(session.run(_CYPHER_MAP_NAME, ids=node_ids))
            id_to_props = {
                row["id"]: {"name": row["name"], "type": row["type"]}
                for row in prop_rows
            }

            return [
                {
                    "name": id_to_props[row["nodeId"]]["name"],
                    "type": id_to_props[row["nodeId"]]["type"],
                    "score": row["score"],
                }
                for row in top_rows
                if row["nodeId"] in id_to_props
            ]
    finally:
        driver.close()


if __name__ == "__main__":
    _sanity_check_rel_types()

    print("\n" + "=" * 50)
    seeds = query_to_seeds("Compare R&D Alphabet vs Meta 2023")
    print(f"\n[test] Seeds for query='Compare R&D Alphabet vs Meta 2023':")
    for s in seeds:
        print(f"  sim={s['similarity']:.3f}  spec={s['specificity']:.3f}  "
              f"{s['name']:30s} ({s['type']})")

    print(f"\n[test] Running PPR (top_k=10)...")
    results = run_ppr(seeds, top_k=10)
    print(f"\n[test] Top {len(results)} entities by PPR score:")
    for r in results:
        print(f"  score={r['score']:.6f}  {r['name']:30s} ({r['type']})")
