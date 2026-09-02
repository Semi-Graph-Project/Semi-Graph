#!/usr/bin/env python3
"""
Pilot pipeline runner — onboard ANY ticker into the corpus end-to-end.

One command runs the full sequence with per-chunk metrics capture:
    download (SEC EDGAR) → preprocess (HTML→MD sections) → discover →
    extract (DeepSeek + token metrics) → embed (chunks + entities + triples) →
    verify (Neo4j counts) → sync corpus config

Usage:
    # Full onboarding for one ticker
    python scripts/pilot.py --ticker QCOM

    # Re-run extract on already-preprocessed data
    python scripts/pilot.py --ticker QCOM --skip-download --skip-preprocess

    # Skip embedding (measurement-only run)
    python scripts/pilot.py --ticker QCOM --skip-embed

    # Tune parallelism
    python scripts/pilot.py --ticker QCOM --workers 4

    # Sync config tickers from Neo4j without onboarding (reconcile config <- DB)
    python scripts/pilot.py --sync-only

Outputs:
    analytics/{ticker_lower}_pilot_metrics.csv    — per-chunk row
    config/default.yaml `tickers:`                — synced to Neo4j (Phase 9)

Idempotent: existing chunks/embeddings are skipped automatically (Neo4j MERGE +
embed scripts check IS NULL). Safe to re-run.
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from semigraph.config import get_config
from semigraph.connections import get_neo4j_driver
from semigraph.offline.ingest import download_filings, get_filing_paths
from semigraph.offline.pipeline import process_filing
from semigraph.offline.preprocess import clean_and_save_documents


FILING_TYPE = "10-K"
LIMIT = 3            # 3 most-recent annual filings
DELAY = 2.0          # SEC rate-limit cushion

DIVIDER = "=" * 70


# ── Phase 1: download ─────────────────────────────────────────────────────────

def phase1_download(ticker: str, skip: bool) -> list[Path]:
    print(f"\n{DIVIDER}\nPHASE 1 — Download {ticker} {FILING_TYPE} (latest {LIMIT})\n{DIVIDER}")
    existing = get_filing_paths(ticker, FILING_TYPE)
    if skip or len(existing) >= LIMIT:
        print(f"  Found {len(existing)} existing filing(s) — skipping download")
        return existing
    print(f"  Downloading up to {LIMIT} filings from SEC EDGAR...")
    download_filings(ticker, FILING_TYPE, limit=LIMIT)
    time.sleep(DELAY)
    return get_filing_paths(ticker, FILING_TYPE)


# ── Phase 2: preprocess ───────────────────────────────────────────────────────

def phase2_preprocess(ticker: str, filing_paths: list[Path], skip: bool) -> None:
    print(f"\n{DIVIDER}\nPHASE 2 - Preprocess -> Markdown sections\n{DIVIDER}")
    if skip:
        print("  --skip-preprocess set - skipping")
        return
    if not filing_paths:
        print("  No filings to preprocess - abort")
        return
    for fp in filing_paths:
        accession = fp.parent.name
        print(f"  Processing {accession}...")
        try:
            clean_and_save_documents(input_file=str(fp), ticker=ticker, filing_id=accession)
        except Exception as e:
            print(f"    ERROR: {e}")


# ── Phase 3: discover ─────────────────────────────────────────────────────────

def phase3_discover(ticker: str, cfg) -> list[tuple[str, str, str]]:
    print(f"\n{DIVIDER}\nPHASE 3 — Discover processed {ticker} filings\n{DIVIDER}")
    ticker_dir = cfg.processed_dir / ticker
    if not ticker_dir.exists():
        print(f"  No processed dir at {ticker_dir}")
        return []
    filings: list[tuple[str, str, str]] = []
    for d in sorted(ticker_dir.iterdir()):
        name = d.name  # e.g. "FY2025-10K"
        if not name.startswith("FY"):
            continue
        try:
            year, ftype = name[2:].split("-", 1)
        except ValueError:
            continue
        filings.append((ticker, year, ftype))
        print(f"  Found: {ticker} FY{year}-{ftype}")
    return filings


# ── Phase 4: extract w/ metrics ───────────────────────────────────────────────

def phase4_extract(filings: list[tuple[str, str, str]], workers: int, cfg) -> list[dict]:
    print(f"\n{DIVIDER}\nPHASE 4 — Extract w/ per-chunk metrics (workers={workers})\n{DIVIDER}")
    metrics: list[dict] = []
    for ticker, fy, ftype in filings:
        print(f"\n  ->> {ticker} FY{fy}-{ftype}")
        t0 = time.time()
        result = process_filing(
            ticker=ticker,
            fiscal_year=fy,
            filing_type=ftype,
            workers=workers,
            cfg=cfg,
            metrics_sink=metrics,
        )
        wall = time.time() - t0
        print(f"    status={result.status} | "
              f"chunks ok={result.chunks_processed} fail={result.chunks_failed} | "
              f"nodes={result.nodes} rels={result.relationships} "
              f"(repair +{result.repaired_relationships}) | wall={wall:.0f}s")
        if result.error:
            print(f"    error: {result.error}")
    return metrics


# ── Phase 5: write CSV ────────────────────────────────────────────────────────

CSV_FIELDS = [
    "ticker", "fiscal_year", "section", "chunk_id",
    "prompt_tokens", "completion_tokens", "total_tokens",
    "latency_sec", "n_nodes", "n_relationships", "status",
]


def phase5_write_csv(ticker: str, metrics: list[dict]) -> Path:
    out_dir = PROJECT_ROOT / "analytics"
    out_dir.mkdir(exist_ok=True)
    path = out_dir / f"{ticker.lower()}_pilot_metrics.csv"
    print(f"\n{DIVIDER}\nPHASE 5 — Write metrics CSV → {path}\n{DIVIDER}")
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        for row in metrics:
            w.writerow({k: row.get(k, "") for k in CSV_FIELDS})
    print(f"  Wrote {len(metrics)} rows")
    return path


# ── Phase 6: embed (chunks + nodes + triples) ─────────────────────────────────

def _run_embed_script(script_name: str) -> bool:
    """Spawn embed script as subprocess with CPU forced (torch CUDA init crashes
    on some machines). Returns True on exit code 0."""
    env = {**os.environ, "CUDA_VISIBLE_DEVICES": ""}
    path = PROJECT_ROOT / "scripts" / script_name
    print(f"  -> {script_name}")
    proc = subprocess.run(
        [sys.executable, str(path)],
        env=env,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    last_lines = proc.stdout.strip().splitlines()[-6:]
    for line in last_lines:
        print(f"      {line}")
    if proc.returncode != 0:
        stderr_tail = proc.stderr.strip().splitlines()[-3:]
        print(f"      STDERR tail: {stderr_tail}")
        return False
    return True


def phase6_embed(skip: bool) -> bool:
    print(f"\n{DIVIDER}\nPHASE 6 — Embed (chunks + entities + triples, CPU mode)\n{DIVIDER}")
    if skip:
        print("  --skip-embed set — skipping")
        return True
    all_ok = True
    for script in ("embed_chunks.py", "embed_nodes.py", "embed_triples.py"):
        if not _run_embed_script(script):
            print(f"  !! {script} failed — continuing but check log")
            all_ok = False
    return all_ok


# ── Phase 6.5: compute specificity ────────────────────────────────────────────

def phase6_5_specificity(skip: bool) -> bool:
    """Recompute Entity.specificity over the full graph. Must run after embed
    so new entities (just MERGEd in Phase 4) get spec values — PPR teleport
    uses these as seed weights; missing spec → seeds dropped or weighted as 1.0
    (silent quality loss)."""
    print(f"\n{DIVIDER}\nPHASE 6.5 — Compute Node Specificity (PPR teleport weights)\n{DIVIDER}")
    if skip:
        print("  --skip-specificity set — skipping")
        return True
    env = {**os.environ, "CUDA_VISIBLE_DEVICES": ""}
    path = PROJECT_ROOT / "scripts" / "compute_specificity.py"
    print(f"  → compute_specificity.py")
    proc = subprocess.run(
        [sys.executable, str(path)],
        env=env,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    # show summary block (last ~15 lines usually contain top hubs/leaves)
    last_lines = proc.stdout.strip().splitlines()[-15:]
    for line in last_lines:
        print(f"      {line}")
    if proc.returncode != 0:
        print(f"      STDERR tail: {proc.stderr.strip().splitlines()[-3:]}")
        return False
    return True


# ── Phase 7: verify in Neo4j ──────────────────────────────────────────────────

def phase7_verify(ticker: str) -> None:
    print(f"\n{DIVIDER}\nPHASE 7 — Verify {ticker} in Neo4j\n{DIVIDER}")
    d = get_neo4j_driver()
    try:
        with d.session() as s:
            checks = [
                ("chunks",
                 f"MATCH (c:Chunk) WHERE c.ticker='{ticker}' "
                 "RETURN count(c) AS n, count(c.embedding) AS e"),
                ("entities (mentioned)",
                 f"MATCH (e:Entity)-[:MENTIONS]-(c:Chunk {{ticker:'{ticker}'}}) "
                 "WITH DISTINCT e "
                 "RETURN count(e) AS n, count(e.embedding) AS e"),
                ("entities w/ specificity",
                 f"MATCH (e:Entity)-[:MENTIONS]-(c:Chunk {{ticker:'{ticker}'}}) "
                 "WITH DISTINCT e "
                 "RETURN count(e) AS n, count(e.specificity) AS e"),
                ("rels (informative w/ triple_embedding)",
                 f"MATCH (c:Chunk {{ticker:'{ticker}'}}) "
                 "WITH collect(c.chunk_id) AS chunk_ids "
                 "MATCH (s:Entity)-[r]->(t:Entity) "
                 f"WHERE r.triple_embedding IS NOT NULL "
                 "  AND r.source_chunk IN chunk_ids "
                 "RETURN count(r) AS n, count(r.triple_embedding) AS e"),
                ("repair rels",
                 f"MATCH (c:Chunk {{ticker:'{ticker}'}}) "
                 "WITH collect(c.chunk_id) AS chunk_ids "
                 "MATCH ()-[r]->() "
                 "WHERE r.source_chunk IN chunk_ids "
                 "  AND r.repair_method IS NOT NULL "
                 "RETURN count(r) AS n, count(r.triple_embedding) AS e"),
                ("isolated entities",
                 f"MATCH (e:Entity)-[:MENTIONS]-(c:Chunk {{ticker:'{ticker}'}}) "
                 "WITH DISTINCT e "
                 "OPTIONAL MATCH (e)-[r]-(other:Entity) "
                 "WHERE type(r) IN ["
                 "'ANNOUNCES','CAUSES_SHORTAGE_OF','COMPETES_WITH','DEPENDS_ON',"
                 "'DISCLOSES','FACES','GUIDES_ON','HAS_STAKE_IN','IMPACTED_BY',"
                 "'IMPACTS','INTRODUCES','INVESTS_IN','INVOLVED_IN','LISTED_ON',"
                 "'NEGATIVELY_IMPACTS','OPERATES_IN','PARTNERS_WITH',"
                 "'POSITIVELY_IMPACTS','PRODUCES','SUBJECT_TO','SUPPLIES'] "
                 "WITH e, count(r) AS degree "
                 "WHERE degree = 0 "
                 "RETURN count(e) AS n, 0 AS e"),
                ("zero-rel chunks",
                 f"MATCH (c:Chunk {{ticker:'{ticker}'}}) "
                 "OPTIONAL MATCH ()-[r]->() "
                 "WHERE r.source_chunk = c.chunk_id "
                 "  AND type(r) IN ["
                 "'ANNOUNCES','CAUSES_SHORTAGE_OF','COMPETES_WITH','DEPENDS_ON',"
                 "'DISCLOSES','FACES','GUIDES_ON','HAS_STAKE_IN','IMPACTED_BY',"
                 "'IMPACTS','INTRODUCES','INVESTS_IN','INVOLVED_IN','LISTED_ON',"
                 "'NEGATIVELY_IMPACTS','OPERATES_IN','PARTNERS_WITH',"
                 "'POSITIVELY_IMPACTS','PRODUCES','SUBJECT_TO','SUPPLIES'] "
                 "WITH c, count(r) AS degree "
                 "WHERE degree = 0 "
                 "RETURN count(c) AS n, 0 AS e"),
            ]
            for label, q in checks:
                try:
                    r = s.run(q).single()
                    print(f"  {label:42} total={r['n']:>5}  embedded={r['e']:>5}")
                except Exception as ex:
                    print(f"  {label:42} ERROR: {ex}")
    finally:
        d.close()


# ── Phase 9: sync config tickers ← Neo4j (DB is source of truth) ──────────────

def get_db_tickers() -> list[str]:
    """Return DISTINCT Chunk.ticker present in Neo4j, sorted. This is the ground
    truth for 'what's in the corpus' — config and CORPUS_TICKERS derive from it."""
    d = get_neo4j_driver()
    try:
        with d.session() as s:
            r = s.run(
                "MATCH (c:Chunk) WHERE c.ticker IS NOT NULL "
                "RETURN DISTINCT c.ticker AS t ORDER BY t"
            )
            return [rec["t"] for rec in r]
    finally:
        d.close()


