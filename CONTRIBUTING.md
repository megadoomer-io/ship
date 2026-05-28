# Contributing

Ship is a claude-first repository. Claude is the primary developer; humans provide direction, review, and approval.

## Development

```bash
make dev     # Start dev server with mock vault data
make check   # Lint + typecheck + test (run before submitting)
make format  # Auto-format with ruff
```

## Before Submitting

1. Run `make check` and fix any failures
2. Keep commits focused and logically organized
3. Update CHANGELOG.md under "Unreleased"
4. Update AGENTS.md TODOs if your change completes or adds items

## Architecture

See [AGENTS.md](AGENTS.md) for architecture overview, conventions, and deploy pipeline docs.
See [DESIGN.md](DESIGN.md) for the visual design system and CSS token conventions.
