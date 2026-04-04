# Enterprise Ingest and Databricks Revalidation

Date: 2026-04-04T08:25:16Z

## Scope

This pass hardened the real-data ingest surface, replayed the local operator UI
against real-world large-format evidence, and reran Databricks notebook
execution against real Unity Catalog tables.

## Measured Facts

- Runtime support now covers file-backed `csv`, `tsv`, `txt`, `json`/`jsonl`/`ndjson`, `excel`, `parquet`, `avro`, `orc`, `delta`, plus Spark/Unity Catalog tables through `format: table`.
- Table-backed execution now requires a fully qualified three-part
  `catalog.schema.table` identifier to avoid resolving against the active Spark
  namespace.
- Directory-backed multi-file loads now fail fast on schema-mismatched files
  instead of silently unioning incompatible columns.
- Local verification passed:
  - `uv run ruff check .`
  - `uv run mypy src/driftsentinel tests`
  - `uv run pytest -q` -> `348 passed in 5.28s`
- Databricks bundle validation passed:
  - `make bundle-validate PROFILE=e62-trial CATALOG=adb_dev`
- Workspace sync passed:
  - `databricks sync . /Users/anthony.johnsonii@etherealogic.ai/driftsentinel_stress_repo --full -p e62-trial`
- Databricks real-table intake rerun passed:
  - submit run id `1009630386999185`
  - task run id `107949017980613`
  - notebook `/Users/anthony.johnsonii@etherealogic.ai/driftsentinel_stress_repo/notebooks/03_run_intake_controls`
  - evidence `dbfs:/Volumes/adb_dev/default/driftsentinel_stress/evidence/intake_nyc_tlc_yellow_uc_table_1.json`
  - payload facts:
    - `total_rows: 300000`
    - `ready: 300000`
    - `quarantined: 0`
    - `overall_verdict: PASS`
    - `source.path: adb_dev.default.driftsentinel_tlc_current`
    - `source.format: table`
- Databricks real-table drift rerun passed:
  - submit run id `560760377798474`
  - task run id `481559989419032`
  - notebook `/Users/anthony.johnsonii@etherealogic.ai/driftsentinel_stress_repo/notebooks/04_run_drift_gate`
  - evidence `dbfs:/Volumes/adb_dev/default/driftsentinel_stress/evidence/drift_nyc_tlc_yellow_uc_table_1.json`
  - payload facts:
    - `health_score: 0.6006`
    - `overall_verdict: FAIL`
    - `columns_checked: 3`
    - `columns_drifted: 0`
    - `row_count_baseline: 300000`
    - `row_count_current: 300000`
    - gate `stability_health_score` failed at threshold `0.7`
    - gate `columns_drifted` passed at threshold `2.0`
- Local app replay passed against the large-format stress fixture:
  - registry rendered 4 registered datasets from `/tmp/driftsentinel_stress/config_formats/registry.json`
  - Run Status queried 16 artifacts from `/tmp/driftsentinel_stress/evidence_formats`
  - the `Visible Artifact Filename` picker opened Evidence Explorer for `pipeline_nyc_tlc_yellow_orc.json`
  - Analytics refreshed and rendered verdict, run-kind, daily volume, and daily health charts

## Changes Applied

- Tightened table resolution and multi-file schema safety in
  `src/driftsentinel/orchestration/dataset_runtime.py`.
- Added regression coverage for:
  - schema-mismatched directory rejection
  - fully qualified table-name enforcement
  - `unity_catalog_table` alias support
  - current notebook bootstrap contract
  - public docs describing the current ingest surface
- Synced public docs and templates to the real runtime contract:
  - workspace-source-tree notebook bootstrap
  - `/Volumes/...` guidance for notebook widgets
  - file-or-table baseline/source references
  - removal of stale hard-coded test-count claims

## Evidence References

- Local UI screenshots:
  - `output/playwright/enterprise-registry.png`
  - `output/playwright/enterprise-run-status.png`
  - `output/playwright/enterprise-evidence-explorer.png`
  - `output/playwright/enterprise-analytics.png`
- Databricks evidence artifacts:
  - `dbfs:/Volumes/adb_dev/default/driftsentinel_stress/evidence/intake_nyc_tlc_yellow_uc_table_1.json`
  - `dbfs:/Volumes/adb_dev/default/driftsentinel_stress/evidence/drift_nyc_tlc_yellow_uc_table_1.json`

## Interpretation

DriftSentinel now has replayable proof for real enterprise tabular ingestion
across common file formats and Unity Catalog tables, both locally and in
Databricks Free Edition. The prior silent-wrong-data risks from ambiguous table
names and mixed-schema directory loads are closed in the runtime.

The remaining product boundary is still important: this repository proves
structured and tabular data ingestion, not arbitrary enterprise binary content
such as PDFs, images, email archives, or Office documents outside spreadsheet
formats. Claiming support for non-tabular enterprise artifacts would require a
different contract and control model than the one implemented here.
