# Agentic Traversal of Unstructured Data

Agentic traversal platform for unstructured financial data and quant research.

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

## README Assets

See [docs/readme_images.md](docs/readme_images.md) for a concrete list of images to add to this README, including an architecture diagram, API screenshot, recommendation report preview, and backtest chart.

## Run locally

```bash
python -m uvicorn --app-dir src quant_agent.api.main:app --reload
```
