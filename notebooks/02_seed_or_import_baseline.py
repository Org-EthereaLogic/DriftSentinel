# Databricks notebook source
# MAGIC %md
# MAGIC # DriftSentinel — Seed or Import Baseline
# MAGIC
# MAGIC Establish a trusted baseline for drift monitoring by seeding from the demo
# MAGIC dataset or importing from a user-supplied trusted load.

# COMMAND ----------

# MAGIC %pip install git+https://github.com/Org-EthereaLogic/DriftSentinel.git
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

dbutils.widgets.text("catalog", "driftsentinel", "Unity Catalog name")
dbutils.widgets.text("schema", "default", "Schema name")

# COMMAND ----------

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
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
