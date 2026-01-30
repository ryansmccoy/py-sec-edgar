.PHONY: install lint test docs build docker-build docker-run clean

# Package name
PACKAGE := py-sec-edgar

install:
	uv sync --dev

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy py_sec_edgar/src/

format:
	uv run ruff check --fix .
	uv run ruff format .

test:
	uv run pytest

test-cov:
	uv run pytest --cov=py_sec_edgar/src/ --cov-report=html --cov-report=term

docs:
	cd py_sec_edgar && uv run mkdocs build

docs-serve:
	cd py_sec_edgar && uv run mkdocs serve

build:
	uv build

clean:
	rm -rf dist/ .pytest_cache/ .mypy_cache/ .ruff_cache/ htmlcov/ .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Generate ecosystem docs
ecosystem:
	python scripts/generate_ecosystem_docs.py -o ECOSYSTEM.md

# Extract TODOs for all projects
todos-all:
	python scripts/extract_todos.py --write-all

# Run example workflows
example-rss:
	uv run python -m py_sec_edgar workflows rss --show-entries --count 10 --list-only

example-daily:
	uv run python -m py_sec_edgar workflows daily --tickers AAPL --days-back 7 --forms "8-K" --no-download
