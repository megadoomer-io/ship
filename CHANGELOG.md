# Changelog

## Unreleased

### Added
- In-memory content cache with generation-counter invalidation on vault sync
- Infinite scroll via HTML fragment API endpoints (`/api/feed`, `/api/timeline`, `/api/retros`)
- Collapsible entries on Porthole (timeline cards) and Bridge (daily entries)
- Spacing tokenization policy in DESIGN.md
- Shared.css dev route (serves from sibling Portal repo in debug mode)

### Changed
- Migrated all layout spacing from hardcoded rem to `--space-*` design tokens
- Porthole initial load reduced from 20 to 10 items (remaining load on scroll)
- Captain's Log initial load reduced from 20 to 10 items

## 2026-05-27

### Added
- DESIGN.md as extension of Portal's design system
- Floating pill view-as controls (moved from header)
- Irken alien script shadow on page headings
- Uppercase group-label style for page headings
- API token auth via `X-Ship-Token` header
- Auth-snippet on nginx-ingress for browse tool access
- 404 error page with nautical theming
- README.md with quickstart, pages, auth, and config docs
- Test coverage reporting

### Fixed
- API token sealed secret trailing newline breaking prod auth
- Unknown routes returning 403 instead of 404
- CSS token compliance (all colors, border-radius via design tokens)
- Legacy `megadoomer-admins` dual-check removed

## 2026-05-26

### Added
- Unified auth model across Portal and Ship
- Admin group mapping (`admins` -> CAPTAIN role)
- View-as role impersonation for all authenticated users
- SHIP_SECRET_KEY sealed secret for persistent sessions
- RollingUpdate deployment strategy
- Smoke test expanded to 12/12 checks

### Fixed
- CI race condition in publish.yaml (git pull --rebase on megadoomer-config)

## 2026-05-22

### Added
- Initial Ship release: Flask app with Obsidian vault rendering
- Role-based access control (cargo < crew < officers < captain)
- Bridge, Observation Deck, Porthole, Captain's Log pages
- Markdown rendering with Obsidian preprocessor (wiki links, tags, frontmatter)
- Background vault sync via APScheduler
- Path prefix middleware for `/ship` routing