def _sync_tickers_to_config(tickers: list[str]) -> Path:
    """Rewrite the `tickers:` block in config/default.yaml to match `tickers`.

    Text-level edit (not a PyYAML round-trip) so comments and ${ENV} placeholders
    elsewhere in the file survive. Matches `tickers:` plus the contiguous `  - X`
    items under it; everything above/below is untouched.
    """
    cfg_path = PROJECT_ROOT / "config" / "default.yaml"
    text = cfg_path.read_text(encoding="utf-8")
    block = "tickers:\n" + "".join(f"  - {t}\n" for t in sorted(tickers))
    new_text, n = re.subn(
        r"^tickers:\n(?:[ \t]*-[ \t].*\n)*",
        block,
        text,
        count=1,
        flags=re.MULTILINE,
    )
    if n == 0:
        raise RuntimeError("could not find a `tickers:` block in config/default.yaml")
    cfg_path.write_text(new_text, encoding="utf-8")
    return cfg_path

def _sync_reextract_tickers_to_config(tickers: list[str]) -> Path:
    "Write the `reextract_tickers:` just get the --ticker and write append to the config/default.yaml"
    cfg_path = PROJECT_ROOT / "config" / "default.yaml"
    text = cfg_path.read_text(encoding="utf-8")

    existing_tickers = set()
    match = re.search(
        r"reextract_tickers:\n((?:[ \t]*-[ \t].*\n)*)",
        text,
        flags=re.MULTILINE,
    )

    if match:
        lines = match.group(1).strip().splitlines()
        for line in lines:
            ticker = line.replace("-", "").strip()
            if ticker:
                existing_tickers.add(ticker)
    else:
        raise RuntimeError("could not find a `reextract_tickers:` block in config/default.yaml")

    all_tickers = existing_tickers.union(set(tickers))

    block = "reextract_tickers:\n" + "".join(f"  - {t}\n" for t in sorted(all_tickers))

    new_text, n = re.subn(
        r"^reextract_tickers:\n((?:[ \t]*-[ \t].*\n)*)",
        block,
        text,
        count=1,
        flags=re.MULTILINE,
    )

    if n == 0:
        raise RuntimeError("could not find a `reextract_tickers:` block in config/default.yaml")
    cfg_path.write_text(new_text, encoding="utf-8")
    return cfg_path

