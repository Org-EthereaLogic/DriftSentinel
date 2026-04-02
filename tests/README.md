# tests

Product test suite for DriftSentinel. 224 tests across 11 files.

| File | Tests | Purpose |
| --- | --- | --- |
| `test_scaffold_layout.py` | 92 | Validates that all expected files and directories exist |
| `test_governance_guards.py` | 2 | Regression guards for banned scaffold markers and bundle invariants |
| `test_intake.py` | 12 | Contract validation, quarantine routing, demo metrics |
| `test_drift.py` | 12 | Entropy scoring, baseline, detection, gates, provenance |
| `test_benchmark.py` | 14 | Synthetic data, detectors, scoring, gates, orchestrator |
| `test_orchestration.py` | 6 | Local pipeline determinism, domain connectivity, evidence |
| `test_config_loading.py` | 14 | YAML config loading, packaged templates, and validation |
| `test_evidence_writer.py` | 6 | Append-only evidence and hash chain writing |
| `test_packaging.py` | 21 | Databricks bundle config, notebook packaging, wheel contents, safe bundle command docs, Phase 3 widgets |
| `test_registry.py` | 22 | Dataset registry, serialization, policy compatibility, version metadata |
| `test_evidence_lookup.py` | 15 | Evidence metadata, list/filter, date range, malformed file handling |
| `test_dataset_orchestration.py` | 8 | Dataset-aware pipeline, evidence metadata end-to-end, demo preservation |

Run with `make test` or `uv run pytest`.
