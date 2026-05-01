from quant_agent.ingestion.pipeline import IngestionPipeline
from quant_agent.schemas import IngestRequest


def test_ingestion_pipeline_indexes_chunks_by_adapter() -> None:
    pipeline = IngestionPipeline()
    response = pipeline.ingest(
        IngestRequest(
            source_url="https://www.sec.gov/example",
            source_type="sec_filing",
            title="Example 10-K",
            raw_text="Revenue increased.\nLiquidity remained strong.\nManagement discussed leverage risk.",
        )
    )

    assert response.accepted is True
    assert response.chunks_indexed >= 1
    assert response.source_type == "sec_filing"
    assert response.document_id in pipeline.index.documents


def test_ingestion_pipeline_uses_source_adapter_metadata() -> None:
    pipeline = IngestionPipeline()
    pipeline.ingest(
        IngestRequest(
            source_url="https://example.com/article",
            source_type="web",
            title="Web Article",
            raw_text="The company reported stronger margins and better cash flow.",
        )
    )

    document = next(iter(pipeline.index.documents.values()))
    assert document.metadata["adapter"] == "web"
    assert document.metadata["source_family"] == "public_web"
