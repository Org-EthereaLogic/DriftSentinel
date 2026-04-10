# tests

Product test suite for DriftSentinel.

| File | Purpose |
| --- | --- |
| `test_scaffold_layout.py` | Validates that all expected files and directories exist |
| `test_packaging.py` | Databricks bundle config, notebook packaging, wheel contents, safe bundle command docs, widgets, and app resource |
| `test_cli.py` | DriftSentinel CLI parser, Databricks bundle wrapper, file sync helpers, job helpers, and entry point wiring |
| `test_app.py` | App file structure, read-only assertions, import hygiene, helper functions, DAB resource |
| `test_stress.py` | Stress and performance tests for evidence parsing and pipeline throughput |
| `test_registry.py` | Dataset registry, serialization, policy compatibility, version metadata |
| `test_evidence_lookup.py` | Evidence metadata, list/filter, date range, malformed file handling |
| `test_config_loading.py` | YAML config loading, packaged templates, and validation |
| `test_benchmark.py` | Synthetic data, detectors, scoring, gates, orchestrator |
| `test_intake.py` | Contract validation, quarantine routing, demo metrics |
| `test_drift.py` | Entropy scoring, baseline, detection, gates, provenance |
| `test_dataset_orchestration.py` | Dataset-aware pipeline, evidence metadata end-to-end, demo preservation |
| `test_evidence_writer.py` | Append-only evidence and hash chain writing |
| `test_orchestration.py` | Local pipeline determinism, domain connectivity, evidence |
| `test_governance_guards.py` | Regression guards for banned scaffold markers and bundle invariants |
| `test_brand_assets.py` | Brand asset integrity, icon verification, and webmanifest validation |

Run with `make test` or `uv run pytest`.
