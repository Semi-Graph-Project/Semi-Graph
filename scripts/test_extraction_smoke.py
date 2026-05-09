"""
Smoke test for LLM-only KG extraction on real NVDA 10-K chunks.

Usage:
    python scripts/test_extraction_smoke.py
    python scripts/test_extraction_smoke.py --section Item_1A --num-chunks 5
    python scripts/test_extraction_smoke.py --ticker AMD --fiscal-year 2024
"""
from __future__ import annotations

import argparse
import time
from collections import defaultdict

from langchain_community.callbacks.manager import get_openai_callback

from semigraph.config import get_config
from semigraph.connections import get_llm
from semigraph.offline.chunker import chunk_section
from semigraph.offline.kg_extract import extract_chunk


# DeepSeek pricing (USD per 1M tokens) — approximate
DEEPSEEK_INPUT_PRICE = 0.14 / 1_000_000
DEEPSEEK_OUTPUT_PRICE = 0.28 / 1_000_000


# Sanity-check anchors — entities we EXPECT to find
EXPECTED_ANCHORS = {
    "Item_1": [
        ("nvidia", "ORG"),
        ("data center", None),
        ("gaming", None),
    ],
    "Item_1A": [
        ("china", "GPE"),
        ("tsmc", None),
    ],
    "Item_7": [
        ("revenue", None),
        ("gross margin", None),
    ],
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", default="NVDA")
    parser.add_argument("--fiscal-year", default="2026")
    parser.add_argument("--section", default="Item_1",
                        choices=["Item_1", "Item_1A", "Item_5", "Item_7", "Item_8"])
    parser.add_argument("--num-chunks", type=int, default=3,
                        help="How many chunks to test (default 3)")
    args = parser.parse_args()

    cfg = get_config()
    print(f"\n=== LLM Config ===")
    print(f"  Provider:  {cfg.llm_provider}")
    print(f"  Model:     {cfg.llm_model}")
    print(f"  Base URL:  {cfg.llm_base_url}")
    print(f"  Temperature: {cfg.llm_temperature}")
    llm = get_llm()
    filing_dir = cfg.processed_dir / args.ticker / f"FY{args.fiscal_year}-10K"
    section_file = filing_dir / f"{args.section}.md"

    if not section_file.exists():
        print(f"[FAIL] Section file not found: {section_file}")
        return

    text = section_file.read_text(encoding="utf-8")
    print(f"\n=== Section file ===")
    print(f"  Path:      {section_file}")
    print(f"  Length:    {len(text):,} chars")

    chunks = chunk_section(
        text=text,
        ticker=args.ticker,
        fiscal_year=args.fiscal_year,
        section=args.section,
    )
    print(f"\n=== Chunking ===")
    print(f"  Total chunks: {len(chunks)}")
    print(f"  Testing first {min(args.num_chunks, len(chunks))} chunk(s)")

    all_nodes_by_type: dict[str, list[str]] = defaultdict(list)
    all_rels: list[tuple[str, str, str]] = []

    total_input_tokens = 0
    total_output_tokens = 0
    total_elapsed = 0.0

    for i, chunk in enumerate(chunks[: args.num_chunks]):
        print(f"\n--- Chunk {i + 1}/{args.num_chunks} ({chunk.char_count} chars) ---")
        print(f"  Preview: {chunk.text[:150]}...")

        t0 = time.time()
        with get_openai_callback() as cb:
            result = extract_chunk(chunk.text, section=args.section, llm=llm)
        elapsed = time.time() - t0

        in_tok = cb.prompt_tokens
        out_tok = cb.completion_tokens
        total_input_tokens += in_tok
        total_output_tokens += out_tok
        total_elapsed += elapsed

        chunk_cost = in_tok * DEEPSEEK_INPUT_PRICE + out_tok * DEEPSEEK_OUTPUT_PRICE
        print(f"  → {len(result.nodes)} nodes, {len(result.relationships)} relationships")
        print(f"  Tokens: input={in_tok:,}  output={out_tok:,}  total={in_tok + out_tok:,}")
        print(f"  Time:   {elapsed:.2f}s  |  Cost: ${chunk_cost:.5f}")

        # Show nodes by type
        by_type: dict[str, list[str]] = defaultdict(list)
        for n in result.nodes:
            by_type[n.type].append(n.id)
            all_nodes_by_type[n.type].append(n.id)

        for type_, ids in sorted(by_type.items()):
            preview = ", ".join(ids[:5])
            more = f" (+{len(ids) - 5} more)" if len(ids) > 5 else ""
            print(f"    [{type_}] {preview}{more}")

        # Show sample relationships
        for r in result.relationships[:5]:
            print(f"    ({r.source} :{r.source_type}) -[:{r.type}]-> ({r.target} :{r.target_type})")
            all_rels.append((r.source, r.type, r.target))
        if len(result.relationships) > 5:
            print(f"    ... (+{len(result.relationships) - 5} more)")

    # Aggregated summary
    n = min(args.num_chunks, len(chunks))
    total_tokens = total_input_tokens + total_output_tokens
    total_cost = total_input_tokens * DEEPSEEK_INPUT_PRICE + total_output_tokens * DEEPSEEK_OUTPUT_PRICE

    print(f"\n=== Aggregated across {n} chunks ===")
    total_nodes = sum(len(v) for v in all_nodes_by_type.values())
    print(f"  Total nodes:  {total_nodes} ({len(all_nodes_by_type)} unique types)")
    print(f"  Total rels:   {len(all_rels)}")
    print(f"\n=== Token / Cost summary ===")
    print(f"  Input tokens:  {total_input_tokens:,}")
    print(f"  Output tokens: {total_output_tokens:,}")
    print(f"  Total tokens:  {total_tokens:,}")
    print(f"  Total time:    {total_elapsed:.2f}s  ({total_elapsed/n:.2f}s/chunk avg)")
    print(f"  Total cost:    ${total_cost:.5f}  (${total_cost/n:.5f}/chunk avg)")
    # Project to full corpus
    chunks_full = 28 * 3 * 120  # 28 companies × 3 years × ~120 chunks
    print(f"\n  Projected for full corpus ({chunks_full:,} chunks):")
    print(f"    ~${total_cost / n * chunks_full:.2f}  |  ~{total_elapsed / n * chunks_full / 60:.0f} min sequential")

    print(f"\n  By type:")
    for type_ in sorted(all_nodes_by_type.keys(), key=lambda t: -len(all_nodes_by_type[t])):
        ids = all_nodes_by_type[type_]
        unique = sorted(set(ids))
        print(f"    [{type_}] {len(ids)} hits, {len(unique)} unique")
        for nid in unique[:6]:
            print(f"        {nid}")
        if len(unique) > 6:
            print(f"        ... ({len(unique) - 6} more)")

    # Sanity check
    print(f"\n=== Sanity check (expected anchors) ===")
    anchors = EXPECTED_ANCHORS.get(args.section, [])
    if not anchors:
        print(f"  No anchors defined for {args.section}")
        return

    found_ids = {nid.lower() for ids in all_nodes_by_type.values() for nid in ids}
    found_types: dict[str, set[str]] = defaultdict(set)
    for type_, ids in all_nodes_by_type.items():
        for nid in ids:
            found_types[nid.lower()].add(type_)

    for substring, expected_label in anchors:
        match_id = next((i for i in found_ids if substring in i), None)
        if match_id is None:
            print(f"  [MISS] {substring!r}")
            continue
        if expected_label and expected_label not in found_types[match_id]:
            print(f"  [WRONG TYPE] {match_id!r} found but type ≠ {expected_label} (got {found_types[match_id]})")
        else:
            print(f"  [OK]   {match_id!r}")


if __name__ == "__main__":
    main()
