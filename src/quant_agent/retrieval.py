from __future__ import annotations

from dataclasses import dataclass
from typing import List

from quant_agent.ingestion.pipeline import InMemoryIngestionIndex
from quant_agent.schemas import EvidenceSpan


@dataclass
class RetrievalService:
    index: InMemoryIngestionIndex

    def retrieve(self, query: str, max_results: int = 10) -> List[EvidenceSpan]:
        query_terms = {term.lower() for term in query.split() if term}
        scored: list[tuple[float, str, str, str]] = []

        for chunk in self.index.chunks:
            text_lower = chunk.text.lower()
            overlap = sum(1 for term in query_terms if term in text_lower)
            if overlap == 0:
                continue
            score = min(1.0, 0.35 + 0.12 * overlap)
            title = chunk.metadata.get("adapter", "indexed chunk")
            scored.append((score, chunk.chunk_id, title, chunk.text))

        if not scored:
            fallback = list(self.index.documents.values())[:max_results]
            for document in fallback:
                scored.append(
                    (
                        0.42,
                        document.document_id,
                        document.title or document.source_type,
                        document.cleaned_text[:240],
                    )
                )

        if not scored:
            scored.append(
                (
                    0.40,
                    "bootstrap-evidence",
                    "bootstrap",
                    f"{query} :: bootstrap evidence will be replaced by indexed documents.",
                )
            )

        scored.sort(key=lambda item: item[0], reverse=True)
        results: list[EvidenceSpan] = []
        for score, source_id, title, excerpt in scored[:max_results]:
            results.append(
                EvidenceSpan(
                    source_id=source_id,
                    url=None,
                    title=title,
                    excerpt=excerpt[:400],
                    score=score,
                )
            )
        return results
