"""
CLI for synonymy edge construction (Phase B2 — Step 2-3).

Usage:
    # Default: cosine_min=0.65, types = ORG/COMP/PRODUCT/GPE/RAW_MATERIAL/FIN_MARKET/SEGMENT
    python scripts/build_synonymy.py

    # Dry run — show what would be written, but don't touch graph
    python scripts/build_synonymy.py --dry-run

    # Tighter candidate filter
    python scripts/build_synonymy.py --cosine-min 0.75

    # Restrict to ORG only
    python scripts/build_synonymy.py --types ORG

After running, :SYNONYM_OF edges exist between entities of the same type that
satisfy at least one of: substring / acronym / token-set ≥ 0.85 / cosine ≥ 0.92.
"""
from __future__ import annotations

import argparse
import sys

from semigraph.offline.synonymy import DEFAULT_SYNONYMY_TYPES, build_synonymy


def main() -> int:
    parser = argparse.ArgumentParser(description="Build SYNONYM_OF edges (Phase B2)")
    parser.add_argument("--cosine-min", type=float, default=0.65,
                        help="cosine threshold for candidate selection (default 0.65)")
    parser.add_argument("--types", nargs="*", default=None,
                        help=f"entity types to consider (default: {sorted(DEFAULT_SYNONYMY_TYPES)})")
    parser.add_argument("--dry-run", action="store_true",
                        help="compute pairs but don't write edges (for tuning)")
    parser.add_argument("--show-pairs", type=int, default=0,
                        help="print first N synonym pairs (useful with --dry-run)")
    args = parser.parse_args()

    types = frozenset(args.types) if args.types else None

    stats = build_synonymy(
        cosine_min=args.cosine_min,
        types=types,
        dry_run=args.dry_run,
    )

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Candidates (cos >= {args.cosine_min}): {stats['candidates']}")
    print(f"Synonym pairs (after rules):     {stats['synonyms']}")
    print(f"Edges written:                   {stats['written']}")
    if stats.get("by_rule"):
        print(f"By rule:                         {stats['by_rule']}")

    if args.show_pairs and stats.get("pairs"):
        print("\n" + "-" * 60)
        print(f"First {min(args.show_pairs, len(stats['pairs']))} pairs:")
        print("-" * 60)
        for p in stats["pairs"][:args.show_pairs]:
            print(f"  [{p['rule']:9s}] {p['name_a']:35s} ↔ {p['name_b']:35s}  "
                  f"cos={p['cosine']:.3f} score={p['score']:.3f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
