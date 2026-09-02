#!/usr/bin/env python3
"""Read-only smoke check for the Docker advisor handoff databases."""

from __future__ import annotations

import argparse
from copy import deepcopy
import sys

from semigraph.config import get_config
from semigraph.connections import get_neo4j_driver


TARGETS = ("production", "controlled")


def _target_config(target: str):
    cfg = deepcopy(get_config())
    cfg.neo4j_uri = {
        "production": cfg.production_neo4j_uri,
        "controlled": cfg.controlled_neo4j_uri,
    }[target]
    return cfg


def check_target(target: str) -> dict:
    """Connect and return non-sensitive corpus/plugin facts without writing."""
    cfg = _target_config(target)
    driver = get_neo4j_driver(cfg)
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            counts = session.run(
                """
                CALL { MATCH (n) RETURN count(n) AS nodes }
                CALL { MATCH ()-[r]->() RETURN count(r) AS relationships }
                RETURN nodes, relationships
                """
            ).single(strict=True)
            plugins = session.run(
                "RETURN apoc.version() AS apoc, gds.version() AS gds"
            ).single(strict=True)
    finally:
        driver.close()

    return {
        "target": target,
        "uri": cfg.neo4j_uri,
        "nodes": counts["nodes"],
        "relationships": counts["relationships"],
        "apoc": plugins["apoc"],
        "gds": plugins["gds"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read-only smoke check for Docker handoff Neo4j services"
    )
    parser.add_argument(
        "--target",
        choices=(*TARGETS, "all"),
        default="all",
        help="database to check (default: all)",
    )
    args = parser.parse_args()

    targets = TARGETS if args.target == "all" else (args.target,)
    failed = False
    for target in targets:
        try:
            result = check_target(target)
        except Exception as exc:
            failed = True
            print(f"[FAIL] {target}: {type(exc).__name__}: {exc}")
            continue

        print(
            f"[OK] {result['target']} {result['uri']} | "
            f"nodes={result['nodes']:,} "
            f"relationships={result['relationships']:,} | "
            f"APOC={result['apoc']} GDS={result['gds']}"
        )

    if failed:
        return 1
    print("Handoff smoke passed. No database records were changed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
