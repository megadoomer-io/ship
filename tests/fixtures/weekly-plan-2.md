---
type: weekly-plan
week: 2026-W22
version: 1
created: 2026-06-08T10:00:00-0700
items_triaged: 18
items_total: 18
staleness_threshold: 7
---

# Weekly Plan: 2026-W22 (v1)

## Commitments

### Ops & Promotions
- [ ] cert-manager v1.17 promotion (infra-dev, infra-prod, dev, staging, prod)
- [ ] Istio 1.26.1 patch rollout
- [ ] Renovate PR sweep (estimated 20+ PRs)

### Building
- [ ] Ship section-collapse feature
- [ ] Cerebral system-service hierarchy doc v2

### Reviews
- [ ] James: namespace-operator RBAC changes
- [ ] Hoey: monitoring-config kube-prometheus-stack upgrade

### Docs
- [ ] kdrift v0.4.0 release notes

## Deferred

| Item | Reason | Revisit |
|------|--------|---------|
| Multi-source vault support | Gathering team feedback, may be YAGNI | W24 |
| GKE 1.32 upgrade | Waiting on release notes review | W23 |
| SonarQube migration | Blocked on license procurement | W25 |

## Dropped

| Item | Reason |
|------|--------|
| Slack bot rewrite | Superseded by Claude MCP integration |

## Carried Forward

- Ship filtering feature (ship#11) -- not started, lower priority than section-collapse

## Blocked

- Kodem CLI integration -- waiting on vendor API access

## Retro Awareness

Last week's retro flagged over-commitment on building items when ops pipelines are active. This week has 3 active pipelines, so building commitments are scoped conservatively.

## Notes

Heavy ops week expected. cert-manager and Istio promotions are the priority. Building work is stretch.

## GSTACK REVIEW REPORT

### Eng Review

This plan shows improved ops awareness after W21's over-commitment. Three promotion pipelines are correctly prioritized above building work. The two building items (Ship section-collapse, cerebral hierarchy doc) are well-scoped and have clear completion criteria.

### Slip Forecast

Low risk on ops items (well-understood promotion workflow). Medium risk on building items if ops takes longer than expected.

### Recommendations

1. Start cert-manager promotion Monday morning to give maximum soak time
2. Batch the Renovate PR sweep into a Friday cleanup session

### VERDICT

APPROVED -- realistic scope given ops load.
