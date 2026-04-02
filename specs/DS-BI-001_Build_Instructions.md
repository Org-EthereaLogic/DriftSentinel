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

Authenticate the Databricks CLI through `.databrickscfg`,
`DATABRICKS_CONFIG_PROFILE`, or `DATABRICKS_*` environment variables, then
run:

```bash
databricks bundle validate
DATABRICKS_CONFIG_PROFILE=<profile> databricks bundle validate
```

Expected result during Phase 0/1: the bundle scaffold validates and loads the
reserved `resources/*.yml` surfaces. Operational jobs and pipelines are added
in DS-IP-001 Phase 2.

## 4. Deployment Activation

Operational deploy/run commands apply after DS-IP-001 Phase 2 lands and the
bundle resources become runnable.

## 5. Manual Workspace Import

Upload the `notebooks/` directory to a Databricks workspace to review the
planned operator surfaces. The current scaffold notebooks fail closed until
DS-IP-001 Phase 2 is implemented.

## 6. Governance Guard Check

```bash
uv run pytest tests/test_governance_guards.py -q
```

Expected result: executable and bundle surfaces contain no banned scaffold
markers, `databricks.yml` includes `resources/*.yml`, and the bundle no longer
encodes Databricks auth interpolation.

## 7. Canonical Placeholder Scan

```bash
PATTERN='TO''DO|FIX''ME|TB''D|PLACE''HOLDER'; rg -n "$PATTERN" specs .claude CLAUDE.md docs
```

Expected result: no matches.
