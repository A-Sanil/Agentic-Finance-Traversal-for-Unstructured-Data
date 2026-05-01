from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4
from typing import Optional

from quant_agent.ingestion.pipeline import IngestionPipeline
from quant_agent.retrieval import RetrievalService
from quant_agent.schemas import BacktestRequest, BacktestResponse, FusedRecommendation, Horizon, IngestRequest, IngestResponse, SignalRequest, TaxAction, TickerSignal


class AgentService:
    def __init__(self, ingestion_pipeline: Optional[IngestionPipeline] = None) -> None:
        self.ingestion_pipeline = ingestion_pipeline or IngestionPipeline()
        self.retriever = RetrievalService(self.ingestion_pipeline.index)

    def ingest(self, request: IngestRequest) -> IngestResponse:
        return self.ingestion_pipeline.ingest(request)

    def generate_signal(self, request: SignalRequest) -> FusedRecommendation:
        evidence = self.retriever.retrieve(request.query, request.max_results)
        target_tickers = request.tickers or ["SPY"]
        horizons = request.horizons or [Horizon.swing, Horizon.position]

        ticker_signals: list[TickerSignal] = []
        for ticker in target_tickers:
            for horizon in horizons:
                confidence = 0.78 if horizon in {Horizon.swing, Horizon.position} else 0.64
                score = 0.25 if horizon != Horizon.intraday else 0.1
                ticker_signals.append(
                    TickerSignal(
                        ticker=ticker.upper(),
                        horizon=horizon,
                        score=score,
                        confidence=confidence,
                        factors={
                            "quality": 0.61,
                            "growth": 0.54,
                            "valuation": 0.47,
                            "leverage": -0.18,
                        },
                        risk_flags=["liquidity_watch"] if ticker.upper() != "SPY" else [],
                        evidence=evidence[:3],
                    )
                )

        fused_confidence = round(sum(signal.confidence for signal in ticker_signals) / max(len(ticker_signals), 1), 3)
        recommendation = "constructive" if fused_confidence >= 0.7 else "insufficient evidence"
        portfolio_bias = "overweight_quality" if recommendation == "constructive" else "neutral"

        tax_actions = []
        if request.account_type == "taxable_us":
            tax_actions.append(
                TaxAction(
                    ticker=target_tickers[0].upper(),
                    action="harvest_candidates_scan",
                    rationale="US taxable account enabled; scan for unrealized losses and replacement baskets.",
                    estimated_tax_impact=0.0,
                )
            )

        return FusedRecommendation(
            run_id=str(uuid4()),
            query=request.query,
            recommendation=recommendation,
            confidence=fused_confidence,
            portfolio_bias=portfolio_bias,
            ticker_signals=ticker_signals,
            tax_actions=tax_actions,
            metadata={
                "horizons": [h.value for h in horizons],
                "mode": "confidence_weighted_fusion",
            },
        )

    def backtest(self, request: BacktestRequest) -> BacktestResponse:
        return BacktestResponse(
            run_id=str(uuid4()),
            strategy_name=request.strategy_name,
            sharpe=1.12,
            max_drawdown=-0.14,
            total_return=0.27,
            notes=[
                "Stub backtest initialized.",
                "Replace with event-driven simulation and tax-aware ledger.",
            ],
        )
