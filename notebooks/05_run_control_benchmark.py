# Databricks notebook source
# MAGIC %md
# MAGIC # DriftSentinel — Run Control Benchmark
# MAGIC
# MAGIC Run control effectiveness benchmarking against known failure scenarios
# MAGIC and write scored evidence bundles.

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

dbutils.widgets.text("seed", "42", "Random seed for reproducibility")
dbutils.widgets.text("n_rows", "1000", "Benchmark sample size")
dbutils.widgets.text("catalog", "", "Unity Catalog name")
dbutils.widgets.text("schema", "default", "Schema name")
dbutils.widgets.text("dataset_id", "", "Optional dataset ID from registry")
dbutils.widgets.text("registry_path", "", "Optional registry JSON path (blank uses shared runtime volume)")
dbutils.widgets.text("drift_policy_path", "", "Optional workspace path to drift policy YAML")
dbutils.widgets.text("policy_path", "", "Optional workspace path to benchmark policy YAML")
dbutils.widgets.text("evidence_dir", "", "Optional evidence directory (blank uses shared runtime volume)")
dbutils.widgets.dropdown("require_dataset_backed", "false", ["false", "true"], "Disable synthetic fallback")

# COMMAND ----------

seed = int(dbutils.widgets.get("seed"))
n_rows = int(dbutils.widgets.get("n_rows"))
catalog = dbutils.widgets.get("catalog").strip()
schema = dbutils.widgets.get("schema").strip()
dataset_id = dbutils.widgets.get("dataset_id").strip()
registry_path = dbutils.widgets.get("registry_path").strip()
drift_policy_path = dbutils.widgets.get("drift_policy_path").strip()
policy_path = dbutils.widgets.get("policy_path").strip()
evidence_dir = dbutils.widgets.get("evidence_dir").strip()
require_dataset_backed = dbutils.widgets.get("require_dataset_backed").strip().lower() == "true"
if not catalog:
    raise ValueError("Set the catalog widget to an existing Unity Catalog catalog before running this notebook.")
if not schema:
    raise ValueError("Set the schema widget to an existing schema before running this notebook.")
print(f"Benchmark config: seed={seed}, n_rows={n_rows}, target={catalog}.{schema}")
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
_configure_trusted_roots(registry_path, drift_policy_path, policy_path, evidence_dir)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Run Benchmark

# COMMAND ----------

from driftsentinel.benchmark.orchestrator import run_benchmark
from driftsentinel.config.loader import (
    DatasetRegistry,
    check_policy_compatibility,
    load_benchmark_policy,
    load_drift_policy,
)
from driftsentinel.evidence.writer import generate_run_id
from driftsentinel.orchestration.runner import run_dataset_benchmark

if require_dataset_backed and (not dataset_id or not drift_policy_path):
    raise ValueError(
        "This execution surface requires dataset-backed benchmark mode. "
        "Set dataset_id and drift_policy_path before running the job."
    )

if dataset_id:
    if not drift_policy_path:
        raise ValueError("Set drift_policy_path when running a dataset-backed benchmark.")
    registry = DatasetRegistry.load(registry_path)
    contract = registry.get(dataset_id)
    drift_policy = load_drift_policy(drift_policy_path)
    check_policy_compatibility(registry, drift_policy["drift_policy"], "Drift policy")
    benchmark_policy = load_benchmark_policy(policy_path) if policy_path else None
    policy_version = None
    if benchmark_policy is not None:
        binding = check_policy_compatibility(registry, benchmark_policy["benchmark_policy"], "Benchmark policy")
        policy_version = binding["policy_version"]
    result = run_dataset_benchmark(
        contract,
        drift_policy,
        benchmark_policy,
        evidence_dir=evidence_dir,
        seed=seed,
        n_rows=n_rows,
        dataset_id=dataset_id,
        contract_version=contract["dataset"].get("contract_version"),
        policy_version=policy_version,
        run_id=generate_run_id(),
    )
    print("Dataset-backed benchmark completed from trusted baseline reference data.")
else:
    result = run_benchmark(
        seed=seed,
        n_rows=n_rows,
        evidence_dir=evidence_dir,
        policy_path=policy_path or None,
    )
    print("Synthetic benchmark completed. Set dataset_id + registry_path + drift_policy_path for real-data mode.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Measured Metrics

# COMMAND ----------

print("Measured metrics:")
metric_rows = [
    {"metric": "quality_recall", "value": float(result["measured"]["quality_recall"])},
    {"metric": "quality_precision", "value": float(result["measured"]["quality_precision"])},
    {"metric": "quality_f1", "value": float(result["measured"]["quality_f1"])},
    {"metric": "quality_fpr", "value": float(result["measured"]["quality_fpr"])},
    {
        "metric": "challenger_beats_baseline_quality",
        "value": float(result["measured"]["challenger_beats_baseline_quality"]),
    },
    {"metric": "sudden_drift_sensitivity", "value": float(result["measured"]["sudden_drift_sensitivity"])},
    {"metric": "gradual_drift_sensitivity", "value": float(result["measured"]["gradual_drift_sensitivity"])},
    {"metric": "drift_fpr", "value": float(result["measured"]["drift_fpr"])},
    {"metric": "new_category_sensitivity", "value": float(result["measured"]["new_category_sensitivity"])},
    {
        "metric": "challenger_beats_baseline_drift",
        "value": float(result["measured"]["challenger_beats_baseline_drift"]),
    },
]
display(metric_rows)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gate Results

# COMMAND ----------

for gr in result["gate_results"]:
    if hasattr(gr, "config"):
        print(f"  {gr.config.name}: threshold={gr.config.threshold}, "
              f"measured={gr.measured_value:.4f}, verdict={gr.verdict.value}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Overall Verdict

# COMMAND ----------

_ov = result["overall_verdict"]
_raw_verdict = _ov.value if hasattr(_ov, "value") else _ov
_VERDICT_LABELS = {"PASS": "PASS", "FAIL": "FAIL", "WARN": "WARN", "UNKNOWN": "UNKNOWN"}
verdict = _VERDICT_LABELS.get(str(_raw_verdict).strip().upper(), "UNKNOWN")
print("Overall verdict: " + verdict)
if result["evidence_path"] is None:
    print("Evidence artifact was not written.")
else:
    print("Evidence artifact written to the configured evidence directory.")
