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
- **Auth:** Group-based roles via GitHub teams (Dex OIDC -> oauth2-proxy -> X-Auth-Request-Groups header). Roles: cargo < crew < officers < captain. Global `admins` group maps to CAPTAIN. API token bypass via X-Ship-Token header. View-as feature for role impersonation.
- **Deploy:** megadoomer-do cluster, ArgoCD auto-sync, GHCR images

## Conventions

- Python 3.13+, strict mypy, ruff for lint/format
- Flask app factory pattern in `src/ship/__init__.py`
- Templates in `src/ship/templates/`, static files in `src/ship/static/`
- Tests in `tests/`, run with `make check`
- Decision records in `docs/decisions/`
- Ship's design system extends Portal's (`DESIGN.md` here is an extension doc, not standalone). Shared tokens (colors, fonts, spacing, radius, nav, footer) are defined in Portal's `DESIGN.md` and delivered via `shared.css`. Ship's `DESIGN.md` documents only Ship-specific component patterns and any parameter deviations from the shared system, with reasoning for each deviation. When adding visual patterns that also exist in Portal, define the pattern in Portal first, then reference it from Ship.

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

### Active
- (none currently)

### Needs discussion / planning
- [ ] Content updating strategy (live reload, polling, manual refresh)
- [ ] Porthole vs Captain's Log content dedup (ship#8) — product decision on overlapping retro content
- [ ] View-as controls in nav bar on desktop widths (floating pill as mobile fallback)

### Deprioritized
- [ ] Multi-source vault support (see docs/decisions/2026-05-22-multi-source-vaults.md) — gathering team feedback, may be YAGNI
- [ ] HTML sanitization in markdown.render(): add nh3 or bleach allowlist if Ship ever ingests content from untrusted sources. Multi-source vault support is the trigger. Current single-owner vault is trusted input.
- [ ] Remove `?token=` query param auth: header-based auth (X-Ship-Token) is sufficient and avoids log/history/Referer leakage. Low priority since query param only works via port-forward today.

### Done
- [x] SHIP_API_TOKEN: token-based auth bypass for automated tools
- [x] /static/ auth bypass in megadoomer-config HTTPRoute
- [x] DESIGN.md: formalize megadoomer.io visual language
- [x] Retro summary rendering on observation deck — retros now written to `journal/summaries/retro/` with correct frontmatter
- [x] Design review: migrated layout spacing to `--space-*` tokens (both Ship and Portal CSS), documented tokenization policy in DESIGN.md
- [x] Local dev shared.css: Flask serves Portal's shared.css in debug mode via sibling repo path
- [x] In-memory content cache with generation-counter invalidation
- [x] Infinite scroll via HTML fragment API endpoints
- [x] Collapsible entries on Porthole and Bridge
- [x] DX docs: CHANGELOG, CONTRIBUTING, issue templates
