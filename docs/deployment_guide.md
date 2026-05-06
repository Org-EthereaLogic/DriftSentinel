# DriftSentinel Deployment Guide

## Prerequisites

- Databricks workspace with Unity Catalog enabled
- An existing Unity Catalog catalog and schema for DriftSentinel tables
  (for example `adb_dev.default`)
- Compute cluster with Python 3.11+
- Databricks CLI installed and authenticated through `.databrickscfg`,
  `DATABRICKS_CONFIG_PROFILE`, or `DATABRICKS_*` environment variables
- A terraform-compatible binary on PATH for any `databricks bundle …`
  invocation. **OpenTofu (`tofu`) is recommended** — see
  [Terraform binary](#terraform-binary) below.

### Terraform binary

The Databricks CLI pins terraform `1.5.5` and verifies the auto-downloaded
binary against an upstream PGP signature that expired in 2025. On a fresh
machine the first `databricks bundle deploy` (or any other bundle command
that materializes terraform state) fails with:

> `Error: error downloading Terraform: unable to verify checksums signature: openpgp: key expired`

The fix is to point the Databricks CLI at a terraform-compatible binary
through two environment variables it already honors:
`DATABRICKS_TF_EXEC_PATH` and `DATABRICKS_TF_VERSION`. OpenTofu (`tofu`)
is a wire-compatible drop-in for terraform that the Databricks CLI accepts.

**Recommended install (macOS):**

```bash
brew install opentofu
```

**Make targets handle the wiring automatically.** Every Make target that
invokes `databricks bundle …` or `driftsentinel databricks …`
(`bundle-validate`, `bundle-deploy`, `app-deploy`, `bootstrap`) sources
`scripts/databricks_tf_env.sh` before the underlying command runs. The
helper applies this precedence:

1. **Operator override.** If `DATABRICKS_TF_EXEC_PATH` is already set,
   it is honored verbatim.
2. **OpenTofu on PATH.** If `tofu` is on PATH, the helper exports
   `DATABRICKS_TF_EXEC_PATH=$(command -v tofu)` and (when unset)
   `DATABRICKS_TF_VERSION=1.11.6`.
3. **System terraform on PATH.** If only `terraform` is available, the
   helper exports `DATABRICKS_TF_EXEC_PATH=$(command -v terraform)` and
   leaves `DATABRICKS_TF_VERSION` to the CLI's default handling.
4. **Neither available.** The Make target fails fast — before the
   `databricks` command runs — with a single message recommending
   `brew install opentofu`.

The same precedence is applied inside the `driftsentinel` Python package
(`src/driftsentinel/databricks/tf_env.py`) so direct CLI calls
(`uv run driftsentinel databricks connect …`) and the app deploy script
(`scripts/deploy_databricks_app.py`) work the same way.

**Manual override.** Operators with a non-Homebrew binary or an alternate
version can export the env vars before calling Make or running raw
`databricks bundle …` commands:

```bash
export DATABRICKS_TF_EXEC_PATH=/path/to/tofu-or-terraform
export DATABRICKS_TF_VERSION=1.11.6     # optional
```

See `specs/DS-PATCH-035_opentofu_auto_detection.md` for the full design
context, including non-goals (this is a shim; the upstream Databricks
CLI pin is not changed) and the tested precedence contract.

## Option 1: Databricks Asset Bundle Deploy

The recommended deployment path uses Databricks Asset Bundles. The bundle
defines a shared runtime volume, fail-closed intake/drift/benchmark jobs, a
full dataset pipeline job, and the Databricks App.

### Verify Catalog Access

```bash
make bundle-catalog-check CATALOG=my_catalog PROFILE=<profile>
```

Direct CLI equivalent:

```bash
databricks catalogs get my_catalog -p <profile>
```

Expected result: the CLI returns catalog metadata for the exact catalog you
plan to pass into the bundle.

### Validate

```bash
git clone https://github.com/Org-EthereaLogic/DriftSentinel.git
cd DriftSentinel

make bundle-validate CATALOG=my_catalog PROFILE=<profile>
```

Direct CLI equivalent:

```bash
databricks bundle validate -p <profile> --target dev --var="catalog=my_catalog"
```

Expected result: `Validation OK!`. This confirms bundle/auth/resource
resolution only. It does not replace the catalog check above, and it does not
prove deploy, job execution, or Databricks App source deployment.

### Deploy

```bash
# Deploy to the dev target (default)
databricks bundle deploy -p <profile> --target dev --var="catalog=my_catalog"

# Deploy to production
databricks bundle deploy -p <profile> --target prod --var="catalog=my_catalog,schema=my_schema"
```

`databricks bundle deploy` creates or updates the Databricks resources in the
bundle, including the app resource definition. It does not by itself create a
Databricks App deployment from the uploaded source code.

### Default Workspace Sync Exclusions

`databricks.yml` ships a `sync.exclude` block that keeps local-only artifacts
out of the workspace bundle path on every deploy:

| Pattern | Reason |
| --- | --- |
| `data/` | Local dataset staging; files routinely exceed the 52428800-byte (50 MB) workspace per-file ceiling |
| `evidence_pulled/`, `archive_exports/`, `orphaned_state_backup/` | Operator-side dumps; canonical evidence lives in the runtime volume |
| `report/` | Local development surface; production evidence is written to the Unity Catalog runtime volume |
| `.venv/` | Local virtualenv |
| `**/__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/` | Tool caches |

Without these exclusions, `databricks bundle deploy` (and `databricks apps
deploy` downstream) fails with `File ... is larger than the maximum allowed
file size of 52428800 bytes` whenever a local `data/` directory contains a
file above the ceiling.

If you stage other large or sensitive local files outside these paths, add
them under `sync.exclude` in `databricks.yml`. See
`specs/DS-PATCH-034_bundle_sync_exclude_defaults.md` for the canonical
exclusion contract.

### Run (CLI — recommended)

The Make wrapper and DriftSentinel CLI handle bundle deploy, file upload, and
job execution in one dataset-backed command:

```bash
# Fresh clone / first dataset-backed bootstrap
make bootstrap CATALOG=my_catalog PROFILE=<profile> \
  DATASET_ID=my_dataset \
  REGISTRY=/path/to/registry.json \
  DRIFT_POLICY=/path/to/drift_policy.yml \
  LANDING_PATH=/path/to/current_data \
  BASELINE_PATH=/path/to/baseline_data
```

`make bootstrap` wraps `uv run driftsentinel databricks connect`, so
`DATASET_ID` and a local `DRIFT_POLICY` are always required. `REGISTRY`,
`LANDING_PATH`, and `BASELINE_PATH` are needed when the shared runtime volume
does not already contain the registry and dataset files. Add
`BENCHMARK_POLICY=/path/to/benchmark_policy.yml` when the benchmark stage
needs a custom policy upload.

Direct CLI form:

```bash
# First run from a fresh clone — bootstrap everything
uv run driftsentinel databricks connect \
  --catalog my_catalog \
  --dataset-id my_dataset \
  --registry /path/to/registry.json \
  --drift-policy /path/to/drift_policy.yml \
  --benchmark-policy /path/to/benchmark_policy.yml \
  --landing-path /path/to/current_data \
  --baseline-path /path/to/baseline_data \
  --wait

# Repeat run for an already-registered dataset
uv run driftsentinel databricks run \
  --catalog my_catalog \
  --dataset-id my_dataset \
  --wait
```

Additional CLI commands:

```bash
# Upload or refresh files without running
uv run driftsentinel databricks sync \
  --catalog my_catalog --dataset-id my_dataset --registry /path/to/registry.json

# Print app URL, job IDs, and runtime volume path
uv run driftsentinel databricks status --catalog my_catalog

# Verify auth, catalog, bundle, volume, and resource IDs
uv run driftsentinel databricks doctor --catalog my_catalog
```

### Run (raw bundle fallback)

Runtime inputs (`dataset_id`, policy paths, `seed`, `n_rows`) are Databricks
job parameters, not bundle variables. Pass them with `--params`:

The `n_rows` parameter defaults to `10000` in the bundle resources (raised
from `1000` in DS-PATCH-037). Lower values are statistically noisy on the
quality recall gate; see
`specs/DS-PATCH-037_benchmark_n_rows_default.md`.

```bash
databricks bundle run dataset_pipeline_job -p <profile> --target dev \
  --var="catalog=my_catalog" \
  --params '{"dataset_id":"my_dataset","registry_path":"/Volumes/my_catalog/default/driftsentinel_runtime/state/registry.json","drift_policy_path":"/Volumes/my_catalog/default/driftsentinel_runtime/policies/drift_policy.yml","evidence_dir":"/Volumes/my_catalog/default/driftsentinel_runtime/evidence"}'
```

These jobs fail closed. If `dataset_id` or the required policy paths are
blank, the jobs error instead of silently switching to demo or synthetic
execution.

### Bundle Variables

Bundle variables are deploy-time only. Runtime inputs are now job parameters
passed at run time via the CLI or `--params`.

| Variable | Description | Default |
| --- | --- | --- |
| `catalog` | Existing Unity Catalog catalog name | Required |
| `schema` | Unity Catalog schema name | `default` |
| `runtime_volume_name` | Shared Unity Catalog volume for registry and evidence state | `driftsentinel_runtime` |

Override at deploy time:

```bash
databricks bundle deploy -p <profile> --var="catalog=my_catalog,schema=my_schema,runtime_volume_name=my_runtime_volume"
```

## Option 2: Direct Notebook Import with pip Install

If you prefer to run notebooks directly without the bundle CLI, each notebook
prefers the bundle-synced workspace source tree when present and otherwise
installs DriftSentinel from GitHub on first run.

1. Clone or download the repository.
2. Import the `notebooks/` directory into your Databricks workspace.
3. Optionally import the `templates/` directory to a workspace volume if you
   want to customize dataset or benchmark YAML files.
4. Open `00_quickstart_setup.py` to verify installation and run a health check.
5. Follow notebooks in order: register dataset, seed baseline, run controls.

Each notebook resolves the deployed workspace root under `/Workspace/...`,
adds the repository `src/` tree to `sys.path` when present, and falls back to
installing the GitHub repository when running standalone. No prior
installation is required on the cluster. The package includes read-only
example templates for the notebook bootstrap path, while
`01_register_dataset.py` and `05_run_control_benchmark.py` also accept
optional workspace YAML paths. For notebook widget paths backed by Databricks
Volumes, prefer `/Volumes/...` rather than `/dbfs/Volumes/...`.

## Notebook Sequence

| Order | Notebook | Purpose |
| --- | --- | --- |
| 0 | `00_quickstart_setup.py` | Install, verify, health check |
| 1 | `01_register_dataset.py` | Load and validate a dataset contract |
| 2 | `02_seed_or_import_baseline.py` | Establish a trusted drift baseline |
| 3 | `03_run_intake_controls.py` | Run intake certification controls |
| 4 | `04_run_drift_gate.py` | Measure drift and emit gate verdicts |
| 5 | `05_run_control_benchmark.py` | Run dual-track benchmark with scoring |
| 6 | `06_review_evidence.py` | Inspect evidence artifacts from prior runs |
| 7 | `07_run_dataset_pipeline.py` | Run the full dataset-backed pipeline |

## Bundle Resources

| Resource | Type | Surface |
| --- | --- | --- |
| `runtime_volume` | Volume | Shared `/Volumes/<catalog>/<schema>/<runtime_volume_name>` state |
| `intake_pipeline` | Job | `03_run_intake_controls.py` |
| `drift_gate_job` | Job | `04_run_drift_gate.py` |
| `benchmark_job` | Job | `05_run_control_benchmark.py` |
| `dataset_pipeline_job` | Job | `07_run_dataset_pipeline.py` |
| `driftsentinel_app` | App (Gradio) | `app/` |

## Databricks App

The `driftsentinel_app` resource defines a Gradio-based operator dashboard.
It provides read-only views of the dataset registry, recent control run
status, and evidence artifacts. The App requires a Premium workspace.
Bundle-backed deployments inject the shared runtime volume path into the app
environment so the dashboard reads the same registry and evidence directories as
the bundle jobs.

Deploy the app from the repository root so Databricks Apps installs the local
`driftsentinel` package from this repository and starts the app runtime:

```bash
make app-deploy CATALOG=my_catalog PROFILE=<profile>
```

`make app-deploy` wraps the reliable sequence for this repository:
`databricks bundle deploy`, `databricks bundle summary` (to resolve the app
name and the deployed `source_code_path`), an auto-generated `app.yml`
uploaded to the workspace `source_code_path`, then
`databricks apps start` and `databricks apps deploy <name> --source-code-path
<path>`, ending with a `databricks apps get` status check.

Databricks CLI `v0.295.0+` does not accept `--target` or `--var` on
`apps deploy`; the supported flags are the positional `<APP_NAME>` and
`--source-code-path <workspace_path>`. The auto-generated `app.yml` carries
the bundle resource's `command:` plus env entries resolved against the
`catalog`, `schema`, and `runtime_volume_name` bundle variables (and any
`value_from` resource references). See
`specs/DS-PATCH-038_app_deploy_source_code_path.md` for the full design and
the failure-mode contract.

Raw CLI sequence:

```bash
databricks bundle deploy -p <profile> --target dev --var="catalog=my_catalog"
databricks bundle summary -p <profile> --target dev --var="catalog=my_catalog" -o json
# inspect summary.resources.apps.driftsentinel_app.source_code_path
databricks workspace import \
  /Workspace/Users/<user>/.bundle/driftsentinel/dev/files/app.yml \
  --file ./app.yml --format AUTO --overwrite -p <profile>
databricks apps start driftsentinel -p <profile>
databricks apps deploy driftsentinel \
  --source-code-path /Workspace/Users/<user>/.bundle/driftsentinel/dev/files \
  -p <profile>
databricks apps get driftsentinel -p <profile> -o json
```

Expected result: the CLI reaches `SUCCEEDED`, and
`databricks apps get driftsentinel -p <profile> -o json` reports
`"state":"SUCCEEDED"` for the active deployment and `"state":"RUNNING"` for the
app. `databricks bundle summary` is not the proof surface for current app
runtime state.

The App reads from the same first-party package surfaces that notebooks use
(`DatasetRegistry.load()`, `list_evidence()`, `load_evidence()`). It never
writes evidence, modifies the registry, or executes controls. `bundle destroy`
removes the app resource after proof.

## Compute Requirements

- DBR 14.3 LTS or later recommended
- Python 3.11+ (included in DBR 14.3+)
- Single-node cluster sufficient for evaluation
- Unity Catalog access for the configured catalog and schema

## Evidence Path Notes

- `05_run_control_benchmark.py` writes JSON evidence bundles to the
  `evidence_dir` widget path.
- Bundle-backed jobs and the Databricks App default to
  `/Volumes/<catalog>/<schema>/<runtime_volume_name>/evidence`.
- Direct local app runs and notebook sessions can still use
  `/tmp/driftsentinel_evidence`, but that path is cluster-local and suitable
  only for a single-cluster evaluation flow.
- For evidence that must persist across job clusters or separate review
  sessions, keep the job, notebook, and app surfaces pointed at the same Unity
  Catalog volume path.
