PYTHON ?= /Users/aadityasanil/Desktop/Ai agent for traversing unstructured data/.venv/bin/python

.PHONY: test run lint

test:
	$(PYTHON) -m pytest

run:
	$(PYTHON) -m uvicorn quant_agent.api.main:app --reload

lint:
	$(PYTHON) -m ruff check src tests
