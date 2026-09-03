from __future__ import annotations

from typing import Optional

from neo4j import Driver

from semigraph.config import Config, get_config
from semigraph.connections import get_neo4j_driver


INFORMATIVE_REL_TYPES: list[str] = get_config().informative_rel_types


def compute_specificity(
    rel_types: Optional[list[str]] = None,
    cfg: Optional[Config] = None,
) -> dict:
    """
    Compute and write `specificity` property on every Entity node.
    """
    cfg = cfg or get_config()
    types = rel_types if rel_types is not None else INFORMATIVE_REL_TYPES

    cypher = """
    MATCH (e:Entity)
    OPTIONAL MATCH (e)-[r]-(other:Entity)
    WHERE type(r) IN $rel_types
    WITH e, count(r) AS degree
    SET e.specificity = CASE
        WHEN degree = 0 THEN 1.0
        ELSE 1.0 / log(degree + 1.0)
    END
    WITH collect(e.specificity) AS specs
    RETURN size(specs) AS updated,
           reduce(m = 999.0, s IN specs | CASE WHEN s < m THEN s ELSE m END) AS min,
           reduce(m = 0.0,   s IN specs | CASE WHEN s > m THEN s ELSE m END) AS max,
           reduce(t = 0.0,   s IN specs | t + s) / size(specs) AS avg
    """

    driver: Driver = get_neo4j_driver(cfg)
    try:
        print(f"[specificity] computing — {len(types)} informative rel types")
        with driver.session() as s:
            result = s.run(cypher, rel_types=types).single()

        stats = {
            "updated": result["updated"],
            "min": result["min"],
            "max": result["max"],
            "avg": result["avg"],
        }
        print(f"[specificity] DONE — updated {stats['updated']} entities "
              f"(min={stats['min']:.4f}, max={stats['max']:.4f}, avg={stats['avg']:.4f})")
        return stats
    finally:
        driver.close()
