# Databricks notebook source
# MAGIC %md
# MAGIC # DriftSentinel — Run Drift Gate
# MAGIC
# MAGIC Measure distribution stability against the stored baseline and emit
# MAGIC explicit gate verdicts before Gold publication.

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
# MAGIC ## Run Drift Gate Demo

# COMMAND ----------

import json
from driftsentinel.orchestration.runner import run_drift_demo

result = run_drift_demo()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Provenance Envelope

# COMMAND ----------

print(json.dumps(result["provenance"], indent=2, default=str))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gate Results

# COMMAND ----------

print(f"Health score:      {result['health_score']}")
print(f"Columns drifted:   {result['columns_drifted']}")
print(f"Overall verdict:   {result['overall_verdict']}")

for gate in result["provenance"]["gate_results"]:
    print(f"  {gate['name']}: measured={gate['measured']}, verdict={gate['verdict']}")
