DB := data/app.db
HOST ?= 127.0.0.1
PORT ?= 8000

.PHONY: setup seed run test lint format typecheck evaluate check

setup:
	uv sync

seed:
	uv run python -m circle_recommender.db.seed

$(DB):
	uv run python -m circle_recommender.db.seed

run: $(DB)
	uv run uvicorn circle_recommender.api.app:app --host $(HOST) --port $(PORT)

test:
	uv run pytest

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff format .
	uv run ruff check --fix .

typecheck:
	uv run mypy

evaluate: seed
	uv run python scripts/evaluate.py

check: lint typecheck test evaluate
