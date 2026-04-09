# notebooks

Databricks notebooks for onboarding, execution, and evidence review.

| Notebook | Purpose |
| --- | --- |
| `00_quickstart_setup.py` | Install package, verify import, run health check |
| `01_register_dataset.py` | Load and validate a dataset contract, then persist it to the shared registry |
| `02_seed_or_import_baseline.py` | Inspect a demo baseline or import a trusted baseline from a dataset contract + drift policy |
| `03_run_intake_controls.py` | Run intake certification in demo mode or against a registered dataset from the shared registry |
| `04_run_drift_gate.py` | Run demo drift or execute drift gates against a registered dataset + explicit baseline reference |
| `05_run_control_benchmark.py` | Run synthetic benchmark mode or inject benchmark scenarios into trusted baseline reference data |
| `06_review_evidence.py` | List and inspect evidence artifacts from prior runs |
| `07_run_dataset_pipeline.py` | Run the full dataset-backed pipeline for one registered dataset |

Each notebook prefers the bundle-synced workspace source tree under
`/Workspace/.../src` when available and otherwise installs DriftSentinel from
GitHub. The package includes bundled example templates for bootstrap runs.
When `catalog` and `schema` are set, blank `registry_path` and `evidence_dir`
widgets resolve to the shared runtime volume under
`/Volumes/<catalog>/<schema>/driftsentinel_runtime/...`. Bundle-backed job
surfaces set `require_dataset_backed=true` so they fail closed instead of
quietly falling back to demo or synthetic execution.
Real dataset execution requires a registered dataset contract with
`source.format` plus either `source.landing_path` or `source.table_name`, and a
drift policy with `monitored_columns` entries that declare `column_name` plus a
supported `method` (`shannon_entropy` or `wasserstein`), and `baseline.format`
plus either `baseline.path` or `baseline.table_name`. For volume-backed files
in Databricks notebooks, use `/Volumes/...` paths rather than
`/dbfs/Volumes/...`. Notebook logic is intentionally thin -- domain logic
lives in `src/driftsentinel/`.
