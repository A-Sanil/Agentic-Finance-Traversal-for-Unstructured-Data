# Agentic Traversal of Unstructured Data

Agentic traversal platform for unstructured financial data and quant research. Ingests public financial documents, normalizes them through a structured pipeline, retrieves evidence with citation traceability, and generates evidence-backed investment recommendations with execution summaries.

## v1 Scope

- Ingest public financial documents and web sources
- Normalize and validate source documents via adapter-driven architecture
- Retrieve evidence with citation traceability and retrieval-augmented generation (RAG)
- Emit evidence-backed portfolio recommendation digests (markdown format)
- Sector-first discovery to explore investment opportunities by market segment
- Automatic execution summary generation with traversed sources and insights
- Run evaluation and backtesting against labeled data
- Quality assurance via deterministic test suite and LLM evaluation framework

## Current Status

This repository includes:

- FastAPI backend with RESTful endpoints for ingestion, recommendations, sector discovery, and backtesting
- Core request/response schemas with Pydantic validation
- Source adapter registry for SEC, web, Twitter, and RSS sources
- In-memory indexed retrieval service with deterministic chunking
- Sector universe and subsector mapping
- Browser UI for sector-first recommendation requests
- Execution summary writer for persisting agent runs with full traceability

## Project Structure

```
.
├── src/
│   └── quant_agent/
│       ├── api/
│       │   ├── main.py              # FastAPI application entrypoint
│       │   └── routes.py            # API route definitions
│       ├── web/
│       │   └── app.py               # Browser UI route
│       ├── sources/
│       │   ├── sec.py               # SEC EDGAR data client
│       │   ├── twitter.py           # Twitter/X scraper
│       │   ├── web.py               # Generic web scraper and RSS ingestion
│       │   └── ...                  # Additional source adapters
│       ├── ingestion/
│       │   ├── pipeline.py          # Chunking and indexing pipeline
│       │   └── source_adapters.py   # Source normalization layer
│       ├── recommendations.py       # Evidence-backed recommendation engine
│       ├── sector_recommendations.py # Sector-first report builder
│       ├── historical.py            # Early-2025 validation and backtesting
│       ├── retrieval.py             # Evidence retrieval from in-memory index
│       ├── prices.py                # Historical price data (Yahoo Finance)
│       ├── parsers.py               # Structured filing parser
│       ├── llm.py                   # Optional Gemini summarizer wrapper
│       ├── execution_summary.py     # Execution summary writer (async/sync)
│       └── ...
├── tests/
│   ├── test_api.py                  # FastAPI endpoint tests
│       ├── test_api_sectors.py      # Sector endpoint tests
│       ├── test_recommendations.py  # Recommendation engine tests
│       ├── test_sector_recommendations.py
│       ├── test_historical.py       # Early-2025 validation tests
│       ├── test_ingestion.py        # Pipeline and adapter tests
│       ├── test_services.py         # Service layer tests
│       └── ...
├── evals/
│   └── golden_dataset.csv           # Ground-truth eval data (source, risk_factor, actual_outcome)
├── data/
│   └── (raw financial documents for local testing: PDFs, transcripts)
├── outputs/
│   └── (execution summaries: TICKER_YYYYMMDD_HHMMSS.txt)
├── docs/
│   └── readme_images.md             # Architecture and UI assets
├── README.md                        # This file
├── pyproject.toml                   # Python project metadata and dependencies
└── Makefile
```

## How The RAG Works

The retrieval system is designed to turn noisy public financial text into a structured research workflow:

1. **Source Collection**: Public sources are collected from SEC filings (10-K, 10-Q, 8-K), web pages, RSS feeds, and social context.
2. **Source Normalization**: Source adapters normalize each document into a consistent internal format with metadata tags (source type, timestamp, URL/CIK).
3. **Chunking & Indexing**: The ingestion pipeline chunks the text with configurable overlap and stores chunks in an in-memory index with full document lineage.
4. **Evidence Retrieval**: Retrieval returns the most relevant evidence spans for a query, preserving citations and source references.
5. **Recommendation Generation**: The recommendation layer uses retrieved evidence to generate a markdown digest with thesis, supporting reasons, source citations, and risk warnings.
6. **Execution Summary**: After analysis, the agent automatically generates a `.txt` execution summary documenting:
   - Timestamp and target company/ticker
   - Exact documents traversed during the run
   - Extracted data points and insights with confidence scores
   - Final market prediction and synthesized conclusion

For recruiters and stakeholders, the point is not a chat demo. The point is the pipeline: document ingestion, structured normalization, retrieval with traceability, evidence-backed recommendations, and automatic persistent execution summaries for audit and validation.

## Testing & Evaluation Architecture

### Unit & Integration Tests (`/tests`)

The test suite uses pytest to validate deterministic logic:

- **API Tests** (`test_api.py`, `test_api_sectors.py`): Validate FastAPI endpoints, request/response contracts, and HTTP status codes.
- **Ingestion Tests** (`test_ingestion.py`): Test chunking, adapter normalization, and index population.
- **Recommendation Tests** (`test_recommendations.py`, `test_sector_recommendations.py`): Validate report generation, markdown formatting, and evidence citation.
- **Historical/Backtest Tests** (`test_historical.py`): Test early-2025 filing selection and forward-return calculation.
- **Service Tests** (`test_services.py`): Test core business logic and data flow.

Run the test suite:
```bash
pytest
```

### LLM Evaluation Framework (`/evals`)

The evaluation framework includes a golden dataset to measure the agent's predictive accuracy:

