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

PHASE_TWO_MESSAGE = (
    "DriftSentinel scaffold notebook is not operational yet. "
    "DS-IP-001 Phase 2 (Databricks MVP Packaging) must be implemented before this notebook can run."
)

raise RuntimeError(PHASE_TWO_MESSAGE)
