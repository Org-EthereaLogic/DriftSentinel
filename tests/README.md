# tests

Product test suite for DriftSentinel. 323 tests across 16 files.

| File | Tests | Purpose |
| --- | --- | --- |
| `test_scaffold_layout.py` | 102 | Validates that all expected files and directories exist |
| `test_packaging.py` | 32 | Databricks bundle config, notebook packaging, wheel contents, safe bundle command docs, Phase 3 widgets, app resource |
| `test_app.py` | 29 | App file structure, read-only assertions, import hygiene, helper functions, DAB resource |
| `test_stress.py` | 26 | Stress and performance tests for evidence parsing and pipeline throughput |
| `test_registry.py` | 24 | Dataset registry, serialization, policy compatibility, version metadata |
| `test_evidence_lookup.py` | 19 | Evidence metadata, list/filter, date range, malformed file handling |
| `test_config_loading.py` | 15 | YAML config loading, packaged templates, and validation |
| `test_benchmark.py` | 14 | Synthetic data, detectors, scoring, gates, orchestrator |
| `test_intake.py` | 12 | Contract validation, quarantine routing, demo metrics |
| `test_drift.py` | 12 | Entropy scoring, baseline, detection, gates, provenance |
| `test_dataset_orchestration.py` | 8 | Dataset-aware pipeline, evidence metadata end-to-end, demo preservation |
| `test_evidence_writer.py` | 7 | Append-only evidence and hash chain writing |
| `test_orchestration.py` | 6 | Local pipeline determinism, domain connectivity, evidence |
| `test_governance_guards.py` | 2 | Regression guards for banned scaffold markers and bundle invariants |
| `test_brand_assets.py` | 2 | Brand asset integrity, icon verification, and webmanifest validation |

Run with `make test` or `uv run pytest`.
