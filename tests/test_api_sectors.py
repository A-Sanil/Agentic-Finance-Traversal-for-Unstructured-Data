from fastapi.testclient import TestClient

from quant_agent.api.main import app

client = TestClient(app)


def test_sector_list_endpoint_returns_sectors() -> None:
    response = client.get("/sectors")
    assert response.status_code == 200
    payload = response.json()
    assert "technology" in payload["sectors"]


def test_sector_recommendation_endpoint_returns_markdown() -> None:
    response = client.post(
        "/sector/recommendations/markdown",
        json={"sector": "technology", "subsector": "semiconductors", "live_sources": False},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "Sector Recommendation Digest" in payload["markdown"]
    assert "Early 2025 Validation" in payload["markdown"]
