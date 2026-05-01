from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

import requests


@dataclass
class SECClient:
    user_agent: str
    timeout: int = 30

    def _headers(self) -> Dict[str, str]:
        return {
            "User-Agent": self.user_agent,
            "Accept-Encoding": "gzip, deflate",
            "Host": "www.sec.gov",
        }

    def fetch_recent_filings(self, cik: str, count: int = 10) -> List[Dict[str, Any]]:
        url = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"
        response = requests.get(url, headers=self._headers(), timeout=self.timeout)
        response.raise_for_status()
        payload = response.json()
        recent = payload.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])[:count]
        accession_numbers = recent.get("accessionNumber", [])[:count]
        primary_docs = recent.get("primaryDocument", [])[:count]
        filing_dates = recent.get("filingDate", [])[:count]

        filings: list[Dict[str, Any]] = []
        for index, form in enumerate(forms):
            filings.append(
                {
                    "cik": cik,
                    "form": form,
                    "accession_number": accession_numbers[index] if index < len(accession_numbers) else "",
                    "primary_document": primary_docs[index] if index < len(primary_docs) else "",
                    "filing_date": filing_dates[index] if index < len(filing_dates) else "",
                }
            )
        return filings

    def fetch_filing_text(self, cik: str, accession_number: str, primary_document: str) -> str:
        accession_clean = accession_number.replace("-", "")
        cik_clean = cik.lstrip("0") or "0"
        url = f"https://www.sec.gov/Archives/edgar/data/{cik_clean}/{accession_clean}/{primary_document}"
        response = requests.get(url, headers=self._headers(), timeout=self.timeout)
        response.raise_for_status()
        return response.text

    def fetch_recent_filing_texts(self, cik: str, count: int = 2) -> List[Dict[str, str]]:
        filings = self.fetch_recent_filings(cik, count=count)
        texts: list[Dict[str, str]] = []
        for filing in filings:
            accession_number = filing.get("accession_number", "")
            primary_document = filing.get("primary_document", "")
            if not accession_number or not primary_document:
                continue
            try:
                text = self.fetch_filing_text(cik, accession_number, primary_document)
            except Exception:
                continue
            texts.append(
                {
                    "source": f"SEC {filing.get('form', '')} {filing.get('filing_date', '')}",
                    "accession_number": accession_number,
                    "primary_document": primary_document,
                    "filing_date": filing.get("filing_date", ""),
                    "text": text,
                }
            )
        return texts
