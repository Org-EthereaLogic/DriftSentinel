# DriftSentinel Deployment Guide

## Prerequisites

- Databricks workspace with Unity Catalog enabled
- A catalog and schema for DriftSentinel tables (e.g. `driftsentinel.default`)
- Compute cluster with Python 3.11+
- Databricks CLI installed and authenticated through `.databrickscfg`,
  `DATABRICKS_CONFIG_PROFILE`, or `DATABRICKS_*` environment variables

## Option 1: Databricks Asset Bundle Deploy

The recommended deployment path uses Databricks Asset Bundles. The bundle
defines an intake pipeline, drift gate job, and benchmark job.

### Validate

```bash
git clone https://github.com/Org-EthereaLogic/DriftSentinel.git
cd DriftSentinel

databricks bundle validate
```

### Deploy

```bash
# Deploy to the dev target (default)
databricks bundle deploy --target dev

# Deploy to production
databricks bundle deploy --target prod
```

### Run

```bash
# Run the intake pipeline
databricks bundle run intake_pipeline

# Run the drift gate job
databricks bundle run drift_gate_job

# Run the benchmark job
databricks bundle run benchmark_job
```

### Bundle Variables

| Variable | Description | Default |
| --- | --- | --- |
| `catalog` | Unity Catalog catalog name | `driftsentinel` |
| `schema` | Unity Catalog schema name | `default` |

Override at deploy time:

```bash
databricks bundle deploy --var="catalog=my_catalog,schema=my_schema"
```

## Option 2: Direct Notebook Import with pip Install

If you prefer to run notebooks directly without the bundle CLI, each notebook
installs DriftSentinel from GitHub on first run.

1. Clone or download the repository.
2. Import the `notebooks/` directory into your Databricks workspace.
3. Import the `templates/` directory to a workspace volume for dataset
   configuration.
4. Open `00_quickstart_setup.py` to verify installation and run a health check.
5. Follow notebooks in order: register dataset, seed baseline, run controls.

Each notebook includes a `%pip install` cell that pulls the package directly
from the GitHub repository. No prior installation is required on the cluster.

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

| Resource | Type | Notebook |
| --- | --- | --- |
| `intake_pipeline` | Pipeline (DLT) | `03_run_intake_controls.py` |
| `drift_gate_job` | Job | `04_run_drift_gate.py` |
| `benchmark_job` | Job | `05_run_control_benchmark.py` |

## Compute Requirements

- DBR 14.3 LTS or later recommended
- Python 3.11+ (included in DBR 14.3+)
- Single-node cluster sufficient for evaluation
- Unity Catalog access for the configured catalog and schema
