"""
CLI entry point for the offline KG extraction pipeline.

Usage:
    # Single filing
    python scripts/run_offline_pipeline.py --ticker NVDA --fiscal-year 2026

    # All filings discovered under data/processed/
    python scripts/run_offline_pipeline.py

    # Force re-run (ignore checkpoint)
    python scripts/run_offline_pipeline.py --no-resume

    # Tweak parallelism
    python scripts/run_offline_pipeline.py --workers 4
"""
from __future__ import annotations

import argparse
import sys

from semigraph.config import get_config
from semigraph.offline.pipeline import process_corpus


def discover_filings(processed_dir) -> list[tuple[str, str, str]]:
    """Walk data/processed/<TICKER>/FY<YEAR>-<TYPE>/ and return (t, fy, type) tuples."""
    out: list[tuple[str, str, str]] = []
    if not processed_dir.exists():
        return out
    for ticker_dir in sorted(processed_dir.iterdir()):
        if not ticker_dir.is_dir():
            continue
        ticker = ticker_dir.name
        for filing_dir in sorted(ticker_dir.iterdir()):
            name = filing_dir.name  # "FY2026-10K"
            if not name.startswith("FY"):
                continue
            try:
                year_type = name[2:]                 # "2026-10K"
                fiscal_year, filing_type = year_type.split("-", 1)
            except ValueError:
                continue
            out.append((ticker, fiscal_year, filing_type))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Run offline KG extraction pipeline")
    parser.add_argument("--ticker", help="Single-filing mode: ticker (e.g. NVDA)")
    parser.add_argument("--fiscal-year", help="Single-filing mode: 4-digit year (e.g. 2026)")
    parser.add_argument("--filing-type", default="10K",
                        help="default 10K (matches preprocess folder convention FY{year}-{type})")
    parser.add_argument("--workers", type=int, default=8, help="chunk-level parallelism (default 8)")
    parser.add_argument("--no-resume", action="store_true",
                        help="ignore checkpoint and reprocess everything")
    args = parser.parse_args()

    cfg = get_config()

    if args.ticker and args.fiscal_year:
        filings = [(args.ticker, args.fiscal_year, args.filing_type)]
        print(f"[run] single-filing mode: {filings[0]}")
    elif args.ticker or args.fiscal_year:
        print("[run] FAIL: --ticker and --fiscal-year must be given together")
        return 2
    else:
        filings = discover_filings(cfg.processed_dir)
        print(f"[run] corpus mode: discovered {len(filings)} filings under {cfg.processed_dir}")
        for f in filings:
            print(f"        {f[0]} / FY{f[1]}-{f[2]}")

    if not filings:
        print("[run] no filings to process — nothing to do")
        return 0

    print(f"\n[run] target_sections: {cfg.target_sections}")
    print(f"[run] workers:         {args.workers}")
    print(f"[run] resume:          {not args.no_resume}\n")

    results = process_corpus(
        filings=filings,
        workers=args.workers,
        cfg=cfg,
        resume=not args.no_resume,
    )

    # ----------------- Summary -----------------
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    if not results:
        print("Nothing processed (all filings already done — use --no-resume to force).")
        return 0

    total_chunks_ok = sum(r.chunks_processed for r in results)
    total_chunks_fail = sum(r.chunks_failed for r in results)
    total_nodes = sum(r.nodes for r in results)
    total_rels = sum(r.relationships for r in results)
    total_elapsed = sum(r.elapsed_s for r in results)

    print(f"Filings processed:   {len(results)}")
    print(f"Chunks ok / failed:  {total_chunks_ok} / {total_chunks_fail}")
    print(f"Nodes total:         {total_nodes}")
    print(f"Relationships total: {total_rels}")
    print(f"Wall-clock time:     {total_elapsed:.0f}s")

    print("\nPer-filing breakdown:")
    for r in results:
        marker = "OK" if r.status == "done" else r.status.upper()
        print(f"  [{marker:7}] {r.filing_key}  "
              f"{r.chunks_processed} ok / {r.chunks_failed} fail  "
              f"{r.nodes}n / {r.relationships}r  ({r.elapsed_s:.0f}s)")
        if r.error:
            print(f"               error: {r.error}")

    failed = [r for r in results if r.status == "failed"]
    if failed:
        print(f"\n[run] {len(failed)} filing(s) FAILED — see error log")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
