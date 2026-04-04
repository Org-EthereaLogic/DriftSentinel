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

dbutils.widgets.text("seed", "42", "Random seed for reproducibility")
dbutils.widgets.text("n_rows", "1000", "Number of synthetic rows")
dbutils.widgets.text("catalog", "", "Unity Catalog name")
dbutils.widgets.text("schema", "default", "Schema name")
dbutils.widgets.text("dataset_id", "", "Optional dataset ID from registry")
dbutils.widgets.text("registry_path", "/tmp/driftsentinel_registry.json", "Dataset registry JSON path")
dbutils.widgets.text("drift_policy_path", "", "Optional workspace path to drift policy YAML")
dbutils.widgets.text("policy_path", "", "Optional workspace path to benchmark policy YAML")
dbutils.widgets.text("evidence_dir", "/tmp/driftsentinel_evidence", "Directory for benchmark evidence JSON")

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
if not catalog:
    raise ValueError("Set the catalog widget to an existing Unity Catalog catalog before running this notebook.")
if not schema:
    raise ValueError("Set the schema widget to an existing schema before running this notebook.")
print(f"Benchmark config: seed={seed}, n_rows={n_rows}, target={catalog}.{schema}")
if dataset_id:
    print(f"Dataset: {dataset_id}")

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

verdict = result["overall_verdict"].value if hasattr(result["overall_verdict"], "value") else result["overall_verdict"]
print(f"Overall verdict: {verdict}")
if result["evidence_path"] is None:
    print("Evidence artifact was not written.")
else:
    print("Evidence artifact written to the configured evidence directory.")
