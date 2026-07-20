#!/usr/bin/env python3
"""Integration-test create/reuse parity against the configured Neo4j GDS."""
from __future__ import annotations

from semigraph.config import get_config
from semigraph.connections import get_neo4j_driver
from semigraph.online.ppr import manage_projection, run_passage_ppr


_CYPHER_PICK_CONNECTED_SEED = """
MATCH (:Chunk)-[:MENTIONS]->(e:Entity)
RETURN e.name AS name, e.type AS type
ORDER BY e.name, e.type
LIMIT 1
"""


def _result_signature(result: dict) -> list[tuple[str, float]]:
    return [
        (str(chunk["chunk_id"]), round(float(chunk["score"]), 12))
        for chunk in result.get("chunks", [])
    ]


def main() -> None:
    cfg = get_config()
    driver = get_neo4j_driver(cfg)
    try:
        with driver.session() as session:
            seed = session.run(_CYPHER_PICK_CONNECTED_SEED).single()
    finally:
        driver.close()

    if seed is None:
        raise RuntimeError("Neo4j has no Chunk-[:MENTIONS]->Entity seed")

    # This only clears the named in-memory GDS projection. Neo4j nodes and
    # relationships are not modified. The second search leaves it prepared.
    manage_projection("drop", "entity_chunk", cfg)
    seeds = [{
        "name": seed["name"],
        "type": seed["type"],
        "similarity": 1.0,
        "specificity": 1.0,
    }]

    first = run_passage_ppr(seeds, cfg=cfg)
    second = run_passage_ppr(seeds, cfg=cfg)

    first_projection = first["projection"]
    second_projection = second["projection"]
    assert first_projection["status"] == "created", first_projection
    assert second_projection["status"] == "reused", second_projection
    assert first_projection["name"] == second_projection["name"]
    assert first_projection["node_count"] > 0
    assert first_projection["relationship_count"] > 0
    assert _result_signature(first) == _result_signature(second)

    print("Projection reuse integration test passed")
    print(f"  name: {second_projection['name']}")
    print(f"  first status: {first_projection['status']}")
    print(f"  second status: {second_projection['status']}")
    print(f"  chunks: {len(second.get('chunks', []))}")


if __name__ == "__main__":
    main()
