
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, List, Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel, Field

from semigraph.config import Config, get_config


# ---------------------------------------------------------------------------
# 1. Data model
# ---------------------------------------------------------------------------

class Chunk(BaseModel):
    """Single text chunk with full provenance."""

    chunk_id: str = Field(description="Deterministic ID: {ticker}_{year}_{section}_{idx:04d}")
    ticker: str
    fiscal_year: str        # e.g. "2026"
    filing_type: str        # e.g. "10-K"
    section: str            # e.g. "Item_1A"
    text: str
    char_count: int
    token_estimate: int     # rough estimate: char_count // 4


# ---------------------------------------------------------------------------
# 2. Core splitting
# ---------------------------------------------------------------------------

_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


def _make_splitter(cfg: Config) -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=cfg.chunk_size,
        chunk_overlap=cfg.chunk_overlap,
        separators=_SEPARATORS,
        length_function=len,
    )


def _chunk_id(ticker: str, fiscal_year: str, section: str, idx: int) -> str:
    base = f"{ticker}_{fiscal_year}_{section}_{idx:04d}"
    digest = hashlib.md5(base.encode()).hexdigest()[:8]
    return f"{base}_{digest}"


def chunk_section(
    text: str,
    ticker: str,
    fiscal_year: str,
    section: str,
    filing_type: str = "10-K",
    cfg: Optional[Config] = None,
) -> List[Chunk]:
    """
    Split a single section's Markdown text into overlapping Chunk objects.

    Args:
        text:        Raw Markdown content of one section.
        ticker:      Stock ticker symbol (e.g. "NVDA").
        fiscal_year: 4-digit year string (e.g. "2026").
        section:     Section name without spaces (e.g. "Item_1A").
        filing_type: Filing form type (default "10-K").
        cfg:         Config instance; uses cached default if None.

    Returns:
        List of Chunk objects in order.
    """
    if cfg is None:
        cfg = get_config()

    splitter = _make_splitter(cfg)
    raw_chunks = splitter.split_text(text)

    chunks: List[Chunk] = []
    for idx, chunk_text in enumerate(raw_chunks):
        chunk_text = chunk_text.strip()
        if not chunk_text:
            continue
        chunks.append(Chunk(
            chunk_id=_chunk_id(ticker, fiscal_year, section, idx),
            ticker=ticker,
            fiscal_year=fiscal_year,
            filing_type=filing_type,
            section=section,
            text=chunk_text,
            char_count=len(chunk_text),
            token_estimate=len(chunk_text) // 4,
        ))

    return chunks


# ---------------------------------------------------------------------------
# 3. Filing-level chunking
# ---------------------------------------------------------------------------

def chunk_filing(
    filing_dir: Path,
    ticker: str,
    fiscal_year: str,
    filing_type: str = "10-K",
    target_sections: Optional[List[str]] = None,
    cfg: Optional[Config] = None,
) -> Dict[str, List[Chunk]]:
    """
    Chunk all section .md files inside a single filing directory.

    Args:
        filing_dir:      Path like data/processed/NVDA/FY2026-10K/
        ticker:          Stock ticker (e.g. "NVDA").
        fiscal_year:     4-digit year string (e.g. "2026").
        filing_type:     Filing form type (default "10-K").
        target_sections: Whitelist of section names (e.g. ["Item_1", "Item_1A"]).
                         Chunks all non-full_10K sections if None.
        cfg:             Config instance; uses cached default if None.

    Returns:
        Dict mapping section name -> List[Chunk].
    """
    if cfg is None:
        cfg = get_config()

    result: Dict[str, List[Chunk]] = {}

    section_files = sorted(filing_dir.glob("Item_*.md"))
    if not section_files:
        print(f"  [chunker] No section files found in {filing_dir}")
        return result

    for md_file in section_files:
        section = md_file.stem  # e.g. "Item_1A"

        if target_sections and section not in target_sections:
            continue

        text = md_file.read_text(encoding="utf-8")
        if not text.strip():
            print(f"  [chunker] Skip empty: {md_file.name}")
            continue

        chunks = chunk_section(
            text=text,
            ticker=ticker,
            fiscal_year=fiscal_year,
            section=section,
            filing_type=filing_type,
            cfg=cfg,
        )
        result[section] = chunks
        total_chars = sum(c.char_count for c in chunks)
        print(
            f"  [chunker] {section}: {len(chunks)} chunks "
            f"({total_chars:,} chars, ~{total_chars // 4:,} tokens)"
        )

    return result


# ---------------------------------------------------------------------------
# 4. Batch chunking across all processed filings
# ---------------------------------------------------------------------------

def chunk_processed_dir(
    processed_dir: Optional[Path] = None,
    target_sections: Optional[List[str]] = None,
    cfg: Optional[Config] = None,
) -> Dict[str, Dict[str, Dict[str, List[Chunk]]]]:
    """
    Chunk every filing in the processed directory tree.

    Directory structure expected:
        {processed_dir}/{TICKER}/FY{YEAR}-{TYPE}/Item_*.md

    Args:
        processed_dir:   Root of processed data (defaults to config processed_dir).
        target_sections: Whitelist of section names. Chunks all if None.
        cfg:             Config instance; uses cached default if None.

    Returns:
        Nested dict: ticker -> fiscal_year -> section -> List[Chunk]
    """
    if cfg is None:
        cfg = get_config()
    if processed_dir is None:
        processed_dir = cfg.processed_dir

    all_chunks: Dict[str, Dict[str, Dict[str, List[Chunk]]]] = {}

    for ticker_dir in sorted(processed_dir.iterdir()):
        if not ticker_dir.is_dir():
            continue
        ticker = ticker_dir.name

        for filing_dir in sorted(ticker_dir.iterdir()):
            if not filing_dir.is_dir():
                continue

            # Parse FY{YEAR}-{TYPE} naming convention
            name = filing_dir.name  # e.g. "FY2026-10K"
            if not name.startswith("FY"):
                continue
            try:
                year_type = name[2:]          # "2026-10K"
                fiscal_year, filing_type = year_type.split("-", 1)
            except ValueError:
                continue

            print(f"\n[chunker] {ticker} / {filing_dir.name}")
            filing_chunks = chunk_filing(
                filing_dir=filing_dir,
                ticker=ticker,
                fiscal_year=fiscal_year,
                filing_type=filing_type,
                target_sections=target_sections,
                cfg=cfg,
            )

            if filing_chunks:
                all_chunks.setdefault(ticker, {})[fiscal_year] = filing_chunks

    return all_chunks
