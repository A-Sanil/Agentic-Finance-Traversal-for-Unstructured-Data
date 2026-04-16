from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

from bs4 import BeautifulSoup


@dataclass
class StructuredFiling:
    filing_type: str
    key_topics: List[str] = field(default_factory=list)
    risk_sentences: List[str] = field(default_factory=list)
    performance_sentences: List[str] = field(default_factory=list)
    liquidity_sentences: List[str] = field(default_factory=list)

    def to_bullets(self) -> List[str]:
        bullets: list[str] = []
        if self.key_topics:
            bullets.extend(self.key_topics[:4])
        if self.performance_sentences:
            bullets.extend(self.performance_sentences[:3])
        if self.risk_sentences:
            bullets.extend(self.risk_sentences[:3])
        if self.liquidity_sentences:
            bullets.extend(self.liquidity_sentences[:3])
        return bullets


class StructuredFilingParser:
    KEYWORDS = {
        "growth": ["revenue", "sales", "growth", "demand", "margin"],
        "risk": ["risk", "uncertain", "headwind", "litigation", "competition"],
        "liquidity": ["liquidity", "cash", "debt", "borrow", "credit"],
        "operations": ["operations", "supply chain", "production", "inventory"],
        "guidance": ["guidance", "outlook", "expects", "forecast", "project"],
    }

    def parse(self, raw_text: str) -> StructuredFiling:
        text = self._normalize(raw_text)
        filing_type = self._detect_filing_type(text)
        sentences = self._sentences(text)

        key_topics: list[str] = []
        risk_sentences: list[str] = []
        performance_sentences: list[str] = []
        liquidity_sentences: list[str] = []

        for sentence in sentences:
            lowered = sentence.lower()
            if any(keyword in lowered for keyword in self.KEYWORDS["growth"]):
                performance_sentences.append(sentence)
                if "revenue" in lowered or "growth" in lowered:
                    key_topics.append(sentence)
            if any(keyword in lowered for keyword in self.KEYWORDS["risk"]):
                risk_sentences.append(sentence)
            if any(keyword in lowered for keyword in self.KEYWORDS["liquidity"]):
                liquidity_sentences.append(sentence)
            if any(keyword in lowered for keyword in self.KEYWORDS["guidance"]):
                key_topics.append(sentence)

        if not key_topics and sentences:
            key_topics.extend(sentences[:2])

        return StructuredFiling(
            filing_type=filing_type,
            key_topics=self._dedupe(key_topics),
            risk_sentences=self._dedupe(risk_sentences),
            performance_sentences=self._dedupe(performance_sentences),
            liquidity_sentences=self._dedupe(liquidity_sentences),
        )

    def _normalize(self, raw_text: str) -> str:
        soup = BeautifulSoup(raw_text, "html.parser")
        text = soup.get_text(" ")
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _sentences(self, text: str) -> List[str]:
        parts = re.split(r"(?<=[.!?])\s+", text)
        return [part.strip() for part in parts if part.strip()]

    def _detect_filing_type(self, text: str) -> str:
        lowered = text.lower()
        for filing_type in ("10-k", "10-q", "8-k", "def 14a"):
            if filing_type in lowered:
                return filing_type.upper()
        return "FILING"

    def _dedupe(self, sentences: List[str]) -> List[str]:
        seen = set()
        deduped: list[str] = []
        for sentence in sentences:
            normalized = sentence.strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            deduped.append(normalized)
        return deduped
