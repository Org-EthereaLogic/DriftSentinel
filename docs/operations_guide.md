# DriftSentinel Operations Guide

## Current Stage

DriftSentinel is at the DS-IP-001 Phase 3 multi-dataset hardening stage. The
repository ships a multi-dataset registry, version-aware policy binding,
queryable evidence lookup, dataset-aware orchestration, runnable bundle
resources, and operational notebook entry points.

## What You Can Operate Today

1. Run local repository validation (`make lint`, `make typecheck`,
   `make test`).
2. Prove a Unity Catalog catalog exists with `make bundle-catalog-check
   CATALOG=<catalog> PROFILE=<profile>`.
3. Validate, deploy, and run the Databricks bundle with that catalog.
4. Run the notebooks directly from GitHub using bundled example templates or
   optional workspace YAML paths, with bundle-deployed notebooks preferring
   the uploaded bundle files.
5. Register multiple datasets via `01_register_dataset.py` with a serializable
   JSON registry.
6. Execute intake, drift, and benchmark runs for a selected dataset using the
   `dataset_id` widget in notebooks 03-05.
7. Review historical evidence filtered by dataset, date range, or run ID in
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
- **Notebook run fails before execution**: set the `catalog` widget to an
  existing Unity Catalog catalog. The notebooks now fail closed when the
  target catalog is blank.
- **Evidence is missing in `06_review_evidence.py` after a job run**: the
  default `/tmp/driftsentinel_evidence` path is cluster-local. Use a volume
  path in the `evidence_dir` widget if you need persistence across clusters.
- **Duplicate dataset registration**: the registry rejects re-registration
  of the same dataset name and contract version. Bump the `contract_version`
  in your YAML or remove the prior entry.

## Evidence Review

Evidence artifacts are append-only. Repository evidence in `report/` covers
verification and sync history. Benchmark notebook and job runs write
machine-readable JSON bundles to the configured `evidence_dir`. Each artifact
carries dataset identity, run ID, run kind, and version metadata for
structured lookup.

## Updating Policies

- Dataset contracts: edit `templates/dataset_contract.yml`
- Drift policies: edit `templates/drift_policy.yml`
- Benchmark policies: edit `templates/benchmark_policy.yml`

All templates include `contract_version` and `policy_version` fields for
explicit version binding. Policies must reference a registered dataset and
matching contract version to pass compatibility checks.
