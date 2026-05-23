---
period: weekly
week: W21
year: 2026
produced_by: work-summarize/0.5.0
---

# Weekly Summary: W21 (May 19--25, 2026)

## Highlights

- **Ship v0.1.0 deployed to production** at ship.megadoomer.io -- Flask webapp with Obsidian-flavored markdown rendering, dark theme, oauth2-proxy auth
- Fixed CI pipeline and added git SHA to /healthz endpoint
- Added pre-commit hooks for ruff and mypy strict mode

## Work Log

| Date | Project | What | Tags |
|------|---------|------|------|
| May 22 | #project/mikedougherty/ship | Deployed Ship v0.1.0 to production | #feature |
| May 23 | #project/mikedougherty/ship | Fixed CI, added healthz SHA, pre-commit hooks | #bugfix #feature |

## Themes

- **New project bootstrap**: Ship went from design doc to production in one session
- **Developer experience**: Pre-commit hooks and CI fixes improve the local development loop
- **Automation patterns**: Adopted resonance's healthz SHA injection pattern

## Next Week

- Local development mode with mock vault data
- Evaluate multi-source vault support design
- Portal namespace migration planning
