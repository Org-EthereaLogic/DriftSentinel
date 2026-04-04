# DriftSentinel Deployment Guide

## Prerequisites

- Databricks workspace with Unity Catalog enabled
- An existing Unity Catalog catalog and schema for DriftSentinel tables
  (for example `adb_dev.default`)
- Compute cluster with Python 3.11+
- Databricks CLI installed and authenticated through `.databrickscfg`,
  `DATABRICKS_CONFIG_PROFILE`, or `DATABRICKS_*` environment variables

## Option 1: Databricks Asset Bundle Deploy

The recommended deployment path uses Databricks Asset Bundles. The bundle
defines an intake pipeline, drift gate job, and benchmark job.

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

### Run

```bash
# Run the intake pipeline
databricks bundle run intake_pipeline -p <profile> --target dev --var="catalog=my_catalog"

# Run the drift gate job
databricks bundle run drift_gate_job -p <profile> --target dev --var="catalog=my_catalog"

# Run the benchmark job
databricks bundle run benchmark_job -p <profile> --target dev --var="catalog=my_catalog"
```

### Bundle Variables

| Variable | Description | Default |
| --- | --- | --- |
| `catalog` | Existing Unity Catalog catalog name | Required |
| `schema` | Unity Catalog schema name | `default` |

Override at deploy time:

```bash
databricks bundle deploy -p <profile> --var="catalog=my_catalog,schema=my_schema"
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

## Bundle Resources

| Resource | Type | Surface |
| --- | --- | --- |
| `intake_pipeline` | Pipeline (DLT) | `03_run_intake_controls.py` |
| `drift_gate_job` | Job | `04_run_drift_gate.py` |
| `benchmark_job` | Job | `05_run_control_benchmark.py` |
| `driftsentinel_app` | App (Gradio) | `app/` |

## Databricks App

The `driftsentinel_app` resource defines a Gradio-based operator dashboard.
It provides read-only views of the dataset registry, recent control run
status, and evidence artifacts. The App requires a Premium workspace.

Deploy the app from the repository root so Databricks Apps installs the local
`driftsentinel` package from this repository and starts the app runtime:

```bash
make app-deploy CATALOG=my_catalog PROFILE=<profile>
```

`make app-deploy` wraps the reliable sequence for this repository:
`databricks bundle deploy`, `databricks apps start`, `databricks apps deploy`,
and a final `databricks apps get` status check.

Raw CLI sequence:

```bash
databricks bundle deploy -p <profile> --target dev --var="catalog=my_catalog"
databricks apps start driftsentinel -p <profile>
databricks apps deploy -p <profile> --target dev --var="catalog=my_catalog"
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
- The default `/tmp/driftsentinel_evidence` path is cluster-local and suitable
  for a single-cluster evaluation flow.
- For evidence that must persist across job clusters or separate review
  sessions, point `evidence_dir` at a Unity Catalog volume path.
