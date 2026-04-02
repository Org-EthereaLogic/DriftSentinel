# DriftSentinel Deployment Guide

## Prerequisites

- Databricks workspace (Free Edition for evaluation, paid for operational
  deployment)
- Databricks CLI installed and authenticated through `.databrickscfg`,
  `DATABRICKS_CONFIG_PROFILE`, or `DATABRICKS_*` environment variables
- Python 3.11+ with uv

## Current Phase

Phase 0/1 provides a validated repository scaffold, bundle entrypoint, and
notebook/resource surfaces. It does not yet define runnable Databricks jobs or
pipelines. DS-IP-001 Phase 2 activates the operational bundle resources.

## Option 1: Validate the Bundle Scaffold

```bash
git clone https://github.com/Org-EthereaLogic/DriftSentinel.git
cd DriftSentinel

# Use your default Databricks CLI profile
databricks bundle validate

# Or select a profile explicitly
DATABRICKS_CONFIG_PROFILE=<profile> databricks bundle validate
```

## Option 2: Review Notebook Entry Points in a Workspace

1. Clone the repository locally.
2. Upload the `notebooks/` directory to your Databricks workspace.
3. Open `00_quickstart_setup.py` to review the scaffolded workflow order.
4. Upload `templates/` to a workspace volume for dataset configuration.

## Option 3: Databricks CLI Upload

```bash
databricks workspace import_dir notebooks/ /Users/<you>/DriftSentinel/notebooks
```

Running the current notebooks raises an explicit DS-IP-001 Phase 2 error. That
is expected scaffold behavior until the operational notebooks are implemented.

## Phase 2 Deployment Activation

Once DS-IP-001 Phase 2 lands and the bundle resources are implemented, the
operational deployment path becomes:

```bash
databricks bundle deploy --target dev
databricks bundle run --target dev <resource>
```
