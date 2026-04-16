from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict

import requests


@dataclass
class HistoricalPricePoint:
    date: str
    close: float


class YahooChartClient:
    def __init__(self, timeout: int = 30) -> None:
        self.timeout = timeout

    def fetch_close_series(self, ticker: str, start_date: str, end_date: str) -> list[HistoricalPricePoint]:
        period1 = int(datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc).timestamp())
        period2 = int(datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc).timestamp())
        url = (
            f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
            f"?period1={period1}&period2={period2}&interval=1d&includeAdjustedClose=true"
        )
        response = requests.get(url, timeout=self.timeout, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        payload: Dict = response.json()
        result = payload.get("chart", {}).get("result", [])
        if not result:
            return []
        chart = result[0]
        timestamps = chart.get("timestamp", [])
        closes = chart.get("indicators", {}).get("quote", [{}])[0].get("close", [])
        points: list[HistoricalPricePoint] = []
        for timestamp, close in zip(timestamps, closes):
            if close is None:
                continue
            date = datetime.fromtimestamp(timestamp, tz=timezone.utc).date().isoformat()
            points.append(HistoricalPricePoint(date=date, close=float(close)))
        return points

    def total_return(self, ticker: str, start_date: str, end_date: str) -> Optional[float]:
        series = self.fetch_close_series(ticker, start_date, end_date)
        if len(series) < 2:
            return None
        start = series[0].close
        end = series[-1].close
        if start <= 0:
            return None
        return (end - start) / start
