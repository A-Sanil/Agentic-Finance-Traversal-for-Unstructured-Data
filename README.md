# Quant RAG Agent

API-first RAG and quant signal platform for unstructured financial data.

## v1 Scope

- Ingest public financial documents and web sources
- Normalize and validate source documents
- Retrieve evidence with citation traceability
- Emit a single fused portfolio recommendation layer
- Apply tax-aware personalized indexing logic for US taxable accounts
- Run evaluation and backtesting against labeled data

## Current Status

This repository starts with the backend scaffold only. The first implementation slice includes:

- FastAPI app skeleton
- Core request/response schemas
- Source adapter registry and ingestion pipeline
- In-memory indexed retrieval service
- Agent router stub

## Development Notes

- The codebase currently runs on the workspace Python 3.9 virtual environment.
- Ingestion is adapter-driven, so new source types can be added without changing the API layer.
- The current retrieval and backtest implementations are intentionally lightweight and deterministic while the platform is still being built out.

## Run locally

```bash
python -m uvicorn quant_agent.api.main:app --reload
```
