#!/usr/bin/env python3
"""
End-to-End test: ingest (SEC EDGAR download) + preprocess (HTML → Markdown → sections)

Focus tickers: NVDA, ASML, MU, AMD
Focus filing:  10-K only (last 3 years per ticker)

Run from project root:
    conda run -n senior_project python scripts/test_e2e_ingest_preprocess.py

Phases:
    1. Status   — show what's already downloaded
    2. Download — fetch missing tickers from SEC EDGAR
    3. Preprocess — convert all downloaded filings to sections
    4. Summary  — show what was created under data/processed/
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

# ── ensure src/ is on the path when running directly ──────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from semigraph.config import get_config
from semigraph.offline.ingest import download_filings, get_filing_paths
from semigraph.offline.preprocess import clean_and_save_documents

# ── constants ──────────────────────────────────────────────────────────────────
TICKERS = ["NVDA", "ASML", "MU", "AMD"]
FILING_TYPE = "10-K"
LIMIT = 3          # last 3 annual filings per ticker
DELAY = 2.0        # seconds between SEC EDGAR requests (rate limit)

DIVIDER = "=" * 60


# ── Phase 1: Status ────────────────────────────────────────────────────────────

def phase1_status(cfg) -> dict[str, list[Path]]:
    """Return dict of ticker → list of local full-submission.txt paths."""
    print(f"\n{DIVIDER}")
    print("PHASE 1 — Current download status")
    print(DIVIDER)

    status: dict[str, list[Path]] = {}
    for ticker in TICKERS:
        paths = get_filing_paths(ticker, FILING_TYPE)
        status[ticker] = paths
        if paths:
            print(f"  {ticker}: {len(paths)} filing(s) found")
            for p in paths:
                accession = p.parent.name
                size_mb = p.stat().st_size / 1_048_576
                print(f"    • {accession}  ({size_mb:.1f} MB)")
        else:
            print(f"  {ticker}: NOT downloaded")

    return status


# ── Phase 2: Download ──────────────────────────────────────────────────────────

def phase2_download(status: dict[str, list[Path]]) -> dict[str, list[Path]]:
    """Download only tickers that have no local filings yet."""
    missing = [t for t, paths in status.items() if not paths]

    print(f"\n{DIVIDER}")
    print("PHASE 2 — Download missing filings")
    print(DIVIDER)

    if not missing:
        print("  All tickers already downloaded. Skipping.")
        return status

    print(f"  Downloading: {missing}")
    print(f"  (limit={LIMIT} filings each, delay={DELAY}s between requests)\n")

    cfg = get_config()
    updated_status = dict(status)

    for ticker in missing:
        print(f"  [{ticker}] Downloading...")
        try:
            count = download_filings(ticker, FILING_TYPE, limit=LIMIT)
            time.sleep(DELAY)
            updated_status[ticker] = get_filing_paths(ticker, FILING_TYPE)
            print(f"  [{ticker}] Downloaded {count} filing(s).")
        except Exception as e:
            print(f"  [{ticker}] ERROR: {e}")

    return updated_status


# ── Phase 3: Preprocess ────────────────────────────────────────────────────────

def phase3_preprocess(status: dict[str, list[Path]], cfg) -> dict[str, dict]:
    """
    Run preprocess pipeline on every downloaded filing.
    Output goes to data/processed/{TICKER}/FY{YEAR}/
    """
    print(f"\n{DIVIDER}")
    print("PHASE 3 — Preprocess filings → Markdown + sections")
    print(DIVIDER)

    results: dict[str, dict] = {}

    for ticker in TICKERS:
        paths = status.get(ticker, [])
        if not paths:
            print(f"\n  [{ticker}] No filings found — skipping.")
            continue

        print(f"\n  [{ticker}] Processing {len(paths)} filing(s)...")
        results[ticker] = {}

        for filing_path in paths:
            accession = filing_path.parent.name  # e.g. "0001045810-26-000021"
            try:
                sections = clean_and_save_documents(
                    input_file=str(filing_path),
                    ticker=ticker,
                    filing_id=accession,
                )
                results[ticker][accession] = {
                    "status": "ok",
                    "sections": list(sections.get("10-K", {}).keys()),
                }
            except Exception as e:
                print(f"    ERROR processing {accession}: {e}")
                results[ticker][accession] = {"status": "error", "error": str(e)}

    return results


# ── Phase 4: Summary ───────────────────────────────────────────────────────────

def phase4_summary(cfg) -> None:
    """Walk data/processed/ and print what was created."""
    print(f"\n{DIVIDER}")
    print("PHASE 4 — Output summary")
    print(DIVIDER)

    processed_root = cfg.processed_dir
    total_sections = 0

    for ticker in TICKERS:
        ticker_dir = processed_root / ticker
        if not ticker_dir.exists():
            print(f"\n  {ticker}/  (no output)")
            continue

        print(f"\n  {ticker}/")
        for year_dir in sorted(ticker_dir.iterdir()):
            if not year_dir.is_dir():
                continue
            md_files = sorted(year_dir.glob("*.md"))
            section_files = [f for f in md_files if f.name != "full_10K.md"]
            full_doc = year_dir / "full_10K.md"
            full_size = f"{full_doc.stat().st_size / 1024:.0f} KB" if full_doc.exists() else "missing"

            print(f"    {year_dir.name}/")
            print(f"      full_10K.md  ({full_size})")
            for sf in section_files:
                size = sf.stat().st_size / 1024
                print(f"      {sf.name}  ({size:.0f} KB)")
                total_sections += 1

    print(f"\n  Total section files created: {total_sections}")
    print(f"  Location: {processed_root}")


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    cfg = get_config()

    print(f"\n{'#' * 60}")
    print("  E2E Test: Ingest + Preprocess")
    print(f"  Tickers : {TICKERS}")
    print(f"  Raw dir : {cfg.raw_dir}")
    print(f"  Out dir : {cfg.processed_dir}")
    print(f"{'#' * 60}")

    status = phase1_status(cfg)
    status = phase2_download(status)
    phase3_preprocess(status, cfg)
    phase4_summary(cfg)

    print(f"\n{'#' * 60}")
    print("  E2E test complete.")
    print(f"{'#' * 60}\n")


if __name__ == "__main__":
    main()
