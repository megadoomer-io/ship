# Ship Agent Instructions

## Claude-First Repository

Ship is a claude-first repo. Claude is the primary developer; humans provide direction, review, and approval. All context needed to work autonomously lives in this file and docs/.

Key implications:
- Invest in test coverage (Claude's primary feedback mechanism)
- Keep this file current with architecture and conventions
- Use GitHub Issues as the work surface
- Understand the deploy pipeline before pushing (push to main = deploy to prod)

## Architecture

- **Framework:** Flask with Jinja2 templates
- **Markdown:** mistune 3.x with custom Obsidian preprocessor (`src/ship/markdown.py`)
- **Vault sync:** Background git clone/pull via APScheduler (`src/ship/vault.py`)
- **Auth:** oauth2-proxy headers (X-Auth-Request-User), no auth code in the app
- **Deploy:** megadoomer-do cluster, ArgoCD auto-sync, GHCR images

## Conventions

- Python 3.13+, strict mypy, ruff for lint/format
- Flask app factory pattern in `src/ship/__init__.py`
- Templates in `src/ship/templates/`, static files in `src/ship/static/`
- Tests in `tests/`, run with `make check`
- Decision records in `docs/decisions/`

## Development

```bash
make run       # Flask dev server with hot reload
make check     # Lint + typecheck + test
make format    # Auto-format with ruff
```

## Deploy Pipeline

Push to main triggers: build image -> push to GHCR -> update megadoomer-config -> ArgoCD auto-sync. The app is live at ship.megadoomer.io.

## TODOs

- [ ] Local development instance with mock vault data for testing without a real vault clone
- [ ] Multi-source vault support (see docs/decisions/2026-05-22-multi-source-vaults.md)
- [ ] Retro summary rendering on observation deck (pending /work-summarize skill update)
- [ ] Git SHA in /healthz output (adopt from resonance's QoL patterns)
