# Retro Summaries Architecture

**Date:** 2026-05-22
**Status:** Planned (not yet implemented)

## Decision

`/work-summarize` orchestrates retro summary generation by invoking `/retro` and consuming its output, then writing the result to the vault at `journal/summaries/retro/<decade>/<year>/`.

## Why

`/work-summarize` already owns periodic summary writing (weekly, monthly). Adding retro as another summary type keeps a single entry point for all vault summary content. `/retro` does the analysis (commit history, work patterns, shipping velocity); `/work-summarize` handles vault placement and formatting.

## Vault Path

Same structure as other summaries: `journal/summaries/retro/<decade>/<year>/`

## Ship Rendering

Ship's observation deck view renders retro summaries from the vault. The structured format (went well, didn't go well, action items, patterns, key numbers) enables both readable rendering and future trend analysis.
