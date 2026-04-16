from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from quant_agent.prices import YahooChartClient
from quant_agent.sources.sec import SECClient


@dataclass
class HistoricalValidationItem:
    ticker: str
    sector: str
    subsector: Optional[str]
    filing_date: str
    filing_form: str
    filing_summary: str
    entry_date: str
    exit_date: str
    total_return: Optional[float]
    notes: List[str] = field(default_factory=list)


class HistoricalValidator:
    def __init__(self, sec_client: SECClient, price_client: YahooChartClient) -> None:
        self.sec_client = sec_client
        self.price_client = price_client

    def validate_early_2025(self, ticker: str, cik: str, sector: str, subsector: Optional[str] = None) -> HistoricalValidationItem:
        filings = self.sec_client.fetch_recent_filings(cik, count=20)
        filing = next((item for item in filings if item.get("filing_date", "") >= "2025-01-01" and item.get("filing_date", "") < "2025-04-01"), None)
        if filing is None:
            return HistoricalValidationItem(
                ticker=ticker,
                sector=sector,
                subsector=subsector,
                filing_date="",
                filing_form="",
                filing_summary="No early-2025 filing found in the public SEC submissions snapshot.",
                entry_date="2025-01-02",
                exit_date="2026-05-01",
                total_return=self.price_client.total_return(ticker, "2025-01-02", "2026-05-01"),
                notes=["Fallback to price validation only."],
            )

        filing_date = filing.get("filing_date", "")
        entry_date = filing_date if filing_date else "2025-01-02"
        filing_text = self.sec_client.fetch_filing_text(cik, filing.get("accession_number", ""), filing.get("primary_document", ""))
        filing_summary = filing_text[:500].replace("\n", " ")
        total_return = self.price_client.total_return(ticker, entry_date, "2026-05-01")
        return HistoricalValidationItem(
            ticker=ticker,
            sector=sector,
            subsector=subsector,
            filing_date=filing_date,
            filing_form=filing.get("form", ""),
            filing_summary=filing_summary,
            entry_date=entry_date,
            exit_date="2026-05-01",
            total_return=total_return,
            notes=["Early-2025 SEC filing found and price performance measured through today."],
        )
