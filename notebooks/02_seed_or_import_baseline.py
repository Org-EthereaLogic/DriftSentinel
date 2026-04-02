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

# COMMAND ----------

catalog = dbutils.widgets.get("catalog").strip()
schema = dbutils.widgets.get("schema").strip()
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
from driftsentinel.drift.sample_data import MONITORED_COLUMNS, generate_baseline

baseline_rows = generate_baseline()
baseline_df = pd.DataFrame(baseline_rows)
print(f"Baseline rows:       {len(baseline_df)}")
print(f"Monitored columns:   {MONITORED_COLUMNS}")
print(f"All columns:         {list(baseline_df.columns)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Baseline Snapshot Summary

# COMMAND ----------

from driftsentinel.drift.baseline import BaselineSnapshot

snapshot = BaselineSnapshot.from_dataframe(baseline_df, MONITORED_COLUMNS)
print(f"Row count:           {snapshot.row_count}")
print(f"Columns tracked:     {list(snapshot.distributions.keys())}")
for col, dist in snapshot.distributions.items():
    top_values = sorted(dist.items(), key=lambda x: x[1], reverse=True)[:3]
    top_str = ", ".join(f"{v}: {round(p, 3)}" for v, p in top_values)
    print(f"  {col}: {top_str}")
