.PHONY: run dev test lint format typecheck check docker-build docker-run

run:
	uv run flask --app ship run --debug

dev:
	uv run python -c "from ship.dev import create_mock_vault; create_mock_vault('/tmp/ship-dev-vault')"
	SHIP_VAULT_PATH=/tmp/ship-dev-vault SHIP_API_TOKEN=dev-token uv run flask --app ship run --debug

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
