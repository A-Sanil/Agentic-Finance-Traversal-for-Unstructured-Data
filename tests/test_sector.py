from quant_agent.sectors import DEFAULT_SECTOR_UNIVERSE


def test_sector_universe_returns_tech_names() -> None:
    tickers = DEFAULT_SECTOR_UNIVERSE.tickers_for("technology")
    assert "AAPL" in tickers
    assert "MSFT" in tickers


def test_sector_universe_returns_semiconductor_subsector() -> None:
    tickers = DEFAULT_SECTOR_UNIVERSE.tickers_for("technology", "semiconductors")
    assert "NVDA" in tickers
    assert "AMD" in tickers
