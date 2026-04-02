# tests

Product test suite for DriftSentinel. 171 tests across 8 files.

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
| `test_packaging.py` | 13 | Databricks bundle config, notebook packaging, and wheel contents |

Run with `make test` or `uv run pytest`.
