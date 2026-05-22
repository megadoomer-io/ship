# syntax=docker/dockerfile:1

# --- Build stage ---
FROM python:3.13-slim AS build

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml ./
RUN python -m venv /opt/venv \
    && uv pip install --python /opt/venv/bin/python -r pyproject.toml

COPY src/ src/
RUN uv pip install --python /opt/venv/bin/python --no-deps .

# --- Runtime stage ---
FROM python:3.13-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -g 1000 ship \
    && useradd -u 1000 -g ship -s /bin/false -M ship

COPY --from=build /opt/venv /opt/venv
COPY --from=build /app/src /app/src

ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

USER ship

EXPOSE 8080

CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:8080", "ship:create_app()"]
