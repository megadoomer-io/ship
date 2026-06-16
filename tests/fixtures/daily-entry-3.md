---
tags:
  - "#project/missionlane/argo-config"
  - "#chore"
produced_by: work-track/0.8.0
---

# 14:00 -- cert-manager CRD migration debugging

**Produced by**: work-track/0.8.0 **Tags**: #project/missionlane/argo-config #chore **Links**: abc1234

## What I did

Investigated and resolved cert-manager v1.17 CRD migration failures in infra-dev. The upgrade introduced new CRD fields that required manual annotation updates before helm could reconcile.

## How I did it

- Identified the failing CRD by reading cert-manager upgrade notes (which didn't mention this)
- Compared CRD manifests between v1.16 and v1.17 to find new required fields
- Applied manual CRD patch via kubectl, then re-ran the helm upgrade
- Documented the pattern in cerebral for future chart upgrades with CRD changes

## Challenges

- Upstream docs did not mention the CRD migration requirement
- Had to read the cert-manager source code to understand the new field semantics
- The failure mode was silent (no error, just perpetual reconciliation loop)
