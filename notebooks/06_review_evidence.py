# Databricks notebook source
# MAGIC %md
# MAGIC # DriftSentinel — Review Evidence
# MAGIC
# MAGIC Inspect the latest control run evidence: quarantine counts, drift verdicts,
# MAGIC benchmark scores, and gate outcomes.

# COMMAND ----------

# MAGIC %pip install git+https://github.com/Org-EthereaLogic/DriftSentinel.git
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
