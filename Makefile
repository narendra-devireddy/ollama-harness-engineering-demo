PYTHON ?= python3
VENV ?= .venv
PIP := $(VENV)/bin/python -m pip
HARNESS_DEMO := $(VENV)/bin/harness-demo
PYTEST := $(VENV)/bin/python -m pytest

.PHONY: setup demo test clean docker-build docker-demo

setup:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install -r requirements.txt
	$(PIP) install -e .

demo:
	$(HARNESS_DEMO) compare --scenario incident-response

test:
	$(PYTEST) -p no:cacheprovider

docker-build:
	docker build -t harness-engineering-demo .

docker-demo:
	docker run --rm --env OLLAMA_API_KEY=$$OLLAMA_API_KEY harness-engineering-demo

clean:
	rm -rf .pytest_cache .ruff_cache reports src/*.egg-info
