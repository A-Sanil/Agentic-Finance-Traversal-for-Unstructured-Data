from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from typing import Optional

from quant_agent.recommendations import RecommendationEngine
from quant_agent.sector_recommendations import SectorRecommendationEngine
from quant_agent.sectors import DEFAULT_SECTOR_UNIVERSE
from quant_agent.schemas import BacktestRequest, BacktestResponse, FusedRecommendation, IngestRequest, IngestResponse, SignalRequest
from quant_agent.services import AgentService
from quant_agent.web.app import router as web_router

app = FastAPI(title="Agentic Traversal of Unstructured Data", version="0.1.0")
service = AgentService()
recommendation_engine = RecommendationEngine()
sector_recommendation_engine = SectorRecommendationEngine()
app.include_router(web_router)


class RecommendationRequest(BaseModel):
    tickers: list[str] = Field(default_factory=list)
    sec_ciks: dict[str, str] = Field(default_factory=dict)
    live_sources: bool = Field(default=False)

Optional[str]
class SectorRecommendationRequest(BaseModel):
    sector: str = Field(..., min_length=2)
    subsector: Optional[str] = None
    live_sources: bool = Field(default=False)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/ingest", response_model=IngestResponse)
def ingest_document(request: IngestRequest) -> IngestResponse:
    return service.ingest(request)


@app.post("/signals", response_model=FusedRecommendation)
def generate_signals(request: SignalRequest) -> FusedRecommendation:
    response = service.generate_signal(request)
    if response.recommendation == "insufficient evidence":
        raise HTTPException(status_code=409, detail="insufficient evidence to generate recommendation")
    return response


@app.post("/backtest", response_model=BacktestResponse)
def run_backtest(request: BacktestRequest) -> BacktestResponse:
    return service.backtest(request)


@app.post("/recommendations/markdown")
def build_recommendation_markdown(request: RecommendationRequest) -> dict[str, str]:
    report = recommendation_engine.build_report(request.tickers, request.sec_ciks, live_sources=request.live_sources)
    return {"markdown": report.to_markdown()}


@app.get("/sectors")
def list_sectors() -> dict[str, list[str]]:
    return {"sectors": DEFAULT_SECTOR_UNIVERSE.sector_names()}


@app.post("/sector/recommendations/markdown")
def build_sector_recommendation_markdown(request: SectorRecommendationRequest) -> dict[str, str]:
    result = sector_recommendation_engine.build_sector_report(
        request.sector,
        request.subsector,
        live_sources=request.live_sources,
    )
    return {"markdown": result.to_markdown()}
