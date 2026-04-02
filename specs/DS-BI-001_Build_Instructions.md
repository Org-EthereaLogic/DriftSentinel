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
databricks bundle validate --target dev --var="catalog=<existing_uc_catalog>"
DATABRICKS_CONFIG_PROFILE=<profile> databricks bundle validate --target dev --var="catalog=<existing_uc_catalog>"
```

Expected result in Phase 2: the bundle validates, resolves `resources/*.yml`,
and requires an explicit existing Unity Catalog catalog instead of relying on
an unsafe hard-coded default.

## 4. Deployment Activation

Deploy and run with the same catalog selection:

```bash
DATABRICKS_CONFIG_PROFILE=<profile> databricks bundle deploy --target dev --var="catalog=<existing_uc_catalog>"
DATABRICKS_CONFIG_PROFILE=<profile> databricks bundle run benchmark_job --target dev --var="catalog=<existing_uc_catalog>"
```

Expected result: the bundle deploys Databricks jobs and pipelines into the
workspace and the benchmark job terminates successfully when the package and
catalog inputs are valid.

## 5. Manual Workspace Import

Upload the `notebooks/` directory to a Databricks workspace to run the package
from the deployed bundle files when available, falling back to GitHub for
standalone imports. The notebooks include packaged example templates for the
bootstrap path, and `01_register_dataset.py` plus
`05_run_control_benchmark.py` also accept optional workspace YAML paths for
customized dataset and benchmark policies.

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
