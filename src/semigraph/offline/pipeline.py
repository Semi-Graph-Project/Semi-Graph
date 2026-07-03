"""
Offline pipeline orchestrator — chunk → extract → store across many filings.

Two entry points:
  - `process_filing(ticker, fy, filing_type)` runs one filing end-to-end with
    chunk-level parallelism (ThreadPool). Continues on per-chunk errors and
    appends them to log/extraction_errors.jsonl.
  - `process_corpus(filings)` walks a list of filings, skipping those already
    marked "done" in the checkpoint. Parallel within filing, sequential across.

The checkpoint lives at data/processed/.checkpoint.json and stores per-filing
status so re-running the pipeline resumes from where it left off.
"""
from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

from semigraph.config import Config, get_config
from semigraph.connections import get_llm, get_neo4j_driver
from semigraph.offline.chunker import Chunk, chunk_filing
from semigraph.offline.graph_repair import repair_filing_graph
from semigraph.offline.kg_extract import extract_chunk
from semigraph.offline.kg_store import KGStore, init_schema


# ===========================================================================
# Result + checkpoint types
# ===========================================================================


@dataclass
class FilingResult:
    """Outcome of processing one filing — used both for logging and checkpoint."""
    filing_key: str
    status: str  # "done" | "partial" | "failed"
    chunks_processed: int = 0
    chunks_failed: int = 0
    nodes: int = 0
    relationships: int = 0
    repaired_relationships: int = 0
    repair_summary: dict = field(default_factory=dict)
    elapsed_s: float = 0.0
    error: Optional[str] = None
    completed_at: Optional[str] = None


class Checkpoint:
    """Per-filing checkpoint stored as JSON. Atomic save via tempfile rename."""

    def __init__(self, path: Path):
        self.path = path
        self.data: dict = self._load()

    def _load(self) -> dict:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                print(f"[checkpoint] WARN: corrupt file at {self.path}, starting fresh")
        return {}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.path)

    def is_done(self, filing_key: str) -> bool:
        return self.data.get(filing_key, {}).get("status") == "done"

    def mark(self, filing_key: str, result: FilingResult) -> None:
        result.completed_at = time.strftime("%Y-%m-%dT%H:%M:%S")
        self.data[filing_key] = asdict(result)
        self.save()


# ===========================================================================
# Helpers
# ===========================================================================


def _filing_key(ticker: str, fiscal_year: str, filing_type: str = "10-K") -> str:
    return f"{ticker}_{fiscal_year}_{filing_type}"


