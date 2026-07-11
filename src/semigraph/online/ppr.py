
from __future__ import annotations

import uuid
from typing import Literal, Optional

from neo4j import Driver

from semigraph.config import Config, get_config
from semigraph.connections import get_neo4j_driver
from semigraph.offline.specificity import INFORMATIVE_REL_TYPES
from semigraph.online.seed import query_to_seeds


# Re-export from Phase B3 (single source of truth in specificity.py).
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
    'MATCH (n:Entity) RETURN id(n) AS id',
    $rel_query
)
YIELD graphName, nodeCount, relationshipCount
RETURN graphName, nodeCount, relationshipCount
"""

_CYPHER_PPR = """
CALL gds.pageRank.stream($graph_name, {
    sourceNodes: $source_ids,
    dampingFactor: $damping,
    maxIterations: $max_iter
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

SeedWeightMode = Literal[
    "uniform",
    "similarity",
    "similarity_specificity",
]

PPRGraphMode = Literal[
    "entity_only", 
    "entity_chunk",
]

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


def _build_rel_query() -> str:
    # Inner Cypher of `gds.graph.project.cypher` is parsed in its own context
    # and cannot reference outer parameters, so rel types are inlined.
    # PPR_REL_TYPES is a module constant (not user input) — safe.
    rels_inline = ", ".join(f'"{t}"' for t in PPR_REL_TYPES)
    return (
        f"MATCH (s:Entity)-[r]-(t:Entity) "
        f"WHERE type(r) IN [{rels_inline}] "
        f"RETURN id(s) AS source, id(t) AS target"
    )

def _build_node_query(graph_mode: PPRGraphMode) -> str:
    """
     Cypher Slec
    """
    if graph_mode == "entity_only":
        return "MATCH (n:Entity) RETURN id(n) AS id"

    if graph_mode == "entity_chunk":
        return (
            "MATCH (n) "
            "WHERE n:Entity OR n:Chunk "
            "RETURN id(n) AS id"
        )

    raise ValueError(f"Unknown PPR graph mode: {graph_mode}")


def run_ppr(
    seeds: list[dict],
    top_k: int = 20,
    damping: float = 0.85,
    max_iterations: int = 20,
    seed_weight_mode: SeedWeightMode = "uniform",
    graph_mode: str = "entity_only",
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
                    rel_query=_build_rel_query(),
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