def phase9_sync_config() -> None:
    print(f"\n{DIVIDER}\nPHASE 9 — Sync config tickers <- Neo4j (DB = source of truth)\n{DIVIDER}")
    db_tickers = get_db_tickers()
    if not db_tickers:
        print("  No tickers in Neo4j — skipping config sync")
        return
    path = _sync_tickers_to_config(db_tickers)
    print(f"  Synced {len(db_tickers)} tickers: {', '.join(db_tickers)}")
    print(f"  -> {path}  (CORPUS_TICKERS now derives from this)")

def phase9_sync_reextract_config(ticker: str) -> None:
    print(f"\n{DIVIDER}\n PHASE 9.5 — Sync config.reextract_tickers <- Neo4j (DB = source of truth)\n{DIVIDER}")
    rextract_ticker = [ticker]
    if not rextract_ticker:
        print("  No tickers in Neo4j — skipping config sync")
        return
    path = _sync_reextract_tickers_to_config(rextract_ticker)
    print(f"  Synced {len(rextract_ticker)} tickers: {', '.join(rextract_ticker)}")
    print(f"  -> {path}  (CORPUS_TICKERS now derives from this)")


# ── Coverage guard: catch silently-dropped filings ───────────────────────────

def check_filing_coverage(
    filings: list[tuple[str, str, str]], metrics: list[dict]
) -> list[str]:
    """Discovered filings that produced ZERO chunks — a silent section-extraction
    failure (e.g. unrecognised header format means 0 sections -> 0 chunks, with no
    exception raised). Returns the sorted fiscal years that vanished.

    Without this, the run prints 'fail: 0' even when whole years never made it
    into the graph (they had no chunks to fail on)."""
    discovered = {str(fy) for _, fy, _ in filings}
    produced = {str(m.get("fiscal_year")) for m in metrics}
    return sorted(discovered - produced)


