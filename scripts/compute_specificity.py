"""
CLI for Node Specificity computation (Phase B3).

Usage:
    # Default: count all informative rel types
    python scripts/compute_specificity.py

    # Override rel types (comma-separated)
    python scripts/compute_specificity.py --rel-types COMPETES_WITH,PRODUCES,DEPENDS_ON

After running, every `:Entity` has a `specificity` float property used as
seed weight in PPR retrieval (Phase C1).
"""
from __future__ import annotations

import argparse
import sys

from semigraph.connections import get_neo4j_driver
from semigraph.offline.specificity import INFORMATIVE_REL_TYPES, compute_specificity


def _print_extremes(top_n: int = 5) -> None:
    """Sanity check: top hubs (lowest spec) + top leaves (highest spec)."""
    driver = get_neo4j_driver()
    try:
        with driver.session() as s:
            hubs = s.run(
                "MATCH (e:Entity) WHERE e.specificity IS NOT NULL "
                "RETURN e.name AS name, e.type AS type, e.specificity AS s "
                "ORDER BY e.specificity ASC LIMIT $n",
                n=top_n,
            ).data()
            leaves = s.run(
                "MATCH (e:Entity) WHERE e.specificity IS NOT NULL "
                "RETURN e.name AS name, e.type AS type, e.specificity AS s "
                "ORDER BY e.specificity DESC LIMIT $n",
                n=top_n,
            ).data()

        print("\n" + "-" * 60)
        print(f"Top {top_n} HUBS (lowest specificity — over-connected)")
        print("-" * 60)
        for h in hubs:
            print(f"  {h['s']:.4f}  {h['name']:35s}  ({h['type']})")

        print("\n" + "-" * 60)
        print(f"Top {top_n} LEAVES (highest specificity — most specific)")
        print("-" * 60)
        for l in leaves:
            print(f"  {l['s']:.4f}  {l['name']:35s}  ({l['type']})")
    finally:
        driver.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute Node Specificity (Phase B3)")
    parser.add_argument("--rel-types", default=None,
                        help=f"comma-separated rel types (default: {len(INFORMATIVE_REL_TYPES)} informative types)")
    parser.add_argument("--no-preview", action="store_true",
                        help="skip top-hubs / top-leaves preview")
    args = parser.parse_args()

    rel_types = (
        [t.strip().upper() for t in args.rel_types.split(",")]
        if args.rel_types
        else None
    )

    stats = compute_specificity(rel_types=rel_types)

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Entities updated: {stats['updated']}")
    print(f"Specificity range: [{stats['min']:.4f}, {stats['max']:.4f}]")
    print(f"Average:           {stats['avg']:.4f}")

    if not args.no_preview:
        _print_extremes(top_n=5)

    return 0


if __name__ == "__main__":
    sys.exit(main())
