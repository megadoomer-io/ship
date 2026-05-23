---
date: 2026-05-23
produced_by: work-track/0.8.0
---

### 12:30 -- Added pre-commit hooks

**Produced by**: work-track/0.8.0
**Tags**: #project/mikedougherty/ship #chore
**Links**: [9d61343](https://github.com/megadoomer-io/ship/commit/9d61343)

#### What I did
Added `.pre-commit-config.yaml` with ruff (lint + format) and mypy (strict) hooks. Same checks as `make check` and CI, catches issues before push.

#### Challenges
- Needed `additional_dependencies` in the mypy hook config to resolve Flask/mistune imports

---
