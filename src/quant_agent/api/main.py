from __future__ import annotations

from fastapi import FastAPI, HTTPException

from quant_agent.schemas import BacktestRequest, BacktestResponse, IngestRequest, IngestResponse, SignalRequest, FusedRecommendation
from quant_agent.services import AgentService

app = FastAPI(title="Agentic Traversal of Unstructured Data", version="0.1.0")
service = AgentService()


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
