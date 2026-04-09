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
import subprocess
import sys


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
if install_target.startswith("/Workspace/"):
    source_root = str(Path(install_target) / "src")
    if source_root not in sys.path:
        sys.path.insert(0, source_root)
    print(f"Using DriftSentinel from workspace source tree: {source_root}")
else:
    print(f"Installing DriftSentinel from: {install_target}")
    subprocess.check_call([sys.executable, "-m", "pip", "install", install_target])
    dbutils.library.restartPython()

# COMMAND ----------

# Installation is handled in the previous cell so serverless runs do not rely on writing a temp file.

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

import os


def _configure_trusted_roots(*raw_paths: str) -> None:
    roots = {"/Workspace", "/Volumes", "/dbfs"}
    for raw in raw_paths:
        raw = str(raw or "").strip()
        if not raw:
            continue
        candidate = Path(raw.replace("dbfs:/", "/dbfs/", 1)).expanduser()
        if candidate.is_absolute():
            roots.add(str(candidate.parent if candidate.suffix else candidate))
    existing = {
        item for item in os.environ.get("DRIFTSENTINEL_ALLOWED_PATH_ROOTS", "").split(os.pathsep) if item
    }
    os.environ["DRIFTSENTINEL_ALLOWED_PATH_ROOTS"] = os.pathsep.join(sorted(existing | roots))


_configure_trusted_roots(contract_path, drift_policy_path)

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
    monitored_specs = [
        (item["column_name"], item["method"])
        for item in drift_policy["drift_policy"].get("monitored_columns", [])
        if item.get("column_name") and item.get("method")
    ]
    monitored_columns = [column_name for column_name, _ in monitored_specs] or MONITORED_COLUMNS
    monitored_methods = {column_name: method for column_name, method in monitored_specs}
    print(f"Imported trusted baseline from: {loaded.source_path}")
    print(f"Files loaded:        {len(loaded.files_loaded)}")
else:
    baseline_rows = generate_baseline()
    baseline_df = pd.DataFrame(baseline_rows)
    monitored_columns = MONITORED_COLUMNS
    monitored_methods = {column_name: "shannon_entropy" for column_name in monitored_columns}
    print("Using bundled demo baseline. Set contract_path + drift_policy_path to inspect a real baseline.")

print(f"Baseline rows:       {len(baseline_df)}")
print(f"Monitored columns:   {monitored_columns}")
print(f"All columns:         {list(baseline_df.columns)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Baseline Snapshot Summary

# COMMAND ----------

from driftsentinel.drift.baseline import BaselineSnapshot

snapshot = BaselineSnapshot.from_dataframe(
    baseline_df,
    monitored_columns,
    methods=monitored_methods,
)
print(f"Row count:           {snapshot.row_count}")
print(f"Columns tracked:     {list(snapshot.columns)}")
for col in snapshot.columns:
    print(
        f"  {col}: method={snapshot.methods[col].value}, "
        f"stability_score={round(snapshot.scores.get(col, 0.0), 4)}"
    )
