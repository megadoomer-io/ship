.PHONY: run test lint format typecheck check docker-build docker-run

run:
	uv run flask --app ship run --debug

test:
	uv run pytest

lint:
	uv run ruff check src/ tests/

format:
	uv run ruff format src/ tests/

typecheck:
	uv run mypy src/

check: lint typecheck test

docker-build:
	docker build -t ship:local .

docker-run:
	docker run --rm -p 8080:8080 ship:local
