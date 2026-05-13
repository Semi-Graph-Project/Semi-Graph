"""
Personalized PageRank walker for Phase C1b — seeds → ranked entities.

Receives seeds from `query_to_seeds()` (Phase C1a) and runs Personalized
PageRank via GDS, biasing the walk toward seed neighborhoods so the top-k
reflects query-relevant entities rather than global graph hubs.

Only informative domain (Entity↔Entity) relationships are projected — see
`INFORMATIVE_REL_TYPES` in `offline/specificity.py`. Provenance edges
(`MENTIONS`, `HAS_CHUNK`, `HAS_SECTION`) and linkage edges (`SYNONYM_OF`)
are excluded. Including provenance would let mass leak into Chunk/Section
nodes and flatten entity rankings within a few power-iteration rounds.

GDS 2.x requires a named projection — `gds.pageRank.stream(graphName, config)`
does NOT accept anonymous `nodeQuery`/`relationshipQuery` in its config map.
Each call creates a uniquely-named ephemeral projection and drops it in a
`finally` block so a failed PPR run does not leak in-memory graphs.

Output of `run_ppr()` is the input to Phase C1c, which maps ranked entities
back to chunks.
"""
from __future__ import annotations

import uuid
from typing import Optional

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
MATCH (e:Entity)
WHERE e.name IN $names
RETURN id(e) AS id, e.name AS name
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


def run_ppr(
    seeds: list[dict],
    top_k: int = 20,
    damping: float = 0.85,
    max_iterations: int = 20,
    cfg: Optional[Config] = None,
) -> list[dict]:
    """Run Personalized PageRank from `seeds` and return top-k entities.

    Args:
        seeds: Output of `query_to_seeds()` — each dict has at least `name`.
        top_k: Number of top-scoring entities to return.
        damping: PageRank damping factor (0.85 = HippoRAG default).
        max_iterations: Power-iteration cap.
        cfg: Optional Config; defaults to cached singleton.

    Returns:
        List of dicts sorted by PPR score desc, each: `{name, type, score}`.
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
            # Map Seed to ID => Prepare Qry
            id_rows = list(session.run(_CYPHER_MAP_ID, names=seed_names))
            seed_ids: list[int] = [row["id"] for row in id_rows]
            found_names = {row["name"] for row in id_rows}
            missing = sorted(set(seed_names) - found_names)
            if missing:
                print(f"[run_ppr] {len(missing)} seed(s) not in graph: {missing}")

            if not seed_ids:
                print("[run_ppr] No valid seed IDs — aborting walk.")
                return []

            try:
                proj = session.run(
                    _CYPHER_PROJECT,
                    graph_name=graph_name,
                    rel_query=_build_rel_query(),
                ).single()
                print(f"[run_ppr] Projected '{graph_name}': "
                      f"{proj['nodeCount']} nodes, "
                      f"{proj['relationshipCount']} relationships")

                print(f"[run_ppr] PPR over {len(seed_ids)} seeds "
                      f"(damping={damping}, max_iter={max_iterations})")
                ppr_rows = list(session.run(
                    _CYPHER_PPR,
                    graph_name=graph_name,
                    source_ids=seed_ids,
                    damping=damping,
                    max_iter=max_iterations,
                ))
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