def _log_chunk_error(error_log_path: Path, chunk: Chunk, exc: Exception) -> None:
    """Append a JSON line for one failed chunk. Thread-safe (single line write)."""
    error_log_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "chunk_id": chunk.chunk_id,
        "ticker": chunk.ticker,
        "fiscal_year": chunk.fiscal_year,
        "section": chunk.section,
        "error_type": type(exc).__name__,
        "error_msg": str(exc),
    }
    with open(error_log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _process_one_chunk(
    chunk: Chunk,
    store: KGStore,
    llm,
    error_log_path: Path,
    metrics_sink: Optional[list] = None,
) -> tuple[bool, dict]:
    """
    Worker called per chunk. Catches all exceptions and logs them so one bad
    chunk does not kill the whole filing.
    Returns (success, counts).

    If metrics_sink is provided, appends one row per chunk with token usage,
    latency, and yield counts. list.append is atomic under the CPython GIL so
    this is safe for ThreadPoolExecutor.
    """
    try:
        chunk_metrics: list = []
        result = extract_chunk(
            chunk.text,
            section=chunk.section,
            llm=llm,
            metrics_sink=chunk_metrics if metrics_sink is not None else None,
        )
        counts = store.store_extraction(chunk, result)
        if metrics_sink is not None and chunk_metrics:
            row = chunk_metrics[0]
            row["chunk_id"] = chunk.chunk_id
            row["ticker"] = chunk.ticker
            row["fiscal_year"] = chunk.fiscal_year
            row["section"] = chunk.section
            row["n_nodes"] = len(result.nodes)
            row["n_relationships"] = len(result.relationships)
            row["status"] = "ok"
            metrics_sink.append(row)
        return True, counts
    except Exception as e:
        _log_chunk_error(error_log_path, chunk, e)
        if metrics_sink is not None:
            metrics_sink.append({
                "chunk_id": chunk.chunk_id,
                "ticker": chunk.ticker,
                "fiscal_year": chunk.fiscal_year,
                "section": chunk.section,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "latency_sec": 0.0,
                "n_nodes": 0,
                "n_relationships": 0,
                "status": f"error:{type(e).__name__}",
            })
        return False, {"nodes": 0, "relationships": 0}


# ===========================================================================
# Main entry points
# ===========================================================================


def process_filing(
    ticker: str,
    fiscal_year: str,
    filing_type: str = "10-K",
    workers: int = 8,
    cfg: Optional[Config] = None,
    metrics_sink: Optional[list] = None,
    overwrite: bool = True,
) -> FilingResult:
    """
    Process a single filing end-to-end. Parallel at chunk level.

    Reads sections from data/processed/<ticker>/FY<year>-<type>/Item_*.md ,
    chunks them, runs extract_chunk concurrently in `workers` threads, and
    pushes each result into Neo4j via KGStore. When `overwrite=True`, any
    previous graph state for the same filing is removed first so reruns stay
    idempotent at the filing level.
    """
    cfg = cfg or get_config()
    filing_key = _filing_key(ticker, fiscal_year, filing_type)
    filing_dir = cfg.processed_dir / ticker / f"FY{fiscal_year}-{filing_type}"
    error_log = cfg.log_dir / "extraction_errors.jsonl"

    if not filing_dir.exists():
        return FilingResult(
            filing_key=filing_key,
            status="failed",
            error=f"filing_dir not found: {filing_dir}",
        )

    # Convert "Item 1A" → "Item_1A" because chunker matches on file stem
    target_sections = [s.replace(" ", "_") for s in cfg.target_sections]

    section_to_chunks = chunk_filing(
        filing_dir=filing_dir,
        ticker=ticker,
        fiscal_year=fiscal_year,
        filing_type=filing_type,
        target_sections=target_sections,
        cfg=cfg,
    )

    all_chunks: list[Chunk] = []
    for chunks in section_to_chunks.values():
        all_chunks.extend(chunks)

    if not all_chunks:
        return FilingResult(
            filing_key=filing_key,
            status="failed",
            error="no chunks produced (target sections may be missing)",
        )

    print(f"[pipeline] {filing_key}: {len(all_chunks)} chunks across "
          f"{len(section_to_chunks)} sections (workers={workers})")

    driver = get_neo4j_driver()
    store = KGStore(driver=driver)
    llm = get_llm()

    try:
        if overwrite:
            store.reset_filing(ticker, fiscal_year, filing_type)
        store.ensure_filing(ticker, fiscal_year, filing_type)

        t0 = time.time()
        success = 0
        fail = 0
        nodes_total = 0
        rels_total = 0

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(_process_one_chunk, c, store, llm, error_log, metrics_sink): c
                for c in all_chunks
            }

            for i, future in enumerate(as_completed(futures), start=1):
                ok, counts = future.result()
                if ok:
                    success += 1
                    nodes_total += counts["nodes"]
                    rels_total += counts["relationships"]
                else:
                    fail += 1

                if i % 10 == 0 or i == len(all_chunks):
                    elapsed = time.time() - t0
                    rate = i / elapsed if elapsed > 0 else 0.0
                    eta = (len(all_chunks) - i) / rate if rate > 0 else 0.0
                    print(f"  [{i}/{len(all_chunks)}] ok={success} fail={fail} | "
                          f"{elapsed:.0f}s elapsed, ETA {eta:.0f}s")

        repair_stats = repair_filing_graph(
            ticker=ticker,
            fiscal_year=fiscal_year,
            filing_type=filing_type,
            cfg=cfg,
            driver=driver,
        )
        if repair_stats.skipped:
            print(f"  [repair] skipped: {repair_stats.reason}")
        else:
            print(
                f"  [repair] {repair_stats.total_created} rels "
                f"(anchor={repair_stats.filer_anchor_created}, "
                f"risk_bridge={repair_stats.item_1a_risk_bridge_created})"
            )

        elapsed = time.time() - t0
        status = "done" if fail == 0 else "partial"
        repaired_rels = repair_stats.total_created

        return FilingResult(
            filing_key=filing_key,
            status=status,
            chunks_processed=success,
            chunks_failed=fail,
            nodes=nodes_total,
            relationships=rels_total + repaired_rels,
            repaired_relationships=repaired_rels,
            repair_summary=repair_stats.as_dict(),
            elapsed_s=elapsed,
        )

    except Exception as e:
        return FilingResult(
            filing_key=filing_key,
            status="failed",
            error=f"{type(e).__name__}: {e}",
        )
    finally:
        store.close()


def process_corpus(
    filings: list[tuple[str, str, str]],
    workers: int = 8,
    cfg: Optional[Config] = None,
    resume: bool = True,
) -> list[FilingResult]:
    """
    Process multiple filings.

    Args:
        filings: list of (ticker, fiscal_year, filing_type) tuples
        workers: chunk-level parallelism within each filing
        cfg:     config; defaults to cached singleton
        resume:  if True, skip filings that the checkpoint marks as "done"

    Returns:
        list of FilingResult — only for filings actually processed (not skipped)
    """
    cfg = cfg or get_config()
    checkpoint_path = cfg.processed_dir / ".checkpoint.json"
    checkpoint = Checkpoint(checkpoint_path)

    # Init schema once before any filing
    driver = get_neo4j_driver()
    try:
        init_schema(driver)
    finally:
        driver.close()

    results: list[FilingResult] = []
    for ticker, fiscal_year, filing_type in filings:
        filing_key = _filing_key(ticker, fiscal_year, filing_type)

        if resume and checkpoint.is_done(filing_key):
            print(f"\n[pipeline] {filing_key}: SKIP (already done)")
            continue

        print(f"\n[pipeline] {filing_key}: START")
        result = process_filing(
            ticker=ticker,
            fiscal_year=fiscal_year,
            filing_type=filing_type,
            workers=workers,
            cfg=cfg,
        )
        checkpoint.mark(filing_key, result)
        results.append(result)

        print(f"[pipeline] {filing_key}: {result.status.upper()} "
              f"({result.chunks_processed} ok / {result.chunks_failed} fail) "
              f"→ {result.nodes} nodes, {result.relationships} rels "
              f"(repair +{result.repaired_relationships}), {result.elapsed_s:.0f}s")
        if result.error:
            print(f"           error: {result.error}")

    return results
