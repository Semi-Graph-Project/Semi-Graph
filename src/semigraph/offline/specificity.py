"""
Compute Node Specificity for Phase B3 — the final piece of Phase B.

Each Entity gets a `specificity` property = 1 / log(degree + 1), where `degree`
counts only **informative** edges (domain knowledge). Provenance edges
(`MENTIONS`, `HAS_CHUNK`, `HAS_SECTION`) and linkage edges (`SYNONYM_OF`) are
excluded — otherwise every entity would inherit chunk-level mass and the
specificity signal would collapse.

Specificity is used in Phase C1 as the seed weight for Personalized PageRank:
hub entities (e.g. `china`, `united states`, `revenue`) get low weight so the
walk doesn't get stuck on overconnected topical anchors; rare entities act as
strong seeds when the query lands on one.

Formula choice:
  1 / log(degree + 1)  for degree >= 1   (gradual decay — HippoRAG style)
  1.0                  for degree == 0   (placeholder; won't seed PPR anyway)

`log` here is natural log (Cypher's `log()` is `ln`). Computed in a single
Cypher write so 3,620 entities update atomically with one round-trip.
"""
from __future__ import annotations

from typing import Optional

from neo4j import Driver

from semigraph.config import Config, get_config
from semigraph.connections import get_neo4j_driver


# All Entity↔Entity domain relationship types. MENTIONS / HAS_* (provenance)
# and SYNONYM_OF (linkage) are intentionally excluded so the signal reflects
# actual knowledge density, not corpus chatter.
INFORMATIVE_REL_TYPES: list[str] = [
    "ANNOUNCES",
    "CAUSES_SHORTAGE_OF",
    "COMPETES_WITH",
    "DEPENDS_ON",
    "DISCLOSES",
    "FACES",
    "GUIDES_ON",
    "HAS_STAKE_IN",
    "IMPACTED_BY",
    "IMPACTS",
    "INTRODUCES",
    "INVESTS_IN",
    "INVOLVED_IN",
    "LISTED_ON",
    "NEGATIVELY_IMPACTS",
    "OPERATES_IN",
    "PARTNERS_WITH",
    "POSITIVELY_IMPACTS",
    "PRODUCES",
    "SUBJECT_TO",
    "SUPPLIES",
]


def compute_specificity(
    rel_types: Optional[list[str]] = None,
    cfg: Optional[Config] = None,
) -> dict:
    """
    Compute and write `specificity` property on every Entity node.

    Args:
        rel_types: which relationship types count toward degree.
                   Defaults to INFORMATIVE_REL_TYPES.
        cfg:       config; defaults to cached singleton.

    Returns:
        stats dict — {updated, min, max, avg}
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
