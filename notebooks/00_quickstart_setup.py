# Databricks notebook source
# MAGIC %md
# MAGIC # DriftSentinel — Quickstart Setup
# MAGIC
# MAGIC This notebook guides you through the initial DriftSentinel setup in your
# MAGIC Databricks workspace.
# MAGIC
# MAGIC ## Steps
# MAGIC 1. Verify workspace prerequisites (Unity Catalog, volumes)
# MAGIC 2. Install the DriftSentinel package
# MAGIC 3. Configure catalog and schema targets
# MAGIC 4. Run a health check
# MAGIC
# MAGIC ## Prerequisites
# MAGIC - Databricks workspace with Unity Catalog enabled
# MAGIC - A catalog and schema for DriftSentinel tables
# MAGIC - Compute cluster with Python 3.11+

# COMMAND ----------

# MAGIC %pip install git+https://github.com/Org-EthereaLogic/DriftSentinel.git
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

import driftsentinel
print(f"DriftSentinel version: {driftsentinel.__version__}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Module Inventory

# COMMAND ----------

import importlib
import pkgutil

modules = [mod.name for mod in pkgutil.iter_modules(driftsentinel.__path__)]
print("Installed modules:")
for name in sorted(modules):
    mod = importlib.import_module(f"driftsentinel.{name}")
    doc = (mod.__doc__ or "").strip().split("\n")[0]
    print(f"  driftsentinel.{name}: {doc}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Health Check

# COMMAND ----------

from driftsentinel.orchestration.runner import run_intake_demo

result = run_intake_demo()
print("Health check — intake demo result:")
print(f"  Total rows processed: {result['total_rows']}")
print(f"  Ready:                {result['ready']}")
print(f"  Quarantined:          {result['quarantined']}")
print(f"  Violations:           {result['violations']}")
print("\nDriftSentinel is operational.")
