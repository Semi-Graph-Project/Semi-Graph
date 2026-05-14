"""
CLI for relationship-triple embedding (Phase C1b+ — HippoRAG v2 alignment).

Usage:
    # Embed only triples missing `triple_embedding`
    python scripts/embed_triples.py

    # Re-embed every informative triple (e.g. after model change)
    python scripts/embed_triples.py --force

After running, every informative Entity-Entity relationship carries a
`triple_embedding` property (768-dim, BGE). `online.seed.query_to_triple_seeds()`
loads these into memory for cosine search.
"""
from __future__ import annotations

import argparse
import sys

from semigraph.offline.embed_triples import embed_triples


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Embed informative-relationship triples (Phase C1b+)")
    parser.add_argument("--force", action="store_true",
                        help="re-embed triples that already have a triple_embedding")
    parser.add_argument("--batch-size", type=int, default=200,
                        help="UNWIND batch size for write-back (default: 200)")
    args = parser.parse_args()

    stats = embed_triples(force=args.force, write_batch=args.batch_size)

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Embedded triples: {stats['embedded']} / {stats['total']}")
    print(f"Elapsed:          {stats['elapsed_s']:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
