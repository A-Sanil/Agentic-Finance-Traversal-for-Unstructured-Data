from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from quant_agent.llm import GeminiSummarizer
from quant_agent.sources import SECClient, TwitterClient, WebSourceClient


@dataclass
class RecommendationItem:
    ticker: str
    thesis: str
    reasons: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    risk_notes: List[str] = field(default_factory=list)


@dataclass
class RecommendationReport:
    title: str
    generated_at: str
    items: List[RecommendationItem]
    notes: List[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        lines = [f"# {self.title}", "", f"Generated: {self.generated_at}", ""]
        for item in self.items:
            lines.append(f"## {item.ticker}")
            lines.append(f"Thesis: {item.thesis}")
            if item.reasons:
                lines.append("Reasons:")
                for reason in item.reasons:
                    lines.append(f"- {reason}")
            if item.sources:
                lines.append("Sources:")
                for source in item.sources:
                    lines.append(f"- {source}")
            if item.risk_notes:
                lines.append("Risk notes:")
                for risk in item.risk_notes:
                    lines.append(f"- {risk}")
            lines.append("")
        if self.notes:
            lines.append("## Notes")
            for note in self.notes:
                lines.append(f"- {note}")
        return "\n".join(lines).strip() + "\n"


class RecommendationEngine:
    def __init__(self) -> None:
        self.google_api_key = os.getenv("GOOGLE_API_KEY", "")
        self.sec_client = SECClient(user_agent=os.getenv("SEC_USER_AGENT", "Agentic Traversal <research@example.com>"))
        self.twitter_client = TwitterClient()
        self.web_client = WebSourceClient()
        self.summarizer = GeminiSummarizer()

    def build_report(self, tickers: List[str], sec_ciks: Optional[Dict[str, str]] = None) -> RecommendationReport:
        sec_ciks = sec_ciks or {}
        items: list[RecommendationItem] = []
        for ticker in tickers:
            sec_context = self._collect_sec_context(sec_ciks.get(ticker.upper(), ""))
            twitter_context = self.twitter_client.search(f"{ticker} stock OR {ticker} earnings", limit=5)
            web_context = self._collect_web_context(ticker)

            thesis = self._thesis_from_context(ticker, sec_context, twitter_context, web_context)
            reasons = self._reasons_from_context(ticker, sec_context, twitter_context, web_context)
            sources = self._sources_from_context(sec_context, twitter_context, web_context)
            risk_notes = self._risk_notes_from_context(sec_context, twitter_context, web_context)

            items.append(
                RecommendationItem(
                    ticker=ticker.upper(),
                    thesis=thesis,
                    reasons=reasons,
                    sources=sources,
                    risk_notes=risk_notes,
                )
            )

        return RecommendationReport(
            title="Stock Recommendation Digest",
            generated_at=datetime.now(timezone.utc).isoformat(),
            items=items,
            notes=[
                "This report is generated from public sources and should be used for research only.",
                "Use the Google API key via environment variable only; never hardcode secrets in the repository.",
            ],
        )

    def _collect_sec_context(self, cik: str) -> list[dict[str, str]]:
        if not cik:
            return []
        filings = self.sec_client.fetch_recent_filing_texts(cik, count=2)
        context: list[dict[str, str]] = []
        for filing in filings:
            context.append(
                {
                    "source": f"SEC {filing.get('form', '')} {filing.get('filing_date', '')}",
                    "accession_number": filing.get("accession_number", ""),
                    "text": filing.get("text", ""),
                }
            )
        return context

    def _collect_web_context(self, ticker: str) -> list[dict[str, str]]:
        rss_sources = [
            "https://www.sec.gov/Archives/edgar/usgaap.rss.xml",
        ]
        context: list[dict[str, str]] = []
        for feed_url in rss_sources:
            try:
                entries = self.web_client.fetch_rss(feed_url, limit=3)
                context.extend(entries)
            except Exception:
                continue
        context.append(self.web_client.fetch_url(f"https://finance.yahoo.com/quote/{ticker}"))
        return context

    def _thesis_from_context(self, ticker: str, sec_context: list[dict[str, str]], twitter_context: list[dict[str, str]], web_context: list[dict[str, str]]) -> str:
        sec_texts = [item.get("text", "") for item in sec_context if item.get("text")]
        if sec_texts:
            summary = self.summarizer.summarize_bullets(f"{ticker} SEC filings", sec_texts[:2])
            return summary.text
        if sec_context:
            return f"{ticker} shows publicly reported filing activity that can support a research thesis around fundamentals and risk."
        if twitter_context:
            return f"{ticker} has active market discussion that should be cross-checked against filings before any allocation."
        return f"{ticker} is included as a placeholder candidate pending deeper public-source review."

    def _reasons_from_context(self, ticker: str, sec_context: list[dict[str, str]], twitter_context: list[dict[str, str]], web_context: list[dict[str, str]]) -> list[str]:
        reasons: list[str] = []
        sec_texts = [item.get("text", "") for item in sec_context if item.get("text")]
        if sec_texts:
            bullet_summary = self.summarizer.summarize_bullets(f"{ticker} filing evidence", sec_texts[:2])
            reasons.extend([line.lstrip("- ") for line in bullet_summary.text.splitlines() if line.strip()][:4])
        elif sec_context:
            reasons.append("SEC filings provide direct evidence of recent management disclosure and formal risk factors.")
        if twitter_context:
            reasons.append("Twitter discussion can surface momentum, sentiment shifts, and catalysts for manual review.")
        if web_context:
            reasons.append("Web sources add market context, headlines, and cross-checks for the filing narrative.")
        if not reasons:
            reasons.append("No strong evidence returned from the public-source collectors in this run.")
        return reasons

    def _sources_from_context(self, sec_context: list[dict[str, str]], twitter_context: list[dict[str, str]], web_context: list[dict[str, str]]) -> list[str]:
        sources: list[str] = []
        for item in sec_context[:3]:
            sources.append(item.get("source", "SEC filing"))
        for item in twitter_context[:3]:
            sources.append(f"Twitter: {item.get('user', 'unknown')} -> {item.get('url', '')}")
        for item in web_context[:3]:
            title = item.get("title") or item.get("url", "Web source")
            sources.append(title)
        return sources[:8]

    def _risk_notes_from_context(self, sec_context: list[dict[str, str]], twitter_context: list[dict[str, str]], web_context: list[dict[str, str]]) -> list[str]:
        notes: list[str] = []
        if sec_context:
            notes.append("Check filing dates carefully for stale disclosures and event-driven updates.")
        if twitter_context:
            notes.append("Twitter data is noisy and should be treated as a signal for follow-up, not a primary truth source.")
        if web_context:
            notes.append("Web sources may vary in reliability; verify facts against filings before acting.")
        return notes
