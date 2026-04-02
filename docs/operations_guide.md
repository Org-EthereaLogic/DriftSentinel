# DriftSentinel Operations Guide

## Current Stage

DriftSentinel is currently in scaffold mode. The repository does not yet ship
operational intake, drift, or benchmark workloads. DS-IP-001 Phase 2 adds the
runtime implementations for those flows.

## What You Can Operate Today

1. Run local repository validation (`make lint`, `make typecheck`,
   `make test`).
2. Validate the Databricks bundle scaffold with authenticated CLI settings.
3. Review templates, notebooks, and bundle surfaces before Phase 2
   implementation lands.

## Troubleshooting

- **`databricks bundle validate` cannot authenticate**: configure a
  `.databrickscfg` profile, set `DATABRICKS_CONFIG_PROFILE`, or provide the
  required `DATABRICKS_*` environment variables.
- **Notebook stops immediately with a DS-IP-001 Phase 2 error**: expected
  scaffold behavior. The notebook surfaces are intentionally non-operational
  until Phase 2.
- **Need runnable jobs, pipelines, or evidence outputs**: out of scope for the
  current scaffold stage. Activate the operational flow in DS-IP-001 Phase 2.

## Evidence Review

Evidence artifacts are append-only. Current evidence in `report/` covers
repository validation and sync history; control-run evidence starts when Phase
2 adds runnable workflows.

## Updating Policies

- Dataset contracts: edit `templates/dataset_contract.yml`
- Drift policies: edit `templates/drift_policy.yml`
- Benchmark policies: edit `templates/benchmark_policy.yml`
