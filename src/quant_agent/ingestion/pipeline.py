from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List

from quant_agent.ingestion.source_adapters import NormalizedDocument, SourceAdapterRegistry
from quant_agent.schemas import IngestRequest, IngestResponse


@dataclass
class DocumentChunk:
    chunk_id: str
    document_id: str
    chunk_index: int
    text: str
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class InMemoryIngestionIndex:
    documents: Dict[str, NormalizedDocument] = field(default_factory=dict)
    chunks: List[DocumentChunk] = field(default_factory=list)

    def upsert_document(self, document: NormalizedDocument, chunks: Iterable[DocumentChunk]) -> None:
        self.documents[document.document_id] = document
        for chunk in chunks:
            self.chunks.append(chunk)


class IngestionPipeline:
    def __init__(self, registry: SourceAdapterRegistry | None = None, index: InMemoryIngestionIndex | None = None) -> None:
        self.registry = registry or SourceAdapterRegistry()
        self.index = index or InMemoryIngestionIndex()

    def ingest(self, request: IngestRequest) -> IngestResponse:
        adapter = self.registry.get(request.source_type)
        document = adapter.normalize(request)
        chunks = list(self._chunk_text(document.cleaned_text, document.document_id, document.metadata))
        self.index.upsert_document(document, chunks)
        return IngestResponse(
            document_id=document.document_id,
            chunks_indexed=len(chunks),
            source_type=request.source_type,
            accepted=True,
        )

    def _chunk_text(self, text: str, document_id: str, metadata: Dict[str, str]) -> Iterable[DocumentChunk]:
        if not text:
            return []

        chunk_size = 900
        overlap = 150
        chunks: list[DocumentChunk] = []
        start = 0
        index = 0
        while start < len(text):
            end = min(len(text), start + chunk_size)
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"{document_id}-{index}",
                        document_id=document_id,
                        chunk_index=index,
                        text=chunk_text,
                        metadata=dict(metadata),
                    )
                )
                index += 1
            if end >= len(text):
                break
            start = max(end - overlap, start + 1)
        return chunks
