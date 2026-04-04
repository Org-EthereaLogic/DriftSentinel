# notebooks

Databricks notebooks for onboarding, execution, and evidence review.

| Notebook | Purpose |
| --- | --- |
| `00_quickstart_setup.py` | Install package, verify import, run health check |
| `01_register_dataset.py` | Load and validate a dataset contract |
| `02_seed_or_import_baseline.py` | Inspect a demo baseline or import a trusted baseline from a dataset contract + drift policy |
| `03_run_intake_controls.py` | Run intake certification in demo mode or against a registered dataset from the registry |
| `04_run_drift_gate.py` | Run demo drift or execute drift gates against a registered dataset + explicit baseline path |
| `05_run_control_benchmark.py` | Run synthetic benchmark mode or inject benchmark scenarios into trusted baseline reference data |
| `06_review_evidence.py` | List and inspect evidence artifacts from prior runs |

Each notebook installs DriftSentinel via `%pip install`, preferring the
deployed bundle files when available and falling back to GitHub for standalone
imports. The package includes bundled example templates for bootstrap runs.
Real dataset execution requires a registered dataset contract with
`source.landing_path` plus a drift policy with an explicit baseline path.
Notebook logic is intentionally thin -- domain logic lives in
`src/driftsentinel/`.
