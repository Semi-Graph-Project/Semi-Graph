
from __future__ import annotations

import time
from io import BytesIO
from pathlib import Path
from typing import Optional

import feedparser
import requests
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


def download_filings_batch(
    tickers: list[str],
    filing_type: str = "10-K",
    limit: int = 5,
    after: Optional[str] = None,
    before: Optional[str] = None,
    delay: float = 1.0,
) -> dict[str, int]:
    """
    Download SEC filings for a list of tickers.

    Args:
        tickers: List of stock ticker symbols
        filing_type: SEC form type
        limit: Max filings per ticker
        after: Only fetch filings after this date
        before: Only fetch filings before this date
        delay: Seconds to wait between requests (SEC rate limit)

    Returns:
        Dict mapping ticker -> number of filings downloaded
    """
    results = {}
    for ticker in tickers:
        results[ticker] = download_filings(ticker, filing_type, limit, after, before)
        if delay > 0:
            time.sleep(delay)
    return results


def check_rss_feed(cik: str, ticker: str = "", filing_type: str = "10-K") -> Optional[dict]:
    """
    Check SEC RSS feed for the latest filing of a given CIK.

    Args:
        cik: SEC Central Index Key (e.g. "0001065280" for Netflix)
        ticker: Ticker symbol for display purposes
        filing_type: Form type to check for

    Returns:
        Dict with latest filing info, or None if not found
    """
    rss_url = (
        f"https://www.sec.gov/cgi-bin/browse-edgar"
        f"?action=getcompany&CIK={cik}&type={filing_type}"
        f"&owner=exclude&count=10&output=atom"
    )
    headers = {"User-Agent": "SemiGraph/1.0 (research project)"}

    try:
        response = requests.get(rss_url, headers=headers, timeout=10)
        response.raise_for_status()
        feed = feedparser.parse(BytesIO(response.content))
    except Exception as e:
        print(f"Error fetching RSS feed for CIK {cik}: {e}")
        return None

    if not feed.entries:
        print(f"No entries found in RSS feed for CIK {cik}")
        return None

    latest = feed.entries[0]
    info = {
        "title": latest.title,
        "date": latest.updated,
        "link": latest.link,
        "is_target_type": filing_type in latest.title,
    }

    label = ticker or cik
    print(f"[{label}] Latest: {info['title']} ({info['date']})")
    if not info["is_target_type"]:
        print(f"  Warning: Latest filing is not a {filing_type}")

    return info


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


def get_date_range_from_logs() -> tuple[Optional[str], Optional[str]]:
    """
    Read last fetch date and current date from log files.

    Returns:
        Tuple of (after_date, before_date) in YYYY-MM-DD format
    """
    cfg = get_config()
    after_date = None
    before_date = None

    fetch_log = cfg.log_dir / "fetching_log.txt"
    current_log = cfg.log_dir / "current_date_log.txt"

    if fetch_log.exists():
        after_date = fetch_log.read_text().strip()

    if current_log.exists():
        before_date = current_log.read_text().strip()

    return after_date, before_date
