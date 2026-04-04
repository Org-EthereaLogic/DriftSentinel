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
dbutils.widgets.text("dataset_id", "", "Optional dataset ID from registry")
dbutils.widgets.text("registry_path", "/tmp/driftsentinel_registry.json", "Dataset registry JSON path")
dbutils.widgets.text("drift_policy_path", "", "Optional workspace path to drift policy YAML")
dbutils.widgets.text("evidence_dir", "/tmp/driftsentinel_evidence", "Directory for evidence artifacts")

# COMMAND ----------

catalog = dbutils.widgets.get("catalog").strip()
schema = dbutils.widgets.get("schema").strip()
dataset_id = dbutils.widgets.get("dataset_id").strip()
registry_path = dbutils.widgets.get("registry_path").strip()
drift_policy_path = dbutils.widgets.get("drift_policy_path").strip()
evidence_dir = dbutils.widgets.get("evidence_dir").strip()
if not catalog:
    raise ValueError("Set the catalog widget to an existing Unity Catalog catalog before running this notebook.")
if not schema:
    raise ValueError("Set the schema widget to an existing schema before running this notebook.")
print(f"Target: {catalog}.{schema}")
if dataset_id:
    print(f"Dataset: {dataset_id}")

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


os.environ["REGISTRY_PATH"] = registry_path
os.environ["EVIDENCE_DIR"] = evidence_dir
_configure_trusted_roots(registry_path, drift_policy_path, evidence_dir)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Run Drift Gate

# COMMAND ----------

import json
from driftsentinel.config.loader import DatasetRegistry, check_policy_compatibility, load_drift_policy
from driftsentinel.evidence.writer import generate_run_id
from driftsentinel.orchestration.runner import run_dataset_drift, run_drift_demo

if dataset_id:
    if not drift_policy_path:
        raise ValueError("Set drift_policy_path when running drift for a registered dataset.")
    registry = DatasetRegistry.load(registry_path)
    contract = registry.get(dataset_id)
    drift_policy = load_drift_policy(drift_policy_path)
    binding = check_policy_compatibility(registry, drift_policy["drift_policy"], "Drift policy")
    run_id = generate_run_id()
    result = run_dataset_drift(
        contract,
        drift_policy,
        evidence_dir=evidence_dir,
        dataset_id=dataset_id,
        contract_version=contract["dataset"].get("contract_version"),
        policy_version=binding["policy_version"],
        run_id=run_id,
    )
    print(f"Dataset-backed drift completed for dataset={dataset_id}, run_id={run_id}")
else:
    result = run_drift_demo()
    print("Demo drift completed. Set dataset_id + registry_path + drift_policy_path to run against real data.")

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
