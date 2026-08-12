.PHONY: install test lint fmt schema ingest demo serve docker-build docker-up docker-down clean

install:
	pip install -e ".[dev,local,api]" -c constraints.txt

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

# The HTTP API against a local checkout. `make ingest` first — the server reads
# the index, it does not build one (the container's entrypoint does that part).
serve:
	uvicorn methodos.api:app --host 127.0.0.1 --port 8000 --reload

# `docker compose build` would refuse without ANTHROPIC_API_KEY — compose
# interpolates the whole file before it knows you only asked to build, and the
# service definition requires the key. Building needs no key, so build directly.
docker-build:
	docker build -t methodos-ai:local .

docker-up:
	docker compose up

docker-down:
	docker compose down

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache build dist *.egg-info data/chroma
