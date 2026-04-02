# Databricks notebook source
# MAGIC %md
# MAGIC # DriftSentinel — Run Drift Gate
# MAGIC
# MAGIC Measure distribution stability against the stored baseline and emit
# MAGIC explicit gate verdicts before Gold publication.

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
dbutils.widgets.text("evidence_dir", "/tmp/driftsentinel_evidence", "Directory for evidence artifacts")

# COMMAND ----------

catalog = dbutils.widgets.get("catalog").strip()
schema = dbutils.widgets.get("schema").strip()
dataset_id = dbutils.widgets.get("dataset_id").strip()
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
# MAGIC ## Run Drift Gate

# COMMAND ----------

import json
from driftsentinel.orchestration.runner import run_drift_demo
from driftsentinel.evidence.writer import generate_run_id, write_evidence

result = run_drift_demo()

if dataset_id and evidence_dir:
    run_id = generate_run_id()
    write_evidence(
        evidence_dir,
        f"drift_{dataset_id}.json",
        result["provenance"],
        dataset_id=dataset_id,
        run_id=run_id,
        run_kind="drift",
    )
    print(f"Evidence written for dataset={dataset_id}, run_id={run_id}")

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