def warn_missing_filings(ticker: str, missing_fy: list[str]) -> None:
    if not missing_fy:
        return
    print(f"\n{'!' * 70}")
    print(f"  WARNING — {len(missing_fy)} discovered filing(s) produced ZERO chunks")
    print(f"  (section extraction found nothing — these years are NOT in the graph):")
    for fy in missing_fy:
        print(f"    {ticker} FY{fy}  ->  inspect data/processed/{ticker}/FY{fy}-10K/")
    print(f"  Likely an unrecognised header format in preprocess._SECTION_PATTERNS.")
    print(f"{'!' * 70}")


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Pilot pipeline runner — onboard ANY ticker end-to-end with metrics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--ticker", help="Stock ticker (e.g. QCOM, AVGO, AMD). Required unless --sync-only")
    ap.add_argument("--sync-only", action="store_true",
                    help="Skip onboarding — just sync config tickers from Neo4j (Phase 9) and exit")
    ap.add_argument("--workers", type=int, default=8, help="Chunk-level parallelism (default 8)")
    ap.add_argument("--skip-download", action="store_true", help="Skip Phase 1 (use existing data/raw)")
    ap.add_argument("--skip-preprocess", action="store_true", help="Skip Phase 2 (use existing data/processed)")
    ap.add_argument("--skip-embed", action="store_true", help="Skip Phase 6 (extract-only run)")
    ap.add_argument("--sync-reextract",action="store_true", help="Sync config.reextract_tickers <- Neo4j (Phase 9.5) and exit")
    ap.add_argument("--skip-specificity", action="store_true", help="Skip Phase 6.5 (Node Specificity compute)")
    ap.add_argument("--skip-verify", action="store_true", help="Skip Phase 7 (Neo4j count check)")
    args = ap.parse_args()

    if args.sync_only:
        phase9_sync_config()
        return 0
    if not args.ticker:
        ap.error("--ticker is required unless --sync-only is set")

    ticker = args.ticker.upper()
    cfg = get_config()
    print(f"\n{'#' * 70}\n  Pilot run — {ticker}\n{'#' * 70}")
    print(f"  Model: {cfg.llm_model}  | Workers: {args.workers}")
    t0 = time.time()

    paths = phase1_download(ticker, args.skip_download)
    phase2_preprocess(ticker, paths, args.skip_preprocess)
    filings = phase3_discover(ticker, cfg)
    if not filings:
        print(f"\n  No {ticker} filings to process — abort")
        return 1
    metrics = phase4_extract(filings, args.workers, cfg)
    if not metrics:
        print("\n  No metrics collected — abort")
        return 1
    missing_fy = check_filing_coverage(filings, metrics)
    warn_missing_filings(ticker, missing_fy)
    phase5_write_csv(ticker, metrics)
    phase6_embed(args.skip_embed)
    phase6_5_specificity(args.skip_specificity)
    if not args.skip_verify:
        phase7_verify(ticker)
    phase9_sync_config()   # config tickers <- Neo4j reality (includes the new ticker)

    if args.sync_reextract:
        print("\n  --sync-reextract set — syncing config.reextract_tickers <- Neo4j and exiting\n")
        phase9_sync_reextract_config(ticker)

    wall = time.time() - t0
    print(f"\n{'#' * 70}")
    status = "COMPLETE" if not missing_fy else f"INCOMPLETE ({len(missing_fy)} year(s) dropped)"
    print(f"  Pilot {status} — {ticker} | total wall: {wall/60:.1f} min")
    if missing_fy:
        print(f"  missing: {', '.join('FY' + fy for fy in missing_fy)} "
              f"— re-run after fixing preprocess to recover them")
    print(f"{'#' * 70}\n")
    return 0 if not missing_fy else 2


if __name__ == "__main__":
    sys.exit(main())
