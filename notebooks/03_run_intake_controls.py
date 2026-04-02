# Databricks notebook source
# MAGIC %md
# MAGIC # DriftSentinel — Run Intake Controls
# MAGIC
# MAGIC Execute intake certification: schema drift detection, duplicate replay
# MAGIC blocking, contract validation, and quarantine routing.

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
# MAGIC ## Run Intake Demo

# COMMAND ----------

import json
from driftsentinel.orchestration.runner import run_intake_demo

result = run_intake_demo()
print(json.dumps(result, indent=2))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary

# COMMAND ----------

print(f"Total rows:    {result['total_rows']}")
print(f"Ready:         {result['ready']}")
print(f"Quarantined:   {result['quarantined']}")
print(f"Violations:    {result['violations']}")

if result["quarantined"] > 0:
    print(f"\nQuarantine rate: {result['quarantined'] / result['total_rows']:.1%}")
