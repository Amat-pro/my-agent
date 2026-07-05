.PHONY: install install-dev format lint typecheck test check run docker-build docker-rebuild docker-prune docker-up docker-down

PYTHON ?= python3

install:
	$(PYTHON) -m pip install -e .

install-dev:
	$(PYTHON) -m pip install -e ".[dev]"

format:
	$(PYTHON) -m ruff format .
	$(PYTHON) -m ruff check --fix .

lint:
	$(PYTHON) -m ruff format --check .
	$(PYTHON) -m ruff check .

typecheck:
	$(PYTHON) -m mypy app

test:
	$(PYTHON) -m pytest

check: lint typecheck test
	$(PYTHON) -c "from app.main import create_app; create_app()"

run:
	$(PYTHON) -m uvicorn app.main:create_app --factory --reload --log-config app/observability/logging/uvicorn.json

docker-build:
	docker compose build api

docker-rebuild:
	docker compose build --no-cache api
	docker image prune --force --filter dangling=true

docker-prune:
	docker image prune --force --filter dangling=true

docker-up: docker-build
	docker compose up

docker-down:
	docker compose down
