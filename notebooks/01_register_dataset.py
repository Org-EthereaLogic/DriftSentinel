# Databricks notebook source
# MAGIC %md
# MAGIC # DriftSentinel — Register Dataset
# MAGIC
# MAGIC Register a new dataset for DriftSentinel monitoring by loading a dataset
# MAGIC contract from `templates/dataset_contract.yml` or providing inline config.

# COMMAND ----------

# Resolve the bundle workspace root when this notebook is deployed through
# Databricks Asset Bundles, then fall back to GitHub for manual imports.
from pathlib import Path


def _resolve_install_target() -> str:
    try:
        notebook_path = (
            dbutils.notebook.entry_point.getDbutils()
            .notebook()
            .getContext()
            .notebookPath()
            .get()
        )
        workspace_path = Path("/Workspace") / notebook_path.lstrip("/")
        for parent in workspace_path.parents:
            if (parent / "pyproject.toml").exists() and (parent / "src" / "driftsentinel").exists():
                return str(parent)
    except Exception:
        pass
    return "git+https://github.com/Org-EthereaLogic/DriftSentinel.git"


install_target = _resolve_install_target()
with open("/tmp/driftsentinel-bootstrap.txt", "w", encoding="utf-8") as fh:
    fh.write(f"{install_target}\n")
print(f"Installing DriftSentinel from: {install_target}")

# COMMAND ----------

# MAGIC %pip install -r /tmp/driftsentinel-bootstrap.txt
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

dbutils.widgets.text("catalog", "", "Unity Catalog name")
dbutils.widgets.text("schema", "default", "Schema name")
dbutils.widgets.text("contract_path", "", "Optional workspace path to dataset contract YAML")

# COMMAND ----------

catalog = dbutils.widgets.get("catalog").strip()
schema = dbutils.widgets.get("schema").strip()
contract_path = dbutils.widgets.get("contract_path").strip()
if not catalog:
    raise ValueError("Set the catalog widget to an existing Unity Catalog catalog before running this notebook.")
if not schema:
    raise ValueError("Set the schema widget to an existing schema before running this notebook.")
print(f"Target: {catalog}.{schema}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load and Validate a Dataset Contract Template

# COMMAND ----------

import json
from driftsentinel.config.loader import load_dataset_contract, load_packaged_dataset_contract

if contract_path:
    contract = load_dataset_contract(contract_path)
    contract_source = contract_path
else:
    contract = load_packaged_dataset_contract()
    contract["dataset"]["catalog"] = catalog
    contract["dataset"]["schema"] = schema
    contract_source = "bundled package template"

print(f"Dataset contract loaded successfully from {contract_source}.")
print(json.dumps(contract, indent=2))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Contract Summary

# COMMAND ----------

ds = contract["dataset"]
ct = contract["contract"]
print(f"Dataset:          {ds['name']}")
print(f"Catalog:          {ds.get('catalog', catalog)}")
print(f"Schema:           {ds.get('schema', schema)}")
print(f"Required columns: {len(ct['required_columns'])}")
print(f"Business key:     {ct['business_key']}")
print(f"Batch identifier: {ct['batch_identifier']}")
