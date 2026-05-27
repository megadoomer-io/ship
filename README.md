# Ship

Viewer for AI-curated Obsidian vault journal summaries. Part of the [megadoomer.io](https://megadoomer.io) platform.

Ship renders markdown journal entries, weekly summaries, retro reports, and active work indexes from an Obsidian vault into a web interface with role-based access control.

## Quickstart

Prerequisites: [uv](https://docs.astral.sh/uv/) and Python 3.13+.

```bash
git clone https://github.com/megadoomer-io/ship.git
cd ship
make dev
# Open http://localhost:5000
```

`make dev` creates mock vault data and starts a Flask dev server with hot reload. No real Obsidian vault needed for development.

## Pages

| Page | Role Required | Description |
|------|--------------|-------------|
| Bridge | captain | Full operational view: active work, daily entries, weekly summaries |
| Observation Deck | officers | Activity feed with period filtering, active work overview |
| Porthole | crew | Timeline of retros and weekly summaries |
| Captain's Log | crew | Retro summaries with metrics and collapsible detail |

## Auth

Ship uses group-based authorization via GitHub teams through a Dex OIDC + oauth2-proxy chain. Roles in ascending order: `cargo` < `crew` < `officers` < `captain`. The global `admins` group maps to captain.

For automated access, set `SHIP_API_TOKEN` and pass it via:
- `X-Ship-Token` header
- `Authorization: Bearer <token>` header
- `?token=<token>` query parameter

## Development

```bash
make dev         # Dev server with mock vault data
make check       # Lint + typecheck + test (CI equivalent)
make format      # Auto-format with ruff
make test        # Run tests with coverage
make typecheck   # Run mypy strict
make lint        # Run ruff
```

## Configuration

| Env Var | Default | Description |
|---------|---------|-------------|
| `SHIP_VAULT_REPO` | (empty) | Git repo URL for vault sync |
| `SHIP_VAULT_PATH` | `/tmp/vault` | Path to vault content |
| `SHIP_VAULT_CLONE_PATH` | `/tmp/vault-clone` | Clone destination for git sync |
| `SHIP_PULL_INTERVAL_SECONDS` | `300` | Vault sync interval |
| `SHIP_API_TOKEN` | (empty) | Token for API auth bypass |
| `SHIP_SECRET_KEY` | (random) | Flask session secret key |
| `SHIP_PATH_PREFIX` | (empty) | URL path prefix (e.g., `/ship`) |

## Architecture

- **Framework:** Flask with Jinja2 templates
- **Markdown:** mistune 3.x with Obsidian preprocessor (wiki links, tags, frontmatter)
- **Vault sync:** Background git clone/pull via APScheduler
- **Deploy:** GHCR images, ArgoCD auto-sync to megadoomer-do cluster

See [CLAUDE.md](CLAUDE.md) for agent-oriented architecture docs and conventions.
