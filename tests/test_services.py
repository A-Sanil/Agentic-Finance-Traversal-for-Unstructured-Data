from quant_agent.schemas import Horizon, IngestRequest, SignalRequest
from quant_agent.services import AgentService


def test_generate_signal_includes_fusion_metadata() -> None:
    service = AgentService()
    result = service.generate_signal(
        SignalRequest(
            query="Evaluate the company for long-term upside",
            tickers=["MSFT"],
            horizons=[Horizon.swing, Horizon.position],
        )
    )

    assert result.metadata["mode"] == "confidence_weighted_fusion"
    assert result.portfolio_bias == "overweight_quality"
    assert result.ticker_signals
    assert result.ticker_signals[0].evidence


def test_ingest_deduplicates_by_source_and_text() -> None:
    service = AgentService()
    request = IngestRequest(
        source_url="https://example.com/doc",
        source_type="web",
        title="Doc",
        raw_text="This is a sample document.",
    )
    first = service.ingest(request)
    second = service.ingest(request)

    assert first.document_id == second.document_id
