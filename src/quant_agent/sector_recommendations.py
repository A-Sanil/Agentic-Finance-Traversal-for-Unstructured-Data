from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from quant_agent.historical import HistoricalValidator
from quant_agent.prices import YahooChartClient
from quant_agent.recommendations import RecommendationEngine, RecommendationReport
from quant_agent.sectors import DEFAULT_SECTOR_UNIVERSE
from quant_agent.sources.sec import SECClient


@dataclass
class SectorRecommendationResult:
    sector: str
    subsector: Optional[str]
    tickers: List[str]
    report: RecommendationReport
    historical_results: List[dict[str, str]] = field(default_factory=list)

    def to_markdown(self) -> str:
        lines = [f"# Sector Recommendation Digest", "", f"Sector: {self.sector}"]
        if self.subsector:
            lines.append(f"Subsector: {self.subsector}")
        lines.extend(["", f"Tickers screened: {', '.join(self.tickers)}", ""])
        lines.append(self.report.to_markdown().strip())
        if self.historical_results:
            lines.extend(["", "## Early 2025 Validation"])
            for item in self.historical_results:
                lines.append(f"### {item['ticker']}")
                lines.append(f"- Filing date: {item['filing_date'] or 'not found'}")
                lines.append(f"- Forward return to today: {item['return'] or 'n/a'}")
                lines.append(f"- Filing summary: {item['summary']}")
        return "\n".join(lines).strip() + "\n"


class SectorRecommendationEngine:
    def __init__(self, recommendation_engine: Optional[RecommendationEngine] = None) -> None:
        self.recommendation_engine = recommendation_engine or RecommendationEngine()
        self.validator = HistoricalValidator(
            sec_client=SECClient(user_agent="Agentic Traversal <research@example.com>"),
            price_client=YahooChartClient(),
        )

    def build_sector_report(self, sector: str, subsector: Optional[str] = None, live_sources: bool = False) -> SectorRecommendationResult:
        tickers = DEFAULT_SECTOR_UNIVERSE.tickers_for(sector, subsector)
        if not tickers:
            raise ValueError(f"Unknown sector/subsector combination: {sector}/{subsector or 'all'}")

        report = self.recommendation_engine.build_report(tickers[:6], live_sources=live_sources)
        historical_results: list[dict[str, str]] = []
        # Use a few representative early-2025 checks so the report is tied to backdated data.
        for ticker in tickers[:4]:
            cik = self._cik_for_ticker(ticker)
            if not cik:
                continue
            result = self.validator.validate_early_2025(ticker, cik, sector, subsector)
            historical_results.append(
                {
                    "ticker": ticker,
                    "filing_date": result.filing_date,
                    "return": "" if result.total_return is None else f"{result.total_return:.2%}",
                    "summary": result.filing_summary[:220],
                }
            )

        report.notes.append(f"Sector mode: {sector}{' / ' + subsector if subsector else ''}")
        report.notes.append("Historical validation uses SEC filings from early 2025 and Yahoo Finance price history through today.")
        return SectorRecommendationResult(sector=sector, subsector=subsector, tickers=tickers, report=report, historical_results=historical_results)

    def _cik_for_ticker(self, ticker: str) -> Optional[str]:
        mapping = {
            "AAPL": "320193",
            "MSFT": "789019",
            "NVDA": "1045810",
            "AMD": "2488",
            "JPM": "19617",
            "BAC": "70858",
            "GS": "886982",
            "UNH": "731766",
            "JNJ": "200406",
            "XOM": "34088",
            "CVX": "93410",
            "SPY": "884394",
        }
        return mapping.get(ticker.upper())
