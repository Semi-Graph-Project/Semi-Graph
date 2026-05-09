"""
CLI entry point for chunk embedding (Phase B1).

Usage:
    # Embed only chunks missing `embedding`
    python scripts/embed_chunks.py

    # Re-embed every chunk (e.g. after model change)
    python scripts/embed_chunks.py --force

After running, a Neo4j vector index `chunk_embedding` exists on Chunk(embedding)
for cosine similarity search.
"""
from __future__ import annotations

import argparse
import sys

from semigraph.offline.embed_chunks import embed_chunks


def main() -> int:
    parser = argparse.ArgumentParser(description="Embed Chunk nodes (Phase B1)")
    parser.add_argument("--force", action="store_true",
                        help="re-embed chunks that already have an embedding")
    args = parser.parse_args()

    stats = embed_chunks(force=args.force)

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Embedded chunks: {stats['embedded']} / {stats['total']}")
    print(f"Elapsed:         {stats['elapsed_s']:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
