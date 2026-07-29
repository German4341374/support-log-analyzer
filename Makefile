PYTHON ?= python3
VENV ?= .venv
BIN := $(VENV)/bin

.PHONY: setup format lint typecheck test coverage demo docker-build clean

setup:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/python -m pip install --upgrade pip
	$(BIN)/python -m pip install -e ".[dev]"
	$(BIN)/pre-commit install --install-hooks
	$(BIN)/pre-commit install --hook-type pre-push

format:
	$(BIN)/ruff format .
	$(BIN)/ruff check --fix .

lint:
	$(BIN)/ruff format --check .
	$(BIN)/ruff check .

typecheck:
	$(BIN)/mypy src

test:
	$(BIN)/pytest -q

coverage:
	$(BIN)/pytest --cov --cov-report=term-missing --cov-report=html

demo:
	$(BIN)/support-log-analyzer generate-demo demo.log --lines 1000

docker-build:
	docker build --tag support-log-analyzer:local .

clean:
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov dist build

