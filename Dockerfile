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
    && apt-get install -y --no-install-recommends git openssh-client \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -g 1000 ship \
    && useradd -u 1000 -g ship -s /bin/false -d /tmp ship

COPY --from=build /opt/venv /opt/venv
COPY --from=build /app/src /app/src

COPY <<'EOF' /etc/gitconfig
[pack]
    threads = 2
[core]
    deltaBaseCacheLimit = 64m
    packedGitLimit = 128m
    packedGitWindowSize = 512k
EOF

ARG GIT_SHA=unknown
ENV PATH="/opt/venv/bin:$PATH"
ENV GIT_SHA=${GIT_SHA}

WORKDIR /app

USER ship

EXPOSE 8080

# Single process (one vault clone, one in-memory content cache) but multiple
# threads so a slow content render doesn't starve liveness probes. gthread
# gives us cheap concurrency without forking multiple workers that would
# each maintain their own vault state.
CMD ["gunicorn", \
     "--worker-class", "gthread", \
     "--workers", "1", \
     "--threads", "4", \
     "--bind", "0.0.0.0:8080", \
     "--access-logfile", "-", \
     "--access-logformat", "%(t)s %(s)s %(M)sms %(m)s %(U)s%(q)s %(b)sb", \
     "ship:create_app()"]
