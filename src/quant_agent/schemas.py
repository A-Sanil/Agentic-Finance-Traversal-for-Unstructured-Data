from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, HttpUrl


class Horizon(str, Enum):
    intraday = "intraday"
    swing = "swing"
    position = "position"
    long_term = "long_term"


class EvidenceSpan(BaseModel):
    source_id: str = Field(..., description="Stable source identifier")
    url: Optional[HttpUrl] = Field(default=None, description="Source URL")
    title: Optional[str] = None
    excerpt: str = Field(..., description="Quoted supporting text")
    score: float = Field(..., ge=0.0, le=1.0)


class SignalRequest(BaseModel):
    query: str = Field(..., min_length=3)
    tickers: list[str] = Field(default_factory=list)
    horizons: list[Horizon] = Field(default_factory=lambda: [Horizon.swing, Horizon.position])
    account_type: str = Field(default="taxable_us")
    max_results: int = Field(default=10, ge=1, le=50)


class TaxAction(BaseModel):
    ticker: str
    action: str
    rationale: str
    estimated_tax_impact: Optional[float] = None


class TickerSignal(BaseModel):
    ticker: str
    horizon: Horizon
    score: float = Field(..., ge=-1.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    factors: dict[str, float] = Field(default_factory=dict)
    risk_flags: list[str] = Field(default_factory=list)
    evidence: list[EvidenceSpan] = Field(default_factory=list)


class FusedRecommendation(BaseModel):
    run_id: str
    query: str
    recommendation: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    portfolio_bias: str
    ticker_signals: list[TickerSignal]
    tax_actions: list[TaxAction] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class IngestRequest(BaseModel):
    source_url: HttpUrl
    source_type: str = Field(..., min_length=2)
    title: Optional[str] = None
    raw_text: str = Field(..., min_length=1)


class IngestResponse(BaseModel):
    document_id: str
    chunks_indexed: int
    source_type: str
    accepted: bool


class BacktestRequest(BaseModel):
    strategy_name: str = Field(..., min_length=3)
    start_date: str
    end_date: str
    tickers: list[str] = Field(default_factory=list)


class BacktestResponse(BaseModel):
    run_id: str
    strategy_name: str
    sharpe: Optional[float] = None
    max_drawdown: Optional[float] = None
    total_return: Optional[float] = None
    notes: list[str] = Field(default_factory=list)