- **golden_dataset.csv**: Ground-truth data with columns:
  - `source_document_name`: The filing or document analyzed (e.g., `NVDA_10K_2024_12.pdf`)
  - `target_risk_factor`: The key risk or opportunity identified (e.g., `supply_chain_resilience`)
  - `company_ticker`: Stock ticker symbol
  - `prediction_date`: When the prediction was made
  - `prediction_signal`: The agent's output (BUY, HOLD, SELL, or detailed outlook)
  - `actual_return_30d`, `actual_return_90d`: Realized forward returns
  - `outcome_match`: Boolean indicating if the agent's signal aligned with subsequent price action

Use this golden dataset to compute precision, recall, and F1 scores of the agent's recommendations against real market outcomes.

### Local Testing with Raw Data (`/data`)

Place raw financial documents in `/data` for offline testing:
- SEC filings (PDF downloads from EDGAR)
- Earnings call transcripts
- Press releases and white papers
- Any other unstructured financial text

The ingestion pipeline will normalize these documents and allow the agent to generate recommendations without hitting live APIs.

## Execution Summary Format

After the agent completes a traversal, it generates a `.txt` file in `/outputs`:

```
================================================================================
EXECUTION SUMMARY REPORT
================================================================================

TIMESTAMP & TARGET
----------------------------------------
Run Timestamp: 2026-05-01T14:32:45.123456
Company: NVIDIA Corporation (NVDA)
Sector: technology
Subsector: semiconductors

SOURCES TRAVERSED
----------------------------------------
1. NVDA_10K_2024_12.pdf
2. NVDA_8K_2025_01_15.txt
3. Twitter posts from @nvidia (2025-01)
4. Reuters AI chip article (Jan 2025)

INSIGHTS UNCOVERED
----------------------------------------
- gross_margin_trend: 64% in Q4 2024, up from 60% YoY (source: NVDA_10K_2024_12.pdf, confidence: 95%)
- supply_chain_risk: "secured key capacity through Q3 2026" (source: NVDA_8K_2025_01_15.txt, confidence: 90%)
- competitive_threat: Low near-term; AMD gaining slower than expected (source: Reuters article, confidence: 75%)

MARKET PREDICTION
----------------------------------------
BUY - Strong fundamentals, sustained demand for AI infrastructure, gross margin expansion

SYNTHESIZED CONCLUSION
----------------------------------------
NVIDIA exhibits structural growth tailwinds in AI infrastructure with improving margins and de-risked supply chain. Recommend overweight position.

================================================================================
```

The `.txt` file is named `{TICKER}_{YYYYMMDD_HHMMSS}.txt` for easy organization and audit trails.

## Sector Discovery

The system expands from ticker-first usage to sector-first discovery. Users can request a sector or subsector, and the system will:

1. Fetch all tickers in that sector (e.g., technology → semiconductors → [NVDA, AMD, QCOM, ...])
2. Collect SEC filings, web context, and market signals for each ticker
3. Generate a ranked recommendation digest with sectoral thesis, individual stock scores, and risk factors
4. Generate an execution summary with full traceability of sources and decisions

Supported sectors: technology, financials, healthcare, industrials, energy, utilities, consumer discretionary, communication services, and S&P 500 subsectors.

## Development Notes

- The codebase currently runs on Python 3.9.6. Maintain compatibility with Python 3.9+ (avoid `| None` syntax; use `Optional[T]` instead).
- Ingestion is adapter-driven, so new source types (financial news APIs, alternative data, corporate actions) can be added without changing the API layer.
- Execution summaries are written asynchronously using `aiofiles` for non-blocking I/O.
- All tests are deterministic and do not require live API access (mock data is used for SEC, Yahoo Finance, etc.).
- The retrieval and backtest implementations are intentionally lightweight and deterministic while the platform is being built out.

## Installation & Setup

```bash
# Clone the repository
git clone <repo-url>
cd "Ai agent for traversing unstructured data"

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# (Optional) Add aiofiles for execution summary writing
pip install aiofiles
```

## Run Locally

### Start the FastAPI Backend

```bash
python -m uvicorn --app-dir src quant_agent.api.main:app --host 127.0.0.1 --port 8000 --reload
```

The API will be available at `http://127.0.0.1:8000`. Visit `/ui` for the browser UI.

### Run Tests

```bash
pytest
pytest -v                # Verbose output
pytest tests/test_api.py # Run specific test file
```

### Generate an Execution Summary (Python)

```python
from quant_agent.execution_summary import ExecutionSummary, ExecutionSummaryItem, write_execution_summary_sync

# Create a summary
summary = ExecutionSummary("NVIDIA Corporation", "NVDA", sector="technology", subsector="semiconductors")

# Add sources traversed
summary.add_source("NVDA_10K_2024.pdf")
summary.add_source("NVDA_8K_2025_01.txt")

# Add insights
summary.add_insight(ExecutionSummaryItem("gross_margin", "64%", "NVDA_10K_2024.pdf", confidence=0.95))
summary.add_insight(ExecutionSummaryItem("supply_chain", "Secured through Q3 2026", "NVDA_8K_2025_01.txt", confidence=0.90))

# Set prediction and conclusion
summary.set_prediction("BUY - Strong AI demand, margin expansion")
summary.set_conclusion("NVIDIA shows structural growth in AI infrastructure with improved profitability.")

# Write to disk
output_path = write_execution_summary_sync(summary, output_dir="./outputs")
print(f"Summary saved to: {output_path}")
```

## README Assets

See [docs/readme_images.md](docs/readme_images.md) for a concrete list of images to add to this README, including architecture diagrams, API screenshots, recommendation report previews, and backtest charts.

---

**For Recruiters**: This project demonstrates a full-stack financial AI system with rigorous testing, deterministic pipelines, evidence-backed reasoning, and audit-friendly execution summaries. The architecture is built for scale and observability.
