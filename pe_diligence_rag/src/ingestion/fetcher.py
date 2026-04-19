"""
SEC EDGAR Filing Fetcher.
Downloads 10-K filings from SEC EDGAR API.
Handles rate limiting and company CIK lookups.
"""

import requests
import time
import re
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from bs4 import BeautifulSoup

from ..config.settings import (
    SEC_BASE_URL,
    SEC_ARCHIVES_URL,
    SEC_USER_AGENT,
    SEC_RATE_LIMIT_DELAY,
    RAW_DIR
)


@dataclass
class FilingMetadata:
    """Metadata for a SEC filing."""
    ticker: str
    company: str
    cik: str
    form: str
    filed_date: str
    accession_number: str
    document: str
    fiscal_year: int


class SECFetcher:
    """Fetches SEC filings from EDGAR API."""

    def __init__(self, save_dir: Path = None):
        self.save_dir = save_dir or RAW_DIR
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": SEC_USER_AGENT})

    def get_cik(self, ticker: str) -> str:
        """Get CIK number for a ticker symbol."""
        # Try SEC company tickers JSON
        url = "https://www.sec.gov/files/company_tickers.json"
        resp = self.session.get(url)
        resp.raise_for_status()

        data = resp.json()
        for entry in data.values():
            if entry['ticker'].upper() == ticker.upper():
                return str(entry['cik_str']).zfill(10)

        # Fallback: search EDGAR
        search_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&ticker={ticker}&type=10-K&dateb=&owner=include&count=1"
        resp = self.session.get(search_url)
        match = re.search(r'CIK=(\d+)', resp.text)
        if match:
            return match.group(1).zfill(10)

        raise ValueError(f"Ticker {ticker} not found in SEC database")

    def get_company_filings(self, cik: str, form: str = "10-K", limit: int = 10) -> list[FilingMetadata]:
        """Get list of filings for a company."""
        url = f"{SEC_BASE_URL}/CIK{cik.zfill(10)}.json"
        resp = self.session.get(url)
        resp.raise_for_status()

        data = resp.json()
        filings = []

        # Get company name
        company = data.get('name', '')

        recent = data.get('filings', {}).get('recent', {})
        forms = recent.get('form', [])
        filing_dates = recent.get('filingDate', [])
        accession_numbers = recent.get('accessionNumber', [])
        documents = recent.get('primaryDocument', [])

        for i, form_type in enumerate(forms):
            if form_type == form:
                accession = accession_numbers[i]
                filed_date = filing_dates[i]
                document = documents[i]

                # Extract fiscal year from filing date
                fiscal_year = int(filed_date[:4])

                filings.append(FilingMetadata(
                    ticker=cik,  # Will be updated with actual ticker
                    company=company,
                    cik=cik,
                    form=form_type,
                    filed_date=filed_date,
                    accession_number=accession,
                    document=document,
                    fiscal_year=fiscal_year
                ))

                if len(filings) >= limit:
                    break

        return filings

    def get_filing_url(self, cik: str, filing: FilingMetadata) -> str:
        """Get the URL for a filing document."""
        accession_clean = filing.accession_number.replace('-', '')
        base_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_clean}/{filing.document}"
        return base_url

    def download_filing(self, cik: str, filing: FilingMetadata) -> tuple[str, str]:
        """Download a filing and return (html_content, filing_url)."""
        url = self.get_filing_url(cik, filing)

        # Rate limit
        time.sleep(SEC_RATE_LIMIT_DELAY)

        resp = self.session.get(url)
        resp.raise_for_status()

        return resp.text, url

    def fetch_10k(self, ticker: str, limit: int = 10, save_raw: bool = True) -> list[dict]:
        """Main method: fetch 10-K filings for a ticker."""
        print(f"Fetching {limit} 10-K filings for {ticker}...")

        # Get CIK
        cik = self.get_cik(ticker)
        print(f"  CIK: {cik}")

        # Get filings list
        filings = self.get_company_filings(cik, form="10-K", limit=limit)
        print(f"  Found {len(filings)} filings")

        # Update ticker in filings
        for f in filings:
            f.ticker = ticker

        results = []
        for filing in filings:
            try:
                print(f"  Downloading {filing.filed_date}...")
                html, url = self.download_filing(cik, filing)

                if save_raw:
                    # Save raw HTML
                    save_path = self.save_dir / ticker / "10-K" / f"{filing.filed_date}.html"
                    save_path.parent.mkdir(parents=True, exist_ok=True)
                    save_path.write_text(html, encoding='utf-8')
                    print(f"    Saved to {save_path}")

                results.append({
                    "ticker": ticker,
                    "cik": cik,
                    "filing": filing,
                    "html": html,
                    "url": url
                })

            except Exception as e:
                print(f"    Error downloading {filing.filed_date}: {e}")
                continue

        return results


def fetch_company(ticker: str, limit: int = 10) -> list[dict]:
    """Convenience function to fetch filings for a company."""
    fetcher = SECFetcher()
    return fetcher.fetch_10k(ticker, limit=limit)
