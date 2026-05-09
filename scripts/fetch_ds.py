"""
Inspect FinReflectKG and extract SOX-semiconductor subset locally.

Available datasets on HuggingFace:
  - domyn/FinReflectKG          : 17.5M triples (the actual graph)
  - domyn/FinReflectKG-EvalBench: 480K triple-quality evaluations
NOT released yet: the 555-pair MultiHop QA benchmark from the paper.

Strategy:
  1. Download each parquet shard locally first (with retry).
  2. Filter for SOX rows from local file (no network).
  3. Resume-able: skips shards already downloaded.
  4. Outputs SOX-only parquet for downstream use.

Usage:
  python scripts/fetch_ds.py                # full run (103 shards, ~30 min)
  python scripts/fetch_ds.py --max 5        # quick test (5 shards)
"""

import argparse
import os
import sys
import time
import pyarrow as pa
import pyarrow.parquet as pq
from huggingface_hub import HfApi, hf_hub_download

SOX_TICKERS = [
    "NVDA", "AMD", "INTC", "AVGO", "TXN", "AMAT",
    "QCOM", "ADI", "MU", "MRVL", "MCHP", "KLAC", "LRCX",
]
REPO_ID = "domyn/FinReflectKG"
CACHE_DIR = "data/finreflectkg_cache"
OUTPUT_PATH = "data/finreflectkg_sox.parquet"


def list_shards():
    api = HfApi()
    files = api.list_repo_files(REPO_ID, repo_type="dataset")
    return sorted(f for f in files if f.startswith("data/") and f.endswith(".parquet"))


def download_shard(shard_path: str, retries: int = 3) -> str:
    """Download to local cache and return local path."""
    for attempt in range(retries):
        try:
            local = hf_hub_download(
                repo_id=REPO_ID,
                filename=shard_path,
                repo_type="dataset",
                cache_dir=CACHE_DIR,
            )
            return local
        except Exception as e:
            wait = 5 * (attempt + 1)
            print(f"  retry {attempt + 1}/{retries} after {wait}s ({e.__class__.__name__})", flush=True)
            time.sleep(wait)
    raise RuntimeError(f"Failed to download {shard_path}")


def filter_sox(local_path: str) -> pa.Table:
    """Filter local parquet for SOX tickers using predicate pushdown."""
    return pq.read_table(local_path, filters=[("ticker", "in", SOX_TICKERS)])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=None, help="max shards to process")
    args = ap.parse_args()

    os.makedirs(CACHE_DIR, exist_ok=True)
    os.makedirs("data", exist_ok=True)

    shards = list_shards()
    if args.max:
        shards = shards[:args.max]
    print(f"Processing {len(shards)} shards", flush=True)

    sox_tables = []
    total_sox = 0
    start = time.time()

    for i, shard in enumerate(shards, 1):
        try:
            local = download_shard(shard)
            table = filter_sox(local)
            n = table.num_rows
            total_sox += n
            tickers = set(table["ticker"].to_pylist()) if n else set()
            elapsed = time.time() - start
            print(f"[{i:>3}/{len(shards)}] {os.path.basename(shard)}: "
                  f"{n:>5} SOX rows ({elapsed/60:.1f} min) {tickers}",
                  flush=True)
            if n > 0:
                sox_tables.append(table)
        except Exception as e:
            print(f"[{i:>3}/{len(shards)}] ERROR: {e}", flush=True)

    if not sox_tables:
        print("No SOX rows found.")
        sys.exit(0)

    combined = pa.concat_tables(sox_tables)
    pq.write_table(combined, OUTPUT_PATH)
    print(f"\nSaved {total_sox:,} SOX rows → {OUTPUT_PATH}", flush=True)

    df = combined.to_pandas()
    print("\nPer-ticker coverage:")
    for t in SOX_TICKERS:
        sub = df[df["ticker"] == t]
        if len(sub):
            print(f"  {t}: {len(sub):>7,} triples, years: {sorted(sub['year'].unique())}")
        else:
            print(f"  {t}: NOT FOUND")


if __name__ == "__main__":
    main()
