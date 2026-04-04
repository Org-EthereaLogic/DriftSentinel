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
