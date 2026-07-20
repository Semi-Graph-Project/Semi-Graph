
from __future__ import annotations

import uuid
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

_CYPHER_MAP_ID = """
UNWIND $seeds AS seed
MATCH (e:Entity)
WHERE e.name = seed.name AND e.type = seed.type
RETURN id(e) AS id,
       e.name AS name,
       e.type AS type
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




def _empty_passage_result() -> dict:
    return {
        "chunks": [],
        "ppr_entities": [],
        "projection": {"node_count": 0, "relationship_count": 0},
    }


def _seed_weight(seed: dict, mode: SeedWeightMode) -> float:
    similarity = max(float(seed.get("similarity", 0)), 0.0)
    specificity = max(float(seed.get("specificity", 1.0)), 0.0)

    if mode == "uniform":
        return 1.0
    if mode == "similarity":
        return similarity
    if mode == "similarity_specificity":
        return similarity * specificity

    raise ValueError(f"Unknown seed weight mode: {mode}")


def _normalize_seed_weights(
    weight_seeds: list[tuple[int, float]],
) -> list[tuple[int, float]]:
    if not weight_seeds:
        return []

    total_weight = sum(weight for _, weight in weight_seeds)

    if total_weight <= 0:
        uniform = 1.0 / len(weight_seeds)
        return [(node_id, uniform) for node_id, _ in weight_seeds]

    return [
        (node_id, weight / total_weight)
        for node_id, weight in weight_seeds
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
    """Run PPR over Entity and Chunk nodes and return ranked passages."""
    if not seeds:
        print("[run_passage_ppr] No seeds provided.")
        return _empty_passage_result()

    cfg = cfg or get_config()
    driver: Driver = get_neo4j_driver(cfg)
    graph_name = f"ppr_{uuid.uuid4().hex[:8]}"

    try:
        with driver.session() as session:
            id_rows = list(session.run(
                _CYPHER_MAP_ID,
                seeds=[
                    {
                        "name": seed["name"],
                        "type": seed["type"],
                    }
                    for seed in seeds
                ]

            ))

            seed_lookup = {
                (seed["name"], seed["type"]): seed
                for seed in seeds
            }

            weighted_seed_ids = []
            for row in id_rows:
                seed = seed_lookup[(row["name"], row["type"])]
                weight = _seed_weight(seed, seed_weight_mode)
                weighted_seed_ids.append((row["id"], weight))

            if not weighted_seed_ids:
                print("[run_passage_ppr] No valid seed IDs - aborting walk.")
                return _empty_passage_result()
            weighted_seed_ids = _normalize_seed_weights(weighted_seed_ids)

            try:
                proj = session.run(
                    _CYPHER_PROJECT,
                    graph_name=graph_name,
                    node_query=_build_node_query("entity_chunk"),
                    rel_query=_build_rel_query("entity_chunk"),
                ).single()
                print(f"[run_passage_ppr] Projected '{graph_name}': "
                      f"{proj['nodeCount']} nodes, "
                      f"{proj['relationshipCount']} relationships")

                if seed_weight_mode == "uniform":
                    source_ids = [node_id for node_id, _ in weighted_seed_ids]
                    ppr_rows = list(session.run(
                        _CYPHER_PPR,
                        graph_name=graph_name,
                        source_ids=source_ids,
                        damping=damping,
                        max_iter=max_iterations,
                    ))
                else:
                    combined_scores: dict[int, float] = {}
                    for seed_id, seed_weight in weighted_seed_ids:
                        rows = session.run(
                            _CYPHER_PPR,
                            graph_name=graph_name,
                            source_ids=[seed_id],
                            damping=damping,
                            max_iter=max_iterations,
                        )
                        for row in rows:
                            node_id = row["nodeId"]
                            weighted_score = float(row["score"]) * seed_weight
                            combined_scores[node_id] = (
                                combined_scores.get(node_id, 0) + weighted_score
                            )
                    ppr_rows = [
                        {"nodeId": node_id, "score": score}
                        for node_id, score in combined_scores.items()
                    ]
                    ppr_rows.sort(key=lambda row: row["score"], reverse=True)
            finally:
                session.run(_CYPHER_DROP, graph_name=graph_name).consume()
            chunk_node_ids = {
                row["id"]
                for row in session.run(_CYPHER_CHUNK_NODE_IDS)
            }

            top_chunk_rows = _top_chunk_score_rows(
                ppr_rows,
                chunk_node_ids,
                top_k_chunks,
            )

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

            chunk_ids = [row["nodeId"] for row in top_chunk_rows]
            property_rows = list(session.run(_CYPHER_MAP_CHUNKS, ids=chunk_ids))
            id_to_chunk = {row["id"]: dict(row) for row in property_rows}

            chunks = [
                {
                    "chunk_id": id_to_chunk[row["nodeId"]]["chunk_id"],
                    "text": id_to_chunk[row["nodeId"]]["text"],
                    "ticker": id_to_chunk[row["nodeId"]]["ticker"],
                    "fiscal_year": id_to_chunk[row["nodeId"]]["fiscal_year"],
                    "section": id_to_chunk[row["nodeId"]]["section"],
                    "score": float(row["score"]),
                }
                for row in top_chunk_rows
                if row["nodeId"] in id_to_chunk
            ]

            return {
                "chunks": chunks,
                "ppr_entities": top_entities,
                "projection": {
                    "node_count": proj["nodeCount"],
                    "relationship_count": proj["relationshipCount"],
                },
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
    """Run Personalized PageRank from `seeds` and return top-k entities.

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

    Raises:
        neo4j.exceptions.* — DB errors propagate; the in-memory projection
        is still dropped via the inner `finally`.
    """
    if not seeds:
        print("[run_ppr] No seeds provided.")
        return []

    seed_names: list[str] = [s["name"] for s in seeds]

    cfg = cfg or get_config()
    driver: Driver = get_neo4j_driver(cfg)
    graph_name = f"ppr_{uuid.uuid4().hex[:8]}"

    try:
        with driver.session() as session:
            # Map each seed to its typed Entity node id.
            id_rows = list(session.run(
                _CYPHER_MAP_ID,
                seeds=[
                    {
                        "name": seed["name"],
                        "type": seed["type"],
                    }
                    for seed in seeds
                ]
            ))
            seed_lookup = {
               (seed["name"], seed["type"]): seed
                for seed in seeds
            }
            weighted_seed_ids = []
            for row in id_rows:
                seed = seed_lookup[(row["name"], row["type"])]
                weight = _seed_weight(seed, seed_weight_mode)
                weighted_seed_ids.append((row["id"], weight))

            if not weighted_seed_ids:
                print("[run_ppr] No valid seed IDs - aborting walk.")
                return []
            weighted_seed_ids = _normalize_seed_weights(weighted_seed_ids)

            try:
                proj = session.run(
                    _CYPHER_PROJECT,
                    graph_name=graph_name,
                    node_query=_build_node_query("entity_only"),
                    rel_query=_build_rel_query("entity_only"),
                ).single()
                print(f"[run_ppr] Projected '{graph_name}': "
                      f"{proj['nodeCount']} nodes, "
                      f"{proj['relationshipCount']} relationships")


                # print(f"[run_ppr] PPR over {len(seed_ids)} seeds "
                #       f"(damping={damping}, max_iter={max_iterations}, teleport=uniform)")
                if seed_weight_mode == "uniform":
                    source_ids = [node_id for node_id, _ in weighted_seed_ids]
                    ppr_rows = list(session.run(
                        _CYPHER_PPR,
                        graph_name=graph_name,
                        source_ids=source_ids,
                        damping=damping,
                        max_iter=max_iterations,
                    ))
                else:
                    combined_scores: dict[int, float] = {}
                    for seed_id, seed_weight in weighted_seed_ids:
                        rows = session.run(
                            _CYPHER_PPR,
                            graph_name=graph_name,
                            source_ids=[seed_id],
                            damping=damping,
                            max_iter=max_iterations,
                        )
                        for row in rows:
                            node_id = row["nodeId"]
                            weighted_score = float(row["score"]) * seed_weight
                            combined_scores[node_id] = (
                                combined_scores.get(node_id, 0) + weighted_score
                            )
                    ppr_rows = [
                        {"nodeId": node_id, "score": score}
                        for node_id, score in combined_scores.items()
                    ]
                    ppr_rows.sort(key=lambda row: row["score"], reverse=True)
                    


            finally:
                session.run(_CYPHER_DROP, graph_name=graph_name).consume()

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
