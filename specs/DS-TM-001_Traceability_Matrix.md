# DS-TM-001: DriftSentinel Traceability Matrix

| Field | Value |
| --- | --- |
| Document ID | DS-TM-001 |
| Version | 1.5 |
| Status | Draft |
| Author | Anthony Johnson |
| Date | 2026-05-05 |

| PRD Requirement | SRS Requirement | Spec Surface | Verification Surface |
| --- | --- | --- | --- |
| DS-FR-001 | DS-SR-001 | PRD, SDD | repo taxonomy, CLAUDE.md, specs/ |
| DS-FR-002 | DS-SR-009 | PRD, SRS, DS-PATCH-034, DS-PATCH-035 | databricks.yml (incl. sync.exclude defaults), resources/, bundle validation, tests/test_packaging.py, Makefile (TF_ENV-wrapped bundle/app/bootstrap targets), scripts/databricks_tf_env.sh, src/driftsentinel/databricks/tf_env.py, tests/test_databricks_tf_env.py |
| DS-FR-003 | DS-SR-008 | PRD, SRS | notebooks, manual import path |
| DS-FR-004 | DS-SR-005 | PRD, SRS | templates/, config loaders, registration notebook |
| DS-FR-005 | DS-SR-002 | PRD, SDD, DS-PATCH-036 | src/driftsentinel/intake/, quarantine outputs, src/driftsentinel/orchestration/runner.py (quarantine_max_ratio gate), src/driftsentinel/config/loader.py (loader-boundary validation), templates/dataset_contract.yml, tests/test_orchestration.py::TestValidateDatasetReadiness, tests/test_dataset_orchestration.py::TestIntakeToleranceEvidence, tests/test_config_loading.py (quarantine_max_ratio cases), tests/test_intake.py (quarantine_ratio rounding) |
| DS-FR-006 | DS-SR-003 | PRD, SDD | src/driftsentinel/drift/, gate-evaluation outputs |
| DS-FR-007 | DS-SR-004 | PRD, SDD, DS-PATCH-037 | src/driftsentinel/benchmark/, evidence bundle writer, resources/benchmark_job.yml, resources/dataset_pipeline_job.yml (n_rows default = 10000), templates/benchmark_policy.yml (recall-floor comment), tests/test_benchmark.py::test_run_benchmark_at_default_n_rows_meets_recall_gate |
| DS-FR-008 | DS-SR-008 | PRD, SRS | notebooks and evidence review surfaces |
| DS-FR-009 | DS-SR-006 | PRD, TP | bundle deploy checks and manual import validation |
| DS-FR-010 | DS-SR-007, DS-SR-010 | PRD, TP | deterministic demo paths and integration tests |
| DS-FR-011 | DS-SR-011 | PRD, SRS, SCMP | .codacy/, codecov.yaml, .snyk, secret-name docs |
| DS-FR-012 | DS-SR-012 | PRD, SRS, SCMP | docs/github_project_sync.md, /sync command |
| DS-NFR-001 | DS-SNFR-002, DS-SNFR-006 | PRD, SRS, TP | report/, benchmark evidence |
| DS-NFR-002 | DS-SNFR-001 | PRD, SRS | append-only evidence writer and replay tests |
| DS-NFR-003 | DS-SNFR-003 | PRD, SRS | missing-field failure tests, blocked status checks |
| DS-NFR-004 | DS-SNFR-005 | PRD, SRS | Free Edition notebook path, workspace scheduling |
| DS-NFR-005 | DS-SNFR-004 | PRD, SDD, SCMP | specs/, .claude/, adws/, report/ scaffold |
| DS-NFR-006 | DS-SNFR-003 | PRD, SRS | blocked publication tests |
| DS-NFR-007 | DS-SNFR-007 | PRD, SRS | secret scan, .gitignore, CI checks |
| DS-NFR-008 | DS-SNFR-008 | PRD, SRS, WBS | documented pre-coding gate |
| DS-NFR-009 | DS-SNFR-009 | PRD, SRS, TP | non-blocking GitHub Project sync rules |

## Changelog

| Version | Date | Change |
| --- | --- | --- |
| 1.5 | 2026-05-05 | Linked DS-FR-007 / DS-SR-004 to DS-PATCH-037 (raise bundle-resource `n_rows` default from 1000 to 10000 in `resources/benchmark_job.yml` and `resources/dataset_pipeline_job.yml`; document the recall-floor at low N in `templates/benchmark_policy.yml`; add regression test in `tests/test_benchmark.py` asserting `quality_recall >= 0.80` at n=10000; note default change in `docs/deployment_guide.md`) |
| 1.4 | 2026-05-05 | Linked DS-FR-005 / DS-SR-002 to DS-PATCH-036 (optional `quarantine_max_ratio` knob on dataset contracts; readiness gate raises only when `quarantine_ratio > quarantine_max_ratio`; intake evidence records `quarantine_max_ratio` and `tolerance_applied`; loader rejects out-of-range / non-numeric values) |
| 1.3 | 2026-05-05 | Linked DS-FR-002 / DS-SR-009 to DS-PATCH-035 (auto-detect OpenTofu and pre-set `DATABRICKS_TF_EXEC_PATH` for the bundle/app/bootstrap surface; shell + Python helpers; env-propagation contract test) |
| 1.2 | 2026-05-05 | Linked DS-FR-002 / DS-SR-009 to DS-PATCH-034 (default `sync.exclude` patterns and packaging test coverage) |
| 1.1 | 2026-05-04 | Updated DS-FR-012 and DS-NFR-009 verification surfaces from Notion to GitHub Project (#8) following governance migration in commit 78bdf82 |
| 1.0 | 2026-04-01 | Initial draft |
