import time
from tabulate import tabulate

import numpy as np
from huggingface_hub import snapshot_download
from sentence_transformers import CrossEncoder
import pandas as pd

from semigraph.online.vector_search import trace_vector_search


import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"

query = "What were NVIDIA's main data center revenue drivers in fiscal 2024?"

print("Retrieving real candidates...")
trace = trace_vector_search(
    query,
    top_k_chunks=5,
    candidate_pool_k=24,
)

candidates = trace["raw_chunk_candidates"]

if not candidates:
    raise RuntimeError("No candidates returned from Neo4j")

print(f"Candidates retrieved: {len(candidates)}")

model_path = snapshot_download(
    "jinaai/jina-reranker-v1-tiny-en",
    local_files_only=True,
)

load_started = time.perf_counter()

model = CrossEncoder(
    model_path,
    backend="onnx",
    max_length=2048,
    local_files_only=True,
    model_kwargs={
        "file_name": "onnx/model_quantized.onnx",
        "provider": "CPUExecutionProvider",
    },
)

print(f"Model load: {time.perf_counter() - load_started:.2f} seconds")

pairs = [
    (query, candidate["text"])
    for candidate in candidates
]


print("Warm-up...")
warmup_started = time.perf_counter()

model.predict(
    pairs[:1],
    batch_size=2,
    show_progress_bar=True,
)

print(f"Warm-up time: {time.perf_counter() - warmup_started:.2f} seconds")

print("Measured inference...")
predict_started = time.perf_counter()

scores = model.predict(
    pairs,
    batch_size=2,
    show_progress_bar=True,
)
predict_time = time.perf_counter() - predict_started

print(f"Warm inference: {predict_time:.2f} seconds")

scores = np.asarray(scores, dtype=float).reshape(-1)
ranking = np.argsort(-scores)


print("Ranking results:", ranking)

print("type(ranking):", type(ranking))

print(f"Rerank time: {predict_time:.2f} seconds")
print("\nLocal ONNX Top-5:")

for rank, index in enumerate(ranking[:5], start=1):
    candidate = candidates[index]
    preview = candidate["text"][:160].replace("\n", " ")

    print(
        f"{rank}. "
        f"chunk_id={candidate.get('chunk_id')} "
        f"vector_score={candidate.get('score')} "
        f"onnx_score={scores[index]:.6f}"
    )
    print(f"   {preview}...")

assert len(scores) == len(candidates)
assert np.isfinite(scores).all()

print("\nREAL DATA RERANK TEST PASSED")
