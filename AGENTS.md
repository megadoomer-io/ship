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

## Content-Type Ownership

Each Ship view owns specific vault content types. Do not add content from one view's domain to another view without updating this spec.

| View             | Min Role | Vault Path(s)                              | Content Type     |
|------------------|----------|--------------------------------------------|------------------|
| Bridge           | CAPTAIN  | claude/active-work/INDEX.md                | Active work      |
|                  |          | journal/entries/\<today\>/*.md             | Today's entries  |
|                  |          | journal/summaries/weekly/ (latest only)    | Weekly summary   |
| Observation Deck | OFFICERS | journal/summaries/weekly/**/*.md           | Weekly summaries |
|                  |          | journal/entries/**/*.md                    | Daily entries    |
| Porthole         | CREW     | journal/summaries/weekly/**/*.md           | Weekly summaries |
| Course           | CREW     | claude/plans/weekly/ (current plan only)   | Current plan     |
| Captain's Log    | CREW     | claude/plans/weekly/**/*.md (past)         | Past plans       |
|                  |          | journal/summaries/retro/**/*.md            | Retro summaries  |

Notes:
- **Course = the current heading.** It shows ONLY the single most recent plan (latest week, current non-superseded version) — what's in front of us now. It does not list history.
- **Captain's Log = the voyage record.** Past plans (every plan except the current one, including superseded versions of the current week) interleaved with all retros, most recent first. Within a week the retro sorts above its plan (the retro is the later event). Each week reads as a pair: the plan, and the retro reflecting on it.
- Plans are split by recency, not duplicated: the current plan is on Course, everything older is in the Captain's Log. A plan moves from Course to the Log when a newer plan supersedes it or a new week begins.
- Cross-links inside the Log are intra-page anchors (a past plan and its retro both live there): a retro's `related_plan` and a plan's `related_retro` resolve to sibling cards. "See all activity" on a retro links out to the Observation Deck.
- Weekly summaries appear on Porthole (as standalone cards) and inside the Observation Deck feed (as collapsible section headers that group daily entries by week). This is an accepted boundary crossing because they serve different structural purposes.
- Journal entries appear on Bridge (today only) and Observation Deck (full history, nested under week groups). This is a scope split, not duplication.
- Active Work appears ONLY on Bridge. Officers see historical activity on Observation Deck but not the active work dashboard.
- Bridge shows only the LATEST weekly summary for context. Obs Deck and Porthole show the full history.

## Vault Frontmatter Contract

Ship reads these frontmatter fields from vault files. Changes to field names, types, or semantics in the agent instructions must be coordinated with Ship's content.py.

### Currently consumed (sorting/dating)

| File type        | Field          | Type          | Used for                    |
|------------------|----------------|---------------|-----------------------------|
| Weekly summaries | period_start   | date (ISO)    | Sort order, date display    |
|                  | metrics        | dict          | Commit/PR counts in labels  |
| Retro summaries  | period_start   | date (ISO)    | Sort order, date display    |
|                  | related_plan   | str (YYYY-Www-vN) | retro→plan cross-link   |
| Weekly plans     | week           | str (YYYY-Www)| Sort order, date extraction |
|                  | version        | int           | Plan version (anchor id)    |
|                  | superseded_by  | str (YYYY-Www-vN) | Dim old versions, link to replacement |
|                  | related_retro  | str (YYYY-Www)| plan→retro link; present only after retrospected |

**Canonical date field**: `period_start` (ISO date string). Ship's content.py has a 3-tier fallback for weekly summaries (period_start -> week+year frontmatter -> filename regex), but only `period_start` should be relied on going forward. New summaries written by `/work-summarize` should always include `period_start`.

**Cross-linking and supersession** (matches the dotfiles plan/retro contract):

- Plans and retros for the same week link to each other. A plan's `related_retro` targets the retro card's anchor; a retro's `related_plan` targets a specific plan version's anchor. `related_retro` is back-filled onto the final plan version when the retro is written, so the current week's (not-yet-retrospected) plan renders no retro link.
- `superseded_by` on a plan version is the sole signal Ship uses to dim it — Ship does not infer "latest version wins." The current version omits the field.
- **Derived anchors** (computed in content.py, not read from frontmatter): plan cards get `id="<plan_id>"` (`<week>-v<version>`, falling back to the filename stem); retro cards get `period` (the `YYYY-Www` stem) so the dormant obs-deck link and the new plan link both resolve.

### Available for filtering (not yet consumed)

These fields are written by the agent instructions but not yet read by Ship. The filtering feature will consume them.

| File type        | Field   | Type         | Values                                      |
|------------------|---------|--------------|---------------------------------------------|
| Journal entries  | tags    | list[str]    | #project/org/repo, #chore, #feat, #fix, etc |
| Work events      | type    | str          | add, delivered, complete, block, triage, etc |
|                  | section | str          | in-progress, prs, issues, jira, blocked, etc|
|                  | item    | str          | kebab-case slug (work item identifier)      |

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
- (none currently)

### Deprioritized
- [ ] Multi-source vault support (see docs/decisions/2026-05-22-multi-source-vaults.md) — gathering team feedback, may be YAGNI
- [ ] HTML sanitization in markdown.render(): add nh3 or bleach allowlist if Ship ever ingests content from untrusted sources. Multi-source vault support is the trigger. Current single-owner vault is trusted input.

### Done
- [x] **ship#11: filtering feature** — sticky filter bar (third nav row), `/` hotkey, debounced text match against entry-card / `[data-filterable]` textContent, section structure preserved (Active Work, Weekly Summary, week/day headers stay visible), auto-expand collapsed details containing matches, Escape / clear button restores. Per-page filterable units: entry-cards (Porthole/Captain's Log/Course/Obs Deck day entries) and `[data-filterable]` (Bridge daily entries). Static asset cache-bust via `?v=<mtime>` so JS/CSS edits ship without manual hard-reload.
- [x] `[-]` partial task checkbox state — mistune's `task_lists` only handles `[ ]`/`[x]`; post-processor in `markdown.py` adds `class="task-list-item-checkbox partial"` for `[-]` items, styled as a dashed orange box.
- [x] SHIP_API_TOKEN: token-based auth bypass for automated tools
- [x] /static/ auth bypass in megadoomer-config HTTPRoute
- [x] DESIGN.md: formalize megadoomer.io visual language
- [x] Retro summary rendering on observation deck — retros now written to `journal/summaries/retro/` with correct frontmatter
- [x] Design review: migrated layout spacing to `--space-*` tokens (both Ship and Portal CSS), documented tokenization policy in DESIGN.md
- [x] Local dev shared.css: Flask serves Portal's shared.css in debug mode via sibling repo path
- [x] In-memory content cache with generation-counter invalidation
- [x] Infinite scroll via HTML fragment API endpoints
- [x] Porthole vs Captain's Log content dedup (ship#8) — retros removed from Porthole, Captain's Log is the dedicated retro view
- [x] Collapsible entries on Porthole and Bridge
- [x] DX docs: CHANGELOG, CONTRIBUTING, issue templates
- [x] Remove `?token=` query param auth — header-based auth only (X-Ship-Token, Authorization Bearer)
- [x] Content auto-refresh — JS polls /api/version every 30s, reloads when cache generation changes
- [x] View-as controls in nav bar with two-tier nav and dropdown (2ba931b)
