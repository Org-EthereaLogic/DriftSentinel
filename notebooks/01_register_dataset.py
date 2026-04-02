# Databricks notebook source
# MAGIC %md
# MAGIC # DriftSentinel — Register Dataset
# MAGIC
# MAGIC Register a new dataset for DriftSentinel monitoring by loading a dataset
# MAGIC contract from `templates/dataset_contract.yml` or providing inline config.

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
# MAGIC ## Load and Validate a Dataset Contract Template

# COMMAND ----------

import json
from driftsentinel.config.loader import load_dataset_contract

# Load the template contract bundled with DriftSentinel
import driftsentinel
from pathlib import Path

pkg_root = Path(driftsentinel.__file__).resolve().parent.parent.parent
template_path = pkg_root / "templates" / "dataset_contract.yml"

contract = load_dataset_contract(template_path)
print("Dataset contract loaded successfully.")
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
