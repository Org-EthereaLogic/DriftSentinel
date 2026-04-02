# DriftSentinel Operations Guide

## Current Stage

DriftSentinel is in the DS-IP-001 Phase 2 packaging stage. The repository
ships runnable bundle resources, operational notebook entry points, and local
validation surfaces.

## What You Can Operate Today

1. Run local repository validation (`make lint`, `make typecheck`,
   `make test`).
2. Validate, deploy, and run the Databricks bundle with an explicit existing
   Unity Catalog catalog.
3. Run the notebooks directly from GitHub using bundled example templates or
   optional workspace YAML paths, with bundle-deployed notebooks preferring
   the uploaded bundle files.

## Troubleshooting

- **`databricks bundle validate` cannot authenticate**: configure a
  `.databrickscfg` profile, set `DATABRICKS_CONFIG_PROFILE`, or provide the
  required `DATABRICKS_*` environment variables.
- **Bundle validation or deploy fails for `catalog`**: pass an existing Unity
  Catalog catalog through `--var="catalog=<catalog>"`, `BUNDLE_VAR_catalog`,
  or `.databricks/bundle/<target>/variable-overrides.json`.
- **Notebook run fails before execution**: set the `catalog` widget to an
  existing Unity Catalog catalog. The notebooks now fail closed when the
  target catalog is blank.
- **Evidence is missing in `06_review_evidence.py` after a job run**: the
  default `/tmp/driftsentinel_evidence` path is cluster-local. Use a volume
  path in the `evidence_dir` widget if you need persistence across clusters.

## Evidence Review

Evidence artifacts are append-only. Repository evidence in `report/` covers
verification and sync history. Benchmark notebook and job runs write
machine-readable JSON bundles to the configured `evidence_dir`.

## Updating Policies

- Dataset contracts: edit `templates/dataset_contract.yml`
- Drift policies: edit `templates/drift_policy.yml`
- Benchmark policies: edit `templates/benchmark_policy.yml`
