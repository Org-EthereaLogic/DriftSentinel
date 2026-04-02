# cleanup_workspace

Safely clean local generated artifacts. Dry-run by default.

## Variables

mode: $ARGUMENTS

## Safe to Remove

`__pycache__/`, `*.pyc`, `*.pyo`, `.pytest_cache/`, `.ruff_cache/`,
`.mypy_cache/`, `.DS_Store`, `dist/`, `build/`, `*.egg-info/`, `coverage.xml`,
`htmlcov/`

## Protected

`specs/`, `docs/`, `.claude/`, `adws/`, `report/`, `src/`, `tests/`, root
governance documents

## Rules

- dry-run unless `--execute` is explicitly provided
- do not remove git-tracked files
- do not touch evidence artifacts in `report/`

## Report

Return a dry-run or execute-mode cleanup summary.
