from quant_agent.historical import HistoricalValidator
from quant_agent.prices import YahooChartClient
from quant_agent.sources.sec import SECClient


class DummySECClient(SECClient):
    def __init__(self) -> None:
        pass

    def fetch_recent_filings(self, cik: str, count: int = 10):
        return [
            {
                "form": "10-K",
                "accession_number": "0000000000-25-000001",
                "primary_document": "dummy.htm",
                "filing_date": "2025-02-14",
            }
        ]

    def fetch_filing_text(self, cik: str, accession_number: str, primary_document: str) -> str:
        return "Revenue increased and margins improved while risk factors remained manageable."


class DummyPriceClient(YahooChartClient):
    def __init__(self) -> None:
        pass

    def total_return(self, ticker: str, start_date: str, end_date: str):
        return 0.22


def test_historical_validator_uses_early_2025_filing() -> None:
    validator = HistoricalValidator(DummySECClient(), DummyPriceClient())
    result = validator.validate_early_2025("AAPL", "320193", "technology")
    assert result.filing_date == "2025-02-14"
    assert result.total_return == 0.22
    assert "Early-2025" in result.notes[0]
