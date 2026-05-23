---
date: 2026-05-23
produced_by: work-track/0.8.0
---

### 09:15 -- Ship CI fix and healthz improvements

**Produced by**: work-track/0.8.0
**Tags**: #project/mikedougherty/ship #bugfix #feature
**Links**: [db9ddae](https://github.com/megadoomer-io/ship/commit/db9ddae)

#### What I did
Fixed the lint-and-test CI workflow by moving dev dependencies from `[project.optional-dependencies]` to `[dependency-groups]`. Added git SHA to the `/healthz` endpoint.

#### How I did it
- Diagnosed CI failure: `ruff` not found because `uv run` doesn't install optional deps
- Changed pyproject.toml to use `[dependency-groups]` which uv installs by default
- Added Docker build arg for GIT_SHA, exposed as env var, returned in healthz JSON

---
