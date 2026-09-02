
from __future__ import annotations

from pathlib import Path
from typing import Optional

from sec_edgar_downloader import Downloader

from semigraph.config import get_config


def _get_downloader() -> Downloader:
    cfg = get_config()
    return Downloader(cfg.edgar_org, cfg.edgar_email, str(cfg.raw_dir))


def download_filings(
    ticker: str,
    filing_type: str = "10-K",
    limit: int = 5,
    after: Optional[str] = None,
    before: Optional[str] = None,
) -> int:
    """
    Download SEC filings for a single ticker.

    Args:
        ticker: Stock ticker symbol (e.g. "NVDA")
        filing_type: SEC form type ("10-K", "10-Q", "8-K")
        limit: Max number of filings to download
        after: Only fetch filings after this date (YYYY-MM-DD)
        before: Only fetch filings before this date (YYYY-MM-DD)

    Returns:
        Number of filings downloaded
    """
    dl = _get_downloader()
    kwargs = {"limit": limit}
    if after:
        kwargs["after"] = after
    if before:
        kwargs["before"] = before

    count = dl.get(filing_type, ticker, **kwargs)
    print(f"Downloaded {count} {filing_type} filing(s) for {ticker}")
    return count


def get_filing_paths(ticker: str, filing_type: str = "10-K") -> list[Path]:
    """
    List all downloaded filing paths for a given ticker.

    Args:
        ticker: Stock ticker symbol
        filing_type: SEC form type

    Returns:
        List of paths to full-submission.txt files
    """
    cfg = get_config()
    filing_dir = cfg.raw_dir / "sec-edgar-filings" / ticker / filing_type
    if not filing_dir.exists():
        return []
    return sorted(filing_dir.glob("*/full-submission.txt"))
