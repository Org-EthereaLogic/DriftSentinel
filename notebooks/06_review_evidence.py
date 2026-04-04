# Databricks notebook source
# MAGIC %md
# MAGIC # DriftSentinel — Review Evidence
# MAGIC
# MAGIC Inspect historical control run evidence with optional filtering by
# MAGIC dataset, date range, or run ID.

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

dbutils.widgets.text("evidence_dir", "/tmp/driftsentinel_evidence", "Path to evidence directory")
dbutils.widgets.text("dataset_id", "", "Filter by dataset ID")
dbutils.widgets.text("run_kind", "", "Filter by run kind (intake, drift, benchmark, pipeline)")
dbutils.widgets.text("run_id", "", "Filter by run ID")
dbutils.widgets.text("date_from", "", "Filter from date (ISO format)")
dbutils.widgets.text("date_to", "", "Filter to date (ISO format)")

# COMMAND ----------

evidence_dir = dbutils.widgets.get("evidence_dir")
dataset_id = dbutils.widgets.get("dataset_id").strip() or None
run_kind = dbutils.widgets.get("run_kind").strip() or None
run_id = dbutils.widgets.get("run_id").strip() or None
date_from = dbutils.widgets.get("date_from").strip() or None
date_to = dbutils.widgets.get("date_to").strip() or None
print(f"Evidence directory: {evidence_dir}")
if dataset_id:
    print(f"Filter dataset: {dataset_id}")
if run_kind:
    print(f"Filter run kind: {run_kind}")
if run_id:
    print(f"Filter run ID: {run_id}")
if date_from or date_to:
    print(f"Filter date range: {date_from or '*'} to {date_to or '*'}")

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


os.environ["EVIDENCE_DIR"] = evidence_dir
_configure_trusted_roots(evidence_dir)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Query Evidence

# COMMAND ----------

from driftsentinel.evidence.writer import list_evidence, load_evidence

results = list_evidence(
    evidence_dir,
    dataset_id=dataset_id,
    run_kind=run_kind,
    run_id=run_id,
    date_from=date_from,
    date_to=date_to,
)

if not results:
    print("No evidence artifacts found matching the filters.")
    print("Run a pipeline or benchmark first to generate evidence artifacts.")
else:
    print(f"Found {len(results)} evidence artifact(s):")
    for r in results:
        if r.get("parse_error"):
            print(f"  [malformed] {r['file']}")
        else:
            parts = [r.get("generated_at", "?")]
            if r.get("dataset_id"):
                parts.append(f"dataset={r['dataset_id']}")
            if r.get("run_kind"):
                parts.append(f"kind={r['run_kind']}")
            if r.get("run_id"):
                parts.append(f"run={r['run_id'][:8]}...")
            print(f"  {' | '.join(parts)} — {r['file']}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Display Evidence Contents

# COMMAND ----------

import json

for r in results:
    if r.get("parse_error"):
        continue
    try:
        data = load_evidence(r["file"])
    except (FileNotFoundError, ValueError) as exc:
        print(f"Could not load {r['file']}: {exc}")
        continue
    print(f"\n{'=' * 60}")
    print(f"File: {r['file']}")
    print(f"{'=' * 60}")
    print(json.dumps(data, indent=2, default=str))
