# Markdown Rendering Approach

**Date:** 2026-05-22
**Status:** Accepted
**Decision:** mistune 3.x + custom preprocessor

## Context

Ship renders Obsidian vault markdown as HTML. Obsidian uses extensions beyond standard markdown: `[[wiki links]]`, `#hierarchical/tags`, YAML frontmatter, task checkboxes.

## Libraries Evaluated

- **`obsidianmd-parser`** (PyPI, v0.4.0, Jan 2026) -- full vault parser with Python object model: wikilinks, tags, frontmatter, sections, tasks, dataview queries, backlink graph, similarity search. Parser only, no HTML rendering. Overkill for a viewer app but could be useful if Ship ever needs structured data extraction (e.g., building a project timeline from vault entries, querying tasks, analyzing backlinks).

- **`python-markdown`** with `wikilinks` extension -- standard library, built-in wikilinks extension converts `[[links]]` to HTML anchors. Also has `meta` (frontmatter), `tables`, `tasklist` extensions. Viable alternative to mistune.

- **`obsidian-html`** (GitHub) -- converts Obsidian notes to proper markdown and optionally to HTML sites. More of a static site generator than a rendering library.

## Decision

**mistune 3.x + custom 40-line preprocessor** (`src/ship/markdown.py`)

- Strip YAML frontmatter (regex)
- Convert `[[wiki links|alias]]` to bold text (links don't resolve in browser)
- Convert `#project/tags` to styled `<span>` elements
- mistune handles the rest (tables, task lists, standard markdown)

## Why

Ship is a thin viewer rendering pre-curated content. The preprocessing is minimal and well-scoped. Adding a vault-analysis library would introduce unnecessary complexity and dependencies for what amounts to three regex substitutions.

## Revisit When

- Ship needs structured access to vault data (timeline views, task queries, tag frequency analysis) -- revisit `obsidianmd-parser` for the object model
- mistune's plugin ecosystem proves limiting for new Obsidian syntax -- consider `python-markdown` as an alternative
- Vault content types grow beyond what regex preprocessing handles cleanly
