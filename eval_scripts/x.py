#!/usr/bin/env python3
"""Minimal Question -> Embedding -> Neo4j Vector Search workbench."""

from pathlib import Path
import json
import sys
import statistics
import time

from dotenv import load_dotenv
import yaml


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from semigraph.config import get_config  # noqa: E402
from semigraph.connections import get_llm  # noqa: E402
from semigraph.online.vector_search import vector_search as production_vector_search  # noqa: E402


NEO4J_URI = "bolt://localhost:7690"
VECTOR_INDEX = "gold_chunk_embedding"
TOP_K = 9
SOX_DATASET = ROOT / "benchmark/freezes/sox74_retrieval_ablation_v1/inputs/finreflectkg_sox_strict74.yaml"
SOX_QUERY_COUNT = 74
TRACE_OUTPUT = ROOT / "benchmark/results/controlled_vector_sox74.jsonl"



def load_sox_queries() -> list[dict]:
    """Load the 74 SOX benchmark queries from YAML."""
    with SOX_DATASET.open(encoding="utf-8") as file:
        dataset = yaml.safe_load(file)

    queries = dataset["queries"]
    if len(queries) != SOX_QUERY_COUNT:
        raise ValueError(f"Expected {SOX_QUERY_COUNT} queries, got {len(queries)}")
    return queries



answer_point = load_sox_queries()

# print(len(answer_point[0]["answer_points"][0]))

ans_point = [len(ans["answer_points"][0]) for ans in answer_point]


print("Min answer points:", min(ans_point))
print("Max answer points:", max(ans_point))
print("Mean answer points:", statistics.mean(ans_point))
print("Median answer points:", statistics.median(ans_point))
print("Mode answer points:", statistics.mode(ans_point))
print("Standard deviation answer points:", statistics.stdev(ans_point))
print("Variance answer points:", statistics.variance(ans_point))
print("Sum answer points:", sum(ans_point))
