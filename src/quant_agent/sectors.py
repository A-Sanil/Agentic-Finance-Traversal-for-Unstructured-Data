from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class SectorUniverse:
    sectors: Dict[str, List[str]]
    subsectors: Dict[str, Dict[str, List[str]]]

    def sector_names(self) -> List[str]:
        return sorted(self.sectors.keys())

    def subsector_names(self, sector: str) -> List[str]:
        return sorted(self.subsectors.get(sector, {}).keys())

    def tickers_for(self, sector: str, subsector: Optional[str] = None) -> List[str]:
        sector_key = sector.lower()
        if subsector:
            return list(self.subsectors.get(sector_key, {}).get(subsector.lower(), []))
        return list(self.sectors.get(sector_key, []))


DEFAULT_SECTOR_UNIVERSE = SectorUniverse(
    sectors={
        "technology": ["AAPL", "MSFT", "NVDA", "AMD", "AVGO", "ORCL", "ADBE", "CRM"],
        "financials": ["JPM", "BAC", "GS", "MS", "WFC", "C", "BLK", "SCHW"],
        "healthcare": ["UNH", "JNJ", "PFE", "MRK", "ABBV", "TMO", "LLY", "DHR"],
        "industrials": ["GE", "CAT", "HON", "UPS", "BA", "LMT", "DE", "ETN"],
        "energy": ["XOM", "CVX", "SLB", "COP", "EOG", "MPC", "PSX", "VLO"],
        "utilities": ["NEE", "DUK", "SO", "EXC", "AEP", "SRE", "XEL", "PCG"],
        "consumer_discretionary": ["AMZN", "TSLA", "HD", "MCD", "NKE", "SBUX", "LOW", "BKNG"],
        "communication_services": ["GOOGL", "META", "NFLX", "TMUS", "DIS", "VZ", "T", "CHTR"],
        "etfs": ["SPY", "QQQ", "XLK", "XLF", "XLV", "XLI", "XLE", "XLU"],
    },
    subsectors={
        "technology": {
            "software": ["MSFT", "ORCL", "ADBE", "CRM"],
            "semiconductors": ["NVDA", "AMD", "AVGO"],
            "hardware": ["AAPL"],
        },
        "financials": {
            "banks": ["JPM", "BAC", "WFC", "C"],
            "asset_management": ["BLK", "SCHW", "MS"],
            "markets": ["GS", "MS", "BLK"],
        },
        "healthcare": {
            "pharma": ["PFE", "MRK", "ABBV", "LLY"],
            "medtech": ["TMO", "DHR"],
            "managed_care": ["UNH"],
        },
        "industrials": {
            "aerospace": ["BA", "LMT"],
            "machinery": ["CAT", "DE", "ETN"],
            "logistics": ["UPS"],
        },
        "energy": {
            "integrated_oil": ["XOM", "CVX"],
            "oil_services": ["SLB"],
            "exploration": ["COP", "EOG"],
        },
    },
)
