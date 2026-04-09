# DriftSentinel Operations Guide

## Current Stage

DriftSentinel is at the DS-IP-001 Phase 4 Databricks App UI stage. The
repository ships a multi-dataset registry, version-aware policy binding,
queryable evidence lookup, dataset-aware orchestration, runnable bundle
resources, operational notebook entry points, and a Gradio-based Databricks
App for operator dashboard access without editing notebooks.

## What You Can Operate Today

1. Run local repository validation (`make lint`, `make typecheck`,
   `make test`).
2. Prove a Unity Catalog catalog exists with `make bundle-catalog-check
   CATALOG=<catalog> PROFILE=<profile>`.
3. Validate, deploy, and run the Databricks bundle with that catalog and a
   shared runtime volume.
4. Deploy and start the Databricks App with `make app-deploy
   CATALOG=<catalog> PROFILE=<profile>`.
5. Run the notebooks directly from GitHub using bundled example templates or
   optional workspace YAML paths, with bundle-deployed notebooks preferring
   the workspace source tree under `/Workspace/.../src`.
6. Register multiple datasets via `01_register_dataset.py` with a serializable
   JSON registry stored in the shared runtime volume by default.
7. Execute intake, drift, benchmark, or full pipeline runs for a selected
   dataset using bundle variables or notebook widgets.
8. Review historical evidence filtered by dataset, date range, or run ID in
   `06_review_evidence.py`.

## Troubleshooting

- **`databricks bundle validate` cannot authenticate**: configure a
  `.databrickscfg` profile, set `DATABRICKS_CONFIG_PROFILE`, or provide the
  required `DATABRICKS_*` environment variables.
- **`databricks bundle validate` passes but deploy or run still fails for
  `catalog`**: `bundle validate` does not prove catalog existence. Run
  `make bundle-catalog-check CATALOG=<catalog> PROFILE=<profile>` or
  `databricks catalogs get <catalog> -p <profile>` first.
- **Bundle validation or deploy fails for `catalog`**: pass an existing Unity
  Catalog catalog through `--var="catalog=<catalog>"`, `BUNDLE_VAR_catalog`,
  or `.databricks/bundle/<target>/variable-overrides.json`.
- **The Databricks App URL exists but the app is still unavailable**:
  `databricks bundle deploy` creates the app resource only. Run
  `make app-deploy CATALOG=<catalog> PROFILE=<profile>` so Databricks Apps
  creates a new deployment and starts the app source. Verify the final state
  with `databricks apps get driftsentinel -p <profile> -o json`; `bundle
  summary` is not the proof surface for current app runtime state.
- **Databricks App deployment fails during package installation**: the repo root
  is the supported app deployment source because it installs the local
  `driftsentinel` package from this repository. Deploy from the repo root, not
  from the `app/` directory alone.
- **Notebook run fails before execution**: set the `catalog` widget to an
  existing Unity Catalog catalog. The notebooks now fail closed when the
  target catalog is blank.
- **Bundle job fails with missing `dataset_id` or policy path**: the shipped
  jobs are intentionally fail-closed. Pass `dataset_id` and the required
  `drift_policy_path` (plus `benchmark_policy_path` when needed) through
  `--var=...` instead of expecting a demo fallback.
- **Evidence is missing in `06_review_evidence.py` after a job run**: the
  bundle-backed default is the shared runtime volume, not `/tmp`. Confirm the
  job, notebook, and app all target the same `catalog`, `schema`, and
  `runtime_volume_name`, or explicitly point `evidence_dir` at the correct
  `/Volumes/...` path.
- **Notebook widgets cannot read a Databricks Volume path**: use
  `/Volumes/<catalog>/<schema>/<volume>/...` in notebook widgets. Avoid
  `/dbfs/Volumes/...`, which is not the supported path surface for notebook
  reads in this workflow.
- **Duplicate dataset registration**: the registry rejects re-registration
  of the same dataset name and contract version. Bump the `contract_version`
  in your YAML or remove the prior entry.

## Evidence Review

Evidence artifacts are append-only. Repository evidence in `report/` covers
verification and sync history. Benchmark notebook and job runs write
machine-readable JSON bundles to the configured `evidence_dir`. Each artifact
carries dataset identity, run ID, run kind, and version metadata for
structured lookup. In Databricks bundle deployments, the default evidence path
is the shared runtime volume.

## Updating Policies

- Dataset contracts: edit `templates/dataset_contract.yml`
- Drift policies: edit `templates/drift_policy.yml`
- Benchmark policies: edit `templates/benchmark_policy.yml`

All templates include `contract_version` and `policy_version` fields for
explicit version binding. Policies must reference a registered dataset and
matching contract version to pass compatibility checks.
