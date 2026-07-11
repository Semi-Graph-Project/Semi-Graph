#!/usr/bin/env python3
"""Run the existing retrieval evaluator against the isolated FinReflectKG DB."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from semigraph.benchmark.finreflectkg import FINREFLECTKG_PPR_REL_TYPES  # noqa: E402


def main() -> None:
    load_dotenv(ROOT / ".env")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--neo4j-uri", default=os.getenv("FINREFLECTKG_NEO4J_URI", "bolt://localhost:7688"))
    parser.add_argument("--tools", nargs="+", choices=("vector", "graph", "hybrid"), default=["vector", "graph"])
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--oracle-k", type=int, default=20)
    parser.add_argument("--candidate-pool-k", type=int, default=100)
    parser.add_argument("--graph-top-k-entities", type=int, default=40)
    parser.add_argument("--graph-damping", type=float, default=0.5)
    parser.add_argument("--version-name", default="finreflectkg_smoke_node_ppr")
    parser.add_argument("--ticker-scope", required=True)
    parser.add_argument(
        "--ppr-seed-weight-mode",
        choices=["uniform", "similarity", "similarity_specificity"],
        default="uniform",
    )
    args = parser.parse_args()

    # Set the target before importing Config; dotenv does not override this.
    os.environ["NEO4J_URI"] = args.neo4j_uri

    from semigraph.config import get_config
    import semigraph.online.ppr as ppr
    import evaluate_retrieval_quality as evaluator

    get_config.cache_clear()
    ppr.PPR_REL_TYPES = list(FINREFLECTKG_PPR_REL_TYPES)

    sys.argv = [
        "scripts/evaluate_retrieval_quality.py",
        "--queries", str(args.queries),
        "--tools", *args.tools,
        "--top-k", str(args.top_k),
        "--oracle-k", str(args.oracle_k),
        "--no-llm-expansion",
        "--graph-seed-mode", "triple",
        "--candidate-pool-k", str(args.candidate_pool_k),
        "--graph-top-k-entities", str(args.graph_top_k_entities),
        "--graph-damping", str(args.graph_damping),
        "--reextract-tickers", args.ticker_scope,
        "--version-name", args.version_name,
        "--ppr-seed-weight-mode", args.ppr_seed_weight_mode,
    ]
    evaluator.main()


if __name__ == "__main__":
    main()

