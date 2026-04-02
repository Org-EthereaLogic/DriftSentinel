# Databricks notebook source
# MAGIC %md
# MAGIC # DriftSentinel — Review Evidence
# MAGIC
# MAGIC Inspect the latest control run evidence: quarantine counts, drift verdicts,
# MAGIC benchmark scores, and gate outcomes.

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

dbutils.widgets.text("evidence_dir", "/tmp/driftsentinel_evidence", "Path to evidence directory")

# COMMAND ----------

import json
import os

evidence_dir = dbutils.widgets.get("evidence_dir")
print(f"Evidence directory: {evidence_dir}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## List Evidence Files

# COMMAND ----------

if not os.path.isdir(evidence_dir):
    print(f"Directory not found: {evidence_dir}")
    print("Run a pipeline or benchmark first to generate evidence artifacts.")
else:
    files = sorted(f for f in os.listdir(evidence_dir) if f.endswith(".json"))
    if not files:
        print("No evidence files found.")
    else:
        print(f"Found {len(files)} evidence file(s):")
        for f in files:
            size = os.path.getsize(os.path.join(evidence_dir, f))
            print(f"  {f} ({size} bytes)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Display Evidence Contents

# COMMAND ----------

if os.path.isdir(evidence_dir):
    files = sorted(f for f in os.listdir(evidence_dir) if f.endswith(".json"))
    for f in files:
        path = os.path.join(evidence_dir, f)
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        print(f"\n{'=' * 60}")
        print(f"File: {f}")
        print(f"{'=' * 60}")
        print(json.dumps(data, indent=2, default=str))
