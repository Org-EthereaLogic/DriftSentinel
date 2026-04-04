# Databricks notebook source
# MAGIC %md
# MAGIC # DriftSentinel — Run Intake Controls
# MAGIC
# MAGIC Execute intake certification: schema drift detection, duplicate replay
# MAGIC blocking, contract validation, and quarantine routing.

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
dbutils.widgets.text("dataset_id", "", "Optional dataset ID from registry")
dbutils.widgets.text("registry_path", "/tmp/driftsentinel_registry.json", "Dataset registry JSON path")
dbutils.widgets.text("evidence_dir", "/tmp/driftsentinel_evidence", "Directory for evidence artifacts")

# COMMAND ----------

catalog = dbutils.widgets.get("catalog").strip()
schema = dbutils.widgets.get("schema").strip()
dataset_id = dbutils.widgets.get("dataset_id").strip()
registry_path = dbutils.widgets.get("registry_path").strip()
evidence_dir = dbutils.widgets.get("evidence_dir").strip()
if not catalog:
    raise ValueError("Set the catalog widget to an existing Unity Catalog catalog before running this notebook.")
if not schema:
    raise ValueError("Set the schema widget to an existing schema before running this notebook.")
print(f"Target: {catalog}.{schema}")
if dataset_id:
    print(f"Dataset: {dataset_id}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Run Intake Controls

# COMMAND ----------

import json
from driftsentinel.config.loader import DatasetRegistry
from driftsentinel.evidence.writer import generate_run_id
from driftsentinel.orchestration.runner import run_dataset_intake, run_intake_demo

if dataset_id:
    registry = DatasetRegistry.load(registry_path)
    contract = registry.get(dataset_id)
    run_id = generate_run_id()
    result = run_dataset_intake(
        contract,
        evidence_dir=evidence_dir,
        run_ts=None,
        dataset_id=dataset_id,
        contract_version=contract["dataset"].get("contract_version"),
        run_id=run_id,
    )
    print(f"Dataset-backed intake completed for dataset={dataset_id}, run_id={run_id}")
else:
    result = run_intake_demo()
    print("Demo intake completed. Set dataset_id + registry_path to run against real registered data.")

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
