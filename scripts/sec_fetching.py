#!/usr/bin/env python3
import time
import feedparser
import requests
import os
from pathlib import Path
from io import BytesIO
from dotenv import load_dotenv
from sec_edgar_downloader import Downloader

load_dotenv()

EMAIL = os.getenv("EDGAR_EMAIL", "")
ORGANIZATION = os.getenv("EDGAR_ORGANIZATION", "")
dl = Downloader(ORGANIZATION, EMAIL, "data/raw")

def onetime_fetch_filings(ticker: str, filing_type: str):
    count = dl.get(filing_type, ticker, limit=1)
    print(f'Downloaded {count} filings for {ticker}\n-----------------')

def test_download_filings():

    with open("log/fetching_log.txt", "r") as f:
        last_fetch_date = f.read().strip()
        
    with open("log/current_date_log.txt","r") as f:
        current_date = f.read().strip() 

    print(f'Fetching filings after: {last_fetch_date} before: {current_date} ...')
    count = dl.get("10-K", "NFLX", after=last_fetch_date, before=current_date)
    print(f'Downloaded {count} filings for NFLX\n-----------------')

def test_dynamic_fetch_filings():
    with open("log/fetching_log.txt", "r") as f:
        last_fetch_date = f.read().strip()
    print(f"Last fetch date: {type(last_fetch_date)}")

def test_fetch_filings():
    rss_url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001065280&type=10-K&owner=exclude&count=10&output=atom"
    headers = {
            'User-Agent': 'MyCryptoBot/1.0 (contact@example.com)' 
        }
    try:
        response = requests.get(rss_url, headers=headers, timeout=10)
        response.raise_for_status()
        content = BytesIO(response.content)
        feed = feedparser.parse(content)

    except Exception as e:
        print(f"Error fetching feed: {e}")
        return
    
    print(f"--- Checking Netflix (NFLX) 10-K Status ---")
    if feed.entries:
        print(f"Found {len(feed.entries)} entries.")
        last_entry = feed.entries[0]

        title = last_entry.title
        date = last_entry.updated
        link = last_entry.link

        print(f"Latest Filing Found: {title}")
        print(f"Date: {date}")
        print(f"Link: {link}")

        if "10-K" in title:
            pass
        else:
            print("Latest filing is not a 10-K.")
if __name__ == "__main__":
    # while True:
        onetime_fetch_filings("TSM", "10-K")
        # print("Waiting for 10 seconds before next check...")
        # time.sleep(10)