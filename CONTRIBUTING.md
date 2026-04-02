# Contributing to DriftSentinel

## Before You Start

1. Read `CLAUDE.md`, `AGENTS.md`, `CONSTITUTION.md`, and `DIRECTIVES.md`.
2. Read the relevant `specs/DS-*.md` documents for the area you plan to change.
3. Read the `README.md` in the directory you plan to work in — every directory
   contains one describing its contents and current state.
4. Run `/prime` to orient to the repository.
5. Run `/start` to verify your local environment is functional.

## Workflow

1. Create a feature or fix branch from `main`.
2. Make your changes following the `Plan -> Act -> Verify -> Report` pattern.
3. Run `/test` and ensure all checks pass.
4. Run `/pull-request` to create a governed PR.

## Commit Conventions

Use conventional commits: `<type>(<scope>): <description>`

Types: `feat`, `fix`, `chore`, `docs`, `test`, `refactor`, `perf`

## Quality Gates

All contributions must pass:

- Placeholder scan (no forbidden markers)
- `uv run ruff check .`
- `uv run mypy src/driftsentinel tests`
- `uv run pytest`

## Evidence Rules

- PASS claims require machine-readable and human-readable evidence.
- Append-only evidence under `report/` must not be modified or deleted.
- `specs/` is canonical and must be updated when behavior changes.
