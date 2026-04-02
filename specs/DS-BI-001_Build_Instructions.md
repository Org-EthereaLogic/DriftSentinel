# DS-BI-001: DriftSentinel Build Instructions

| Field | Value |
| --- | --- |
| Document ID | DS-BI-001 |
| Version | 1.0 |
| Status | Draft |
| Author | Anthony Johnson |
| Date | 2026-04-01 |

## 1. Pre-Implementation Quality-Control Gate

Before substantive product code, verify:

- `.codacy/README.md` exists
- `codecov.yaml` exists
- `.snyk` exists
- `.github/workflows/ci.yml` references all three secret names:
  `CODACY_PROJECT_TOKEN`, `CODECOV_PROJECT_TOKEN`, `SNYK_PROJECT_TOKEN`

## 2. Local Build

```bash
uv sync --all-groups
uv run ruff check .
uv run mypy src/driftsentinel tests
uv run pytest
```

## 3. Bundle Validation

```bash
databricks bundle validate
```

## 4. Deployment

```bash
databricks bundle deploy --target dev
databricks bundle run --target dev <resource>
```

## 5. Manual Workspace Import

Upload the `notebooks/` directory to a Databricks workspace and follow
`00_quickstart_setup.py`.

## 6. Placeholder Scan

```bash
PATTERN='TO''DO|FIX''ME|TB''D|PLACE''HOLDER'; rg -n "$PATTERN" specs .claude CLAUDE.md docs
```

Expected result: no matches.
