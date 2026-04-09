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
dbutils.widgets.text("registry_path", "", "Optional registry JSON path (blank uses shared runtime volume)")
dbutils.widgets.text("evidence_dir", "", "Optional evidence directory (blank uses shared runtime volume)")
dbutils.widgets.dropdown("require_dataset_backed", "false", ["false", "true"], "Disable demo fallback")

# COMMAND ----------

catalog = dbutils.widgets.get("catalog").strip()
schema = dbutils.widgets.get("schema").strip()
dataset_id = dbutils.widgets.get("dataset_id").strip()
registry_path = dbutils.widgets.get("registry_path").strip()
evidence_dir = dbutils.widgets.get("evidence_dir").strip()
require_dataset_backed = dbutils.widgets.get("require_dataset_backed").strip().lower() == "true"
if not catalog:
    raise ValueError("Set the catalog widget to an existing Unity Catalog catalog before running this notebook.")
if not schema:
    raise ValueError("Set the schema widget to an existing schema before running this notebook.")
print(f"Target: {catalog}.{schema}")
if dataset_id:
    print(f"Dataset: {dataset_id}")

# COMMAND ----------

from driftsentinel.runtime_paths import runtime_evidence_dir, runtime_registry_path, runtime_volume_root

runtime_root = runtime_volume_root(catalog, schema)
if not registry_path:
    registry_path = runtime_registry_path(catalog, schema)
    print(f"Using default shared registry path: {registry_path}")
else:
    print(f"Using custom registry path: {registry_path}")
if not evidence_dir:
    evidence_dir = runtime_evidence_dir(catalog, schema)
    print(f"Using default shared evidence directory: {evidence_dir}")
else:
    print(f"Using custom evidence directory: {evidence_dir}")
print(f"Runtime volume root: {runtime_root}")

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
_configure_trusted_roots(registry_path, evidence_dir)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Run Intake Controls

# COMMAND ----------

import json
from driftsentinel.config.loader import DatasetRegistry
from driftsentinel.evidence.writer import generate_run_id
from driftsentinel.orchestration.runner import run_dataset_intake, run_intake_demo

if require_dataset_backed and not dataset_id:
    raise ValueError(
        "This execution surface requires dataset-backed mode. "
        "Set dataset_id (and registry_path if you are not using the shared runtime volume)."
    )

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
