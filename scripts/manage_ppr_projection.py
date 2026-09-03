#!/usr/bin/env python3
"""Inspect and manage reusable GDS projections used by PPR retrieval."""
from __future__ import annotations

import argparse
import json

from semigraph.online.ppr import manage_projection


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        choices=("status", "prepare", "refresh", "drop"),
        help="Projection lifecycle action.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = manage_projection(args.action)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
