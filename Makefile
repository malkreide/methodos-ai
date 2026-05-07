.PHONY: install test lint fmt schema ingest demo clean

install:
	pip install -e ".[dev,local]"

test:
	pytest

lint:
	ruff check src tests scripts
	ruff format --check src tests scripts
	mypy src/methodos

fmt:
	ruff format src tests scripts
	ruff check --fix src tests scripts

schema:
	python scripts/regenerate_schema.py

ingest:
	python -m methodos.cli ingest

demo: ingest
	python -m methodos.cli query "we need to enter a new market without burning cash" --no-llm

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache build dist *.egg-info data/chroma
