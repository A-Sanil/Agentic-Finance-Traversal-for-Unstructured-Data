from quant_agent.sector_recommendations import SectorRecommendationEngine


def test_sector_recommendation_engine_builds_technology_report() -> None:
    engine = SectorRecommendationEngine()
    result = engine.build_sector_report("technology", "semiconductors", live_sources=False)

    assert result.sector == "technology"
    assert "NVDA" in result.tickers
    assert result.report.items
    assert result.historical_results
