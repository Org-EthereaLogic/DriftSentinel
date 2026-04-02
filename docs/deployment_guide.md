# DriftSentinel Deployment Guide

## Prerequisites

- Databricks workspace (Free Edition for evaluation, paid for production)
- Databricks CLI installed and configured
- Python 3.11+ with uv

## Option 1: Bundle Deployment (Recommended)

```bash
git clone https://github.com/Org-EthereaLogic/DriftSentinel.git
cd DriftSentinel
databricks bundle validate
databricks bundle deploy --target dev
```

## Option 2: Manual Workspace Import

1. Clone the repository locally.
2. Upload the `notebooks/` directory to your Databricks workspace.
3. Open `00_quickstart_setup.py` and follow the guided setup.
4. Upload `templates/` to a workspace volume for dataset configuration.

## Option 3: Databricks CLI Upload

```bash
databricks workspace import_dir notebooks/ /Users/<you>/DriftSentinel/notebooks
```

## Post-Deployment

1. Register your dataset using `01_register_dataset.py`.
2. Seed or import a baseline with `02_seed_or_import_baseline.py`.
3. Run the control pipeline with notebooks 03 through 06.
4. Review evidence with `06_review_evidence.py`.
