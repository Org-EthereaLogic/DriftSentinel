# Databricks notebook source
# MAGIC %md
# MAGIC # DriftSentinel — Seed or Import Baseline
# MAGIC
# MAGIC Establish a trusted baseline for drift monitoring by seeding from the demo
# MAGIC dataset or importing from a user-supplied trusted load.

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
dbutils.widgets.text("drift_policy_path", "", "Optional workspace path to drift policy YAML")

# COMMAND ----------

catalog = dbutils.widgets.get("catalog").strip()
schema = dbutils.widgets.get("schema").strip()
contract_path = dbutils.widgets.get("contract_path").strip()
drift_policy_path = dbutils.widgets.get("drift_policy_path").strip()
if not catalog:
    raise ValueError("Set the catalog widget to an existing Unity Catalog catalog before running this notebook.")
if not schema:
    raise ValueError("Set the schema widget to an existing schema before running this notebook.")
print(f"Target: {catalog}.{schema}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Generate Sample Baseline

# COMMAND ----------

import pandas as pd
from driftsentinel.config.loader import load_dataset_contract, load_drift_policy
from driftsentinel.drift.sample_data import MONITORED_COLUMNS, generate_baseline
from driftsentinel.orchestration.dataset_runtime import load_baseline_dataset

if contract_path and drift_policy_path:
    contract = load_dataset_contract(contract_path)
    drift_policy = load_drift_policy(drift_policy_path)
    loaded = load_baseline_dataset(contract, drift_policy)
    baseline_df = loaded.frame
    monitored_columns = [
        item["column_name"]
        for item in drift_policy["drift_policy"].get("monitored_columns", [])
        if item.get("column_name")
    ] or MONITORED_COLUMNS
    print(f"Imported trusted baseline from: {loaded.source_path}")
    print(f"Files loaded:        {len(loaded.files_loaded)}")
else:
    baseline_rows = generate_baseline()
    baseline_df = pd.DataFrame(baseline_rows)
    monitored_columns = MONITORED_COLUMNS
    print("Using bundled demo baseline. Set contract_path + drift_policy_path to inspect a real baseline.")

print(f"Baseline rows:       {len(baseline_df)}")
print(f"Monitored columns:   {monitored_columns}")
print(f"All columns:         {list(baseline_df.columns)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Baseline Snapshot Summary

# COMMAND ----------

from driftsentinel.drift.baseline import BaselineSnapshot

snapshot = BaselineSnapshot.from_dataframe(baseline_df, monitored_columns)
print(f"Row count:           {snapshot.row_count}")
print(f"Columns tracked:     {list(snapshot.columns)}")
for col in snapshot.columns:
    print(f"  {col}: stability_score={round(snapshot.scores.get(col, 0.0), 4)}")
