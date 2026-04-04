# Dataset-Backed Pipeline Remediation

Date: 2026-04-04T06:03:05Z
Repository: `/Users/etherealogic-2/Dev/Databricks/DriftSentinel`

## Issue

`run_dataset_pipeline()` accepted a registered dataset identity but still executed:

- `run_intake_demo()`
- `run_drift_demo()`
- synthetic benchmark generation unrelated to the registered dataset schema

This meant dataset-aware runs only tagged metadata onto demo results. They did
not execute controls against the registered dataset's `source.landing_path`, did
not compare against an explicit trusted baseline path, and did not benchmark
controls using a real reference sample from the dataset.

## Root Cause

Measured facts:

- `src/driftsentinel/orchestration/runner.py` routed dataset-aware execution to
  the demo helpers.
- `src/driftsentinel/intake/contracts.py` only supported the Chapter 1 demo row
  schema.
- `src/driftsentinel/benchmark/orchestrator.py` only built scenarios from the
  synthetic benchmark dataset.
- The dataset contract and drift policy templates exposed real source and
  baseline concepts that the runtime ignored.

Interpretation:

- The registry and evidence model were ahead of the execution layer.
- The product could present dataset metadata and evidence artifacts in the UI,
  but not honestly claim real dataset-backed execution.

## Remediation

Implemented changes:

- Added trusted dataset loaders in
  `src/driftsentinel/orchestration/dataset_runtime.py` for `csv`, `json`,
  `parquet`, and `delta` inputs from files or directories.
- Reworked intake to evaluate arbitrary DataFrames against declarative contract
  rules in `src/driftsentinel/intake/contracts.py`.
- Added dataset-backed stage runners:
  - `run_dataset_intake()`
  - `run_dataset_drift()`
  - `run_dataset_benchmark()`
- Reworked `run_dataset_pipeline()` to:
  - require a drift policy
  - load current data from `source.landing_path`
  - load a trusted baseline from `drift_policy.baseline.path` or
    `contract.source.baseline_path`
  - validate trusted baseline readiness before drift and benchmark
  - write stage-specific intake and drift evidence in addition to benchmark and
    pipeline summary artifacts
- Added real-reference benchmark scenario injection in
  `src/driftsentinel/benchmark/reference_data.py`.
- Generalized benchmark detectors to support arbitrary business keys and
  dataset-backed ordering columns.
- Updated templates, notebooks, and README surfaces so operator workflows match
  the corrected runtime.
- Added default install dependencies for real `parquet` and `delta` execution:
  `pyarrow` and `deltalake`.

## Verification

### Static and test checks

- `uv run ruff check .` PASS
- `uv run mypy src/driftsentinel tests` PASS
- `uv run pytest -q` PASS, `323 passed`

### Real file-backed execution proof

Executed a replayable CSV-backed dataset run using:

- current load:
  `output/verification_real_pipeline/current_costs.csv`
- trusted baseline:
  `output/verification_real_pipeline/baseline_costs.csv`
- evidence directory:
  `output/verification_real_pipeline/evidence`

Measured output:

- intake: `ready=4`, `quarantined=0`, `violations=0`
- drift: `overall_verdict=FAIL`, `columns_drifted=1`,
  `health_score=0.4732`
- benchmark: `overall_verdict=PASS`, `execution_mode=reference_data`,
  `reference_row_count=4`

Evidence artifacts written:

- `bench_42_4.json`
- `drift_meridian_project_costs.json`
- `intake_meridian_project_costs.json`
- `pipeline_meridian_project_costs.json`

## External Blocker

- `CATALOG=main make bundle-validate` remains blocked by local Databricks auth:
  `default auth: cannot configure default credentials`

This is an external environment/authentication issue, not a product code
failure in the dataset-backed runtime.
