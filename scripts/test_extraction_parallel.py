"""
Parallel smoke test for LLM extraction — ThreadPoolExecutor + retry on 429.

Compared to test_extraction_smoke.py (sequential), this:
  - runs N chunks concurrently via ThreadPoolExecutor
  - retries on rate-limit / API errors with exponential backoff
  - reports speedup vs sequential baseline

Usage:
    python scripts/test_extraction_parallel.py
    python scripts/test_extraction_parallel.py --section Item_1A --num-chunks 10 --workers 8
"""
from __future__ import annotations

import argparse
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from langchain_community.callbacks.manager import get_openai_callback
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from semigraph.config import get_config
from semigraph.connections import get_llm
from semigraph.offline.chunker import chunk_section
from semigraph.offline.kg_extract import extract_chunk


DEEPSEEK_INPUT_PRICE = 0.14 / 1_000_000
DEEPSEEK_OUTPUT_PRICE = 0.28 / 1_000_000


# Retry on any API/network exception. Specific 429 detection happens via
# message inspection — DeepSeek raises generic exceptions through openai SDK.
@retry(
    retry=retry_if_exception_type(Exception),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(5),
    reraise=True,
)
def _extract_with_metrics(chunk, section: str, llm) -> dict:
    """
    One worker call: extract chunk + capture token usage.
    Each thread runs its own get_openai_callback context (thread-local).
    """
    t0 = time.time()
    with get_openai_callback() as cb:
        result = extract_chunk(chunk.text, section=section, llm=llm)
    return {
        "chunk_id": chunk.chunk_id,
        "char_count": chunk.char_count,
        "result": result,
        "input_tokens": cb.prompt_tokens,
        "output_tokens": cb.completion_tokens,
        "elapsed": time.time() - t0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", default="NVDA")
    parser.add_argument("--fiscal-year", default="2026")
    parser.add_argument("--section", default="Item_1",
                        choices=["Item_1", "Item_1A", "Item_5", "Item_7", "Item_8"])
    parser.add_argument("--num-chunks", type=int, default=3)
    parser.add_argument("--workers", type=int, default=4,
                        help="ThreadPool workers (default 4 — safe for DeepSeek)")
    args = parser.parse_args()

    cfg = get_config()
    print(f"\n=== LLM Config ===")
    print(f"  Provider:    {cfg.llm_provider}")
    print(f"  Model:       {cfg.llm_model}")
    print(f"  Temperature: {cfg.llm_temperature}")
    print(f"  Workers:     {args.workers}")
    llm = get_llm()

    filing_dir = cfg.processed_dir / args.ticker / f"FY{args.fiscal_year}-10K"
    section_file = filing_dir / f"{args.section}.md"
    if not section_file.exists():
        print(f"[FAIL] Section file not found: {section_file}")
        return

    text = section_file.read_text(encoding="utf-8")
    chunks = chunk_section(
        text=text,
        ticker=args.ticker,
        fiscal_year=args.fiscal_year,
        section=args.section,
    )
    n = min(args.num_chunks, len(chunks))
    print(f"\n=== Chunking ===")
    print(f"  Total chunks: {len(chunks)}")
    print(f"  Testing first {n} chunk(s) with {args.workers} workers")

    # ---------------------- Parallel execution ----------------------
    print(f"\n=== Running in parallel ===")
    wall_start = time.time()

    futures_to_idx = {}
    results_by_idx: dict[int, dict] = {}

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        for i, chunk in enumerate(chunks[:n]):
            future = executor.submit(_extract_with_metrics, chunk, args.section, llm)
            futures_to_idx[future] = i

        for future in as_completed(futures_to_idx):
            idx = futures_to_idx[future]
            try:
                results_by_idx[idx] = future.result()
                r = results_by_idx[idx]
                print(
                    f"  [chunk {idx + 1}/{n}] {len(r['result'].nodes)} nodes, "
                    f"{len(r['result'].relationships)} rels  |  "
                    f"{r['input_tokens']:,} in / {r['output_tokens']:,} out  |  "
                    f"{r['elapsed']:.1f}s"
                )
            except Exception as e:
                print(f"  [chunk {idx + 1}/{n}] FAILED after retries: {e}")

    wall_elapsed = time.time() - wall_start

    # ---------------------- Aggregate ----------------------
    all_nodes_by_type: dict[str, list[str]] = defaultdict(list)
    all_rels: list[tuple[str, str, str]] = []
    total_input = 0
    total_output = 0
    total_per_chunk_time = 0.0
    success = 0

    for idx in sorted(results_by_idx):
        r = results_by_idx[idx]
        for n_ in r["result"].nodes:
            all_nodes_by_type[n_.type].append(n_.id)
        for rel in r["result"].relationships:
            all_rels.append((rel.source, rel.type, rel.target))
        total_input += r["input_tokens"]
        total_output += r["output_tokens"]
        total_per_chunk_time += r["elapsed"]
        success += 1

    total_tokens = total_input + total_output
    total_cost = total_input * DEEPSEEK_INPUT_PRICE + total_output * DEEPSEEK_OUTPUT_PRICE

    print(f"\n=== Aggregated ({success}/{n} succeeded) ===")
    print(f"  Total nodes: {sum(len(v) for v in all_nodes_by_type.values())} "
          f"({len(all_nodes_by_type)} unique types)")
    print(f"  Total rels:  {len(all_rels)}")

    print(f"\n=== Token / Cost / Time ===")
    print(f"  Input tokens:      {total_input:,}")
    print(f"  Output tokens:     {total_output:,}")
    print(f"  Total tokens:      {total_tokens:,}")
    print(f"  Total cost:        ${total_cost:.5f}")
    print(f"  Sum of per-chunk:  {total_per_chunk_time:.1f}s  (sequential equivalent)")
    print(f"  Wall-clock time:   {wall_elapsed:.1f}s  (parallel actual)")
    if wall_elapsed > 0:
        print(f"  Speedup:           {total_per_chunk_time / wall_elapsed:.2f}x")
        print(f"  Throughput:        {success / wall_elapsed * 60:.1f} chunks/min")

    # Project to full corpus
    if success > 0:
        chunks_3co = 3 * 3 * 120
        chunks_28co = 28 * 3 * 120
        avg_cost = total_cost / success
        avg_wall = wall_elapsed / success  # parallel-aware

        print(f"\n  Projected (with {args.workers} workers):")
        print(f"    3-company scope ({chunks_3co:,} chunks):  "
              f"~${avg_cost * chunks_3co:.2f}  |  ~{avg_wall * chunks_3co / 60:.0f} min")
        print(f"    28-company scope ({chunks_28co:,} chunks): "
              f"~${avg_cost * chunks_28co:.2f}  |  ~{avg_wall * chunks_28co / 60:.0f} min")

    # Sample nodes
    print(f"\n=== Top entity types ===")
    for type_ in sorted(all_nodes_by_type.keys(), key=lambda t: -len(all_nodes_by_type[t]))[:5]:
        ids = all_nodes_by_type[type_]
        unique = sorted(set(ids))
        print(f"  [{type_}] {len(ids)} hits, {len(unique)} unique")
        for nid in unique[:5]:
            print(f"      {nid}")


if __name__ == "__main__":
    main()
