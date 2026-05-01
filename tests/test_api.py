from fastapi.testclient import TestClient

from quant_agent.api.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ingest_document() -> None:
    response = client.post(
        "/ingest",
        json={
            "source_url": "https://www.sec.gov/example",
            "source_type": "sec_filing",
            "title": "Example 10-K",
            "raw_text": "Revenue increased and liquidity remained strong.",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["accepted"] is True
    assert payload["chunks_indexed"] >= 1


def test_generate_signals() -> None:
    response = client.post(
        "/signals",
        json={
            "query": "What signals matter most for this company?",
            "tickers": ["AAPL"],
            "horizons": ["swing", "position"],
            "account_type": "taxable_us",
            "max_results": 3,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["recommendation"] == "constructive"
    assert payload["confidence"] >= 0.7
    assert payload["tax_actions"]


def test_backtest() -> None:
    response = client.post(
        "/backtest",
        json={
            "strategy_name": "baseline",
            "start_date": "2020-01-01",
            "end_date": "2024-12-31",
            "tickers": ["SPY"],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["strategy_name"] == "baseline"
    assert payload["sharpe"] is not None
