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
make dev       # Dev server with mock vault data (no real vault needed)
make run       # Flask dev server with hot reload (needs SHIP_VAULT_REPO)
make check     # Lint + typecheck + test
make format    # Auto-format with ruff
```

## Deploy Pipeline

Push to main triggers: build image -> push to GHCR -> update megadoomer-config -> ArgoCD auto-sync. The app is live at megadoomer.io/ship/.

### Post-deploy validation

Run the smoke test after routing or infrastructure changes:
```bash
~/src/github.com/megadoomer-io/megadoomer-config/scripts/smoke-test-megadoomer.sh
```

### Known CI race condition

Ship and Portal CI workflows update megadoomer-config's image tag via `kustomize edit set image` + push. If megadoomer-config was modified by another push between CI's clone and push, the CI push fails with "rejected (fetch first)." The image is built and in GHCR; only the tag update fails. Fix: manually update the tag with `kustomize edit set image` in the megadoomer-config repo, or re-run the failed workflow.

### Routing architecture

All megadoomer.io traffic routes through nginx-gateway-fabric (Gateway API HTTPRoutes) then to nginx-ingress (Kubernetes Ingress). Auth is controlled at the Ingress level, not the gateway level. nginx-gateway-fabric does not reliably handle path priority between rules in the same or across HTTPRoutes for a shared hostname.

- Ship: `/ship/*` -> nginx-ingress -> auth Ingress (`ship-web`) or no-auth Ingress (`ship-healthz`, `ship-static`)
- Portal: `/*` -> nginx-ingress -> no-auth Ingress (`portal-public`) or auth Ingress (`portal-services`)
- oauth2: `/oauth2/*` -> nginx-ingress -> ExternalName service to oauth2-proxy

## TODOs

- [ ] Multi-source vault support (see docs/decisions/2026-05-22-multi-source-vaults.md)
- [ ] Retro summary rendering on observation deck (pending /work-summarize skill update)
- [ ] SHIP_API_TOKEN: token-based auth bypass for automated tools (browse daemon benchmarking, monitoring). Skip oauth2-proxy when the right header is present.
- [x] /static/ auth bypass in megadoomer-config HTTPRoute (route directly to ship pod, skip nginx-ingress + oauth2-proxy)
- [ ] DESIGN.md: formalize megadoomer.io visual language (colors, typography, spacing, component patterns) after domain consolidation ships. Run /design-consultation to create it, then /plan-design-review to audit ship+portal against it.
