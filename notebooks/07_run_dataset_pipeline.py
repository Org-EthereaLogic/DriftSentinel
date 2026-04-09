# Databricks notebook source
# MAGIC %md
# MAGIC # DriftSentinel — Run Dataset Pipeline
# MAGIC
# MAGIC Execute intake, drift, and benchmark controls in sequence for one
# MAGIC registered dataset using real registered inputs and a trusted baseline.

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
    except Exception as exc:
        print(f"Could not resolve workspace install target; falling back to GitHub package ({exc}).")
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
dbutils.widgets.text("dataset_id", "", "Dataset ID from registry")
dbutils.widgets.text("registry_path", "", "Optional registry JSON path (blank uses shared runtime volume)")
dbutils.widgets.text("drift_policy_path", "", "Workspace path to drift policy YAML")
dbutils.widgets.text("policy_path", "", "Optional workspace path to benchmark policy YAML")
dbutils.widgets.text("evidence_dir", "", "Optional evidence directory (blank uses shared runtime volume)")
dbutils.widgets.text("seed", "42", "Random seed for reproducibility")
dbutils.widgets.text("n_rows", "1000", "Reference sample size for benchmark")

# COMMAND ----------

catalog = dbutils.widgets.get("catalog").strip()
schema = dbutils.widgets.get("schema").strip()
dataset_id = dbutils.widgets.get("dataset_id").strip()
registry_path = dbutils.widgets.get("registry_path").strip()
drift_policy_path = dbutils.widgets.get("drift_policy_path").strip()
policy_path = dbutils.widgets.get("policy_path").strip()
evidence_dir = dbutils.widgets.get("evidence_dir").strip()
seed = int(dbutils.widgets.get("seed"))
n_rows = int(dbutils.widgets.get("n_rows"))
if not catalog:
    raise ValueError("Set the catalog widget to an existing Unity Catalog catalog before running this notebook.")
if not schema:
    raise ValueError("Set the schema widget to an existing schema before running this notebook.")
if not dataset_id:
    raise ValueError("Set dataset_id to a registered dataset before running the pipeline.")
if not drift_policy_path:
    raise ValueError("Set drift_policy_path to a dataset-compatible drift policy before running the pipeline.")
print(f"Target: {catalog}.{schema}")
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
_configure_trusted_roots(registry_path, drift_policy_path, policy_path, evidence_dir)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Run Dataset Pipeline

# COMMAND ----------

import json
from driftsentinel.config.loader import DatasetRegistry, load_benchmark_policy, load_drift_policy
from driftsentinel.evidence.writer import generate_run_id
from driftsentinel.orchestration.runner import run_dataset_pipeline

registry = DatasetRegistry.load(registry_path)
drift_policy = load_drift_policy(drift_policy_path)
benchmark_policy = load_benchmark_policy(policy_path) if policy_path else None
run_id = generate_run_id()

result = run_dataset_pipeline(
    registry,
    dataset_id,
    evidence_dir=evidence_dir,
    drift_policy=drift_policy,
    benchmark_policy=benchmark_policy,
    seed=seed,
    n_rows=n_rows,
    run_id=run_id,
)

print(f"Dataset pipeline completed for dataset={dataset_id}, run_id={run_id}")
print(json.dumps(result, indent=2, default=str))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Stage Summary

# COMMAND ----------

print(f"Overall verdict: {result['overall_verdict']}")
print(f"Current source:  {result['current_source']['path']}")
print(f"Baseline source: {result['baseline_source']['path']}")
print(f"Pipeline artifact: {result.get('evidence_path', '(not written)')}")
for stage in ["intake", "drift", "benchmark"]:
    stage_result = result.get(stage, {})
    print(f"  {stage}: {stage_result.get('overall_verdict', '(no verdict)')}")
