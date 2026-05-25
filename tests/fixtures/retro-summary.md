---
type: retro
period: 2026-W21
period_start: "2026-05-18"
period_end: "2026-05-24"
generated: "2026-05-24T14:42:00-07:00"
produced_by: retro/2.0.0
projects:
  - ship
  - argo-config
metrics:
  prs_authored: 12
  prs_reviewed: 34
  commits: 47
---

# Retro: W21 (May 18-24, 2026)

## Shipped
- Deployed Ship v0.1.0 to production at ship.megadoomer.io
- Added tiered role-based auth with three access levels
- Fixed vault clone OOM with git pack tuning

## Patterns
- New project bootstrap: Ship went from design doc to production in one session
- Strong focus on infrastructure and deployment automation

## Went Well
- Ship deployment was smooth with ArgoCD auto-sync
- Pre-commit hooks caught type errors early

## Didn't Go Well
- Vault clone hitting OOM required multiple debugging cycles
- Initial auth implementation needed rework for preferred-username header

## Learnings
- Git pack configuration matters for large repos in containers
- oauth2-proxy preferred-username header is more reliable than OIDC subject
