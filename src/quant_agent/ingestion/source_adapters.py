from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Dict, Optional

from quant_agent.schemas import IngestRequest


@dataclass
class NormalizedDocument:
    document_id: str
    source_url: str
    source_type: str
    title: Optional[str]
    raw_text: str
    cleaned_text: str
    metadata: Dict[str, str] = field(default_factory=dict)
    ingested_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class SourceAdapter(ABC):
    source_type: str = "generic"

    @abstractmethod
    def normalize(self, request: IngestRequest) -> NormalizedDocument:
        raise NotImplementedError

    def _document_id(self, request: IngestRequest, cleaned_text: str) -> str:
        payload = f"{request.source_url}|{request.source_type}|{request.title or ''}|{cleaned_text}"
        return sha256(payload.encode("utf-8")).hexdigest()[:16]

    def _clean_text(self, text: str) -> str:
        lines = [line.strip() for line in text.splitlines()]
        cleaned = " ".join(part for part in lines if part)
        return " ".join(cleaned.split())


class GenericSourceAdapter(SourceAdapter):
    source_type = "generic"

    def normalize(self, request: IngestRequest) -> NormalizedDocument:
        cleaned_text = self._clean_text(request.raw_text)
        return NormalizedDocument(
            document_id=self._document_id(request, cleaned_text),
            source_url=str(request.source_url),
            source_type=request.source_type,
            title=request.title,
            raw_text=request.raw_text,
            cleaned_text=cleaned_text,
            metadata={
                "adapter": self.source_type,
                "source_type": request.source_type,
                "ingestion_mode": "raw_text",
            },
        )


class SECSourceAdapter(GenericSourceAdapter):
    source_type = "sec"

    def normalize(self, request: IngestRequest) -> NormalizedDocument:
        document = super().normalize(request)
        document.metadata.update(
            {
                "adapter": self.source_type,
                "source_family": "public_filing",
                "priority": "high",
            }
        )
        return document


class WebSourceAdapter(GenericSourceAdapter):
    source_type = "web"

    def normalize(self, request: IngestRequest) -> NormalizedDocument:
        document = super().normalize(request)
        document.metadata.update(
            {
                "adapter": self.source_type,
                "source_family": "public_web",
                "priority": "medium",
            }
        )
        return document


class TranscriptSourceAdapter(GenericSourceAdapter):
    source_type = "transcript"

    def normalize(self, request: IngestRequest) -> NormalizedDocument:
        document = super().normalize(request)
        document.metadata.update(
            {
                "adapter": self.source_type,
                "source_family": "earnings_transcript",
                "priority": "high",
            }
        )
        return document


class SourceAdapterRegistry:
    def __init__(self) -> None:
        self._adapters: Dict[str, SourceAdapter] = {
            "sec_filing": SECSourceAdapter(),
            "sec": SECSourceAdapter(),
            "web": WebSourceAdapter(),
            "transcript": TranscriptSourceAdapter(),
            "generic": GenericSourceAdapter(),
        }

    def get(self, source_type: str) -> SourceAdapter:
        return self._adapters.get(source_type, self._adapters["generic"])
