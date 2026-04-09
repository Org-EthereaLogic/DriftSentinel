# DS-BI-001: DriftSentinel Build Instructions

| Field | Value |
| --- | --- |
| Document ID | DS-BI-001 |
| Version | 1.1 |
| Status | Draft |
| Author | Anthony Johnson |
| Date | 2026-04-02 |

## 1. Pre-Implementation Quality-Control Gate

Before substantive product code, verify:

- `.codacy/README.md` exists
- `codecov.yaml` exists
- `.snyk` exists
- `.github/workflows/ci.yml` wires:
  - Codecov upload via `CODECOV_TOKEN` (preferred) or `CODECOV_PROJECT_TOKEN`
    for backward compatibility
  - Snyk auth via `SNYK_PROJECT_TOKEN`
  - Codacy CI analysis via `codacy/codacy-analysis-cli-action`

Codacy has two valid CI modes:

1. Default analysis mode: no Codacy token required, results appear in the GitHub
   Actions log and the workflow fails on detected issues.
2. Client-side upload mode: requires a Codacy token plus enabling `Run analysis on your build server` in Codacy repository settings before CI uploads will succeed.

The current repository workflow uses default analysis mode to avoid depending on
that optional external Codacy setting.

## 2. Local Build

```bash
uv sync --all-groups
uv run ruff check .
uv run mypy src/driftsentinel tests
uv run pytest
```

## 3. Catalog Access Check

Before bundle validation, prove the selected Unity Catalog catalog exists in
the intended workspace:

```bash
make bundle-catalog-check CATALOG=<existing_uc_catalog> PROFILE=<profile>
databricks catalogs get <existing_uc_catalog> -p <profile>
```

Expected result: the CLI returns catalog metadata for the exact catalog you
plan to pass into the bundle.

## 4. Bundle Validation

Authenticate the Databricks CLI through `.databrickscfg`,
`DATABRICKS_CONFIG_PROFILE`, or `DATABRICKS_*` environment variables, then
run:

```bash
make bundle-validate CATALOG=<existing_uc_catalog> PROFILE=<profile>
databricks bundle validate -p <profile> --target dev --var="catalog=<existing_uc_catalog>"
DATABRICKS_CONFIG_PROFILE=<profile> databricks bundle validate --target dev --var="catalog=<existing_uc_catalog>"
```

Expected result in Phase 2: the bundle validates, resolves `resources/*.yml`,
and requires an explicit existing Unity Catalog catalog instead of relying on
an unsafe hard-coded default. `Validation OK!` proves bundle/auth/resource
resolution only; it does not prove deploy or job execution. The bundle defines
a shared runtime volume plus fail-closed job surfaces that require dataset and
policy inputs at run time.

## 5. Deployment Activation

Deploy and run with the same catalog selection:

```bash
databricks bundle deploy -p <profile> --target dev --var="catalog=<existing_uc_catalog>"
databricks bundle run dataset_pipeline_job -p <profile> --target dev --var="catalog=<existing_uc_catalog>,dataset_id=<registered_dataset>,drift_policy_path=/Volumes/<existing_uc_catalog>/<schema>/driftsentinel_runtime/policies/drift_policy.yml,benchmark_policy_path=/Volumes/<existing_uc_catalog>/<schema>/driftsentinel_runtime/policies/benchmark_policy.yml"
```

Expected result: the bundle deploys the runtime volume, Databricks jobs, and
the app resource into the workspace. Dataset-backed jobs terminate
successfully when the package, catalog, dataset, and policy inputs are valid.
If required job inputs are omitted, the run must fail closed instead of
silently using demo or synthetic execution.

## 6. Manual Workspace Import

Upload the `notebooks/` directory to a Databricks workspace to run the package
from the deployed bundle files when available, falling back to GitHub for
standalone imports. The notebooks include packaged example templates for the
bootstrap path, and `01_register_dataset.py` plus
`05_run_control_benchmark.py` also accept optional workspace YAML paths for
customized dataset and benchmark policies.

## 7. Governance Guard Check

```bash
uv run pytest tests/test_governance_guards.py -q
```

Expected result: executable and bundle surfaces contain no banned scaffold
markers, `databricks.yml` includes `resources/*.yml`, and the bundle no longer
encodes Databricks auth interpolation.

## 8. Canonical Placeholder Scan

```bash
PATTERN='TO''DO|FIX''ME|TB''D|PLACE''HOLDER'; rg -n "$PATTERN" specs .claude CLAUDE.md docs
```

Expected result: no matches.
