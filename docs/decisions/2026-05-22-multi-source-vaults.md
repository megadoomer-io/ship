# Multi-Source Vault Support

**Date:** 2026-05-22
**Status:** Deferred to v2

## Context

The current design assumes a single vault repo (`obsidian-vaults`) with a single vault directory (`general/`). Two future needs:

1. **Multiple source repos** -- Ship may need to pull from repos beyond the Obsidian vault (e.g., project-specific docs, separate knowledge bases)
2. **Multiple vaults within a repo** -- `obsidian-vaults` is plural; only the `general/` vault is relevant today, but others may become relevant

## Current Design

Single `SHIP_VAULT_REPO` env var, single `SHIP_VAULT_PATH`, single git clone/pull loop. Deploy key is scoped to the obsidian-vaults repo specifically.

## Future Design Considerations

- Config-driven source list (repo URL, local path, subdirectory, pull interval)
- Per-source deploy keys (already started -- sealed secret named for the target repo, not the consumer)
- Content module needs to know which source to read from for each content type
