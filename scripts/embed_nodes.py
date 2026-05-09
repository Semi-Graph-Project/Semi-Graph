"""
CLI for Entity node embedding (Phase B2 — Step 1).

Usage:
    # Embed only entities missing `embedding`
    python scripts/embed_nodes.py

    # Re-embed every entity (e.g. after model change)
    python scripts/embed_nodes.py --force

After running, a Neo4j vector index `entity_embedding` exists on
Entity(embedding) for cosine similarity search.
"""
from __future__ import annotations

import argparse
import sys

from semigraph.offline.embed_nodes import embed_entities


def main() -> int:
    parser = argparse.ArgumentParser(description="Embed Entity nodes (Phase B2 Step 1)")
    parser.add_argument("--force", action="store_true",
                        help="re-embed entities that already have an embedding")
    args = parser.parse_args()

    stats = embed_entities(force=args.force)

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Embedded entities: {stats['embedded']} / {stats['total']}")
    print(f"Elapsed:           {stats['elapsed_s']:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
