# notebooks

Databricks notebooks for onboarding, execution, and evidence review.

| Notebook | Purpose |
| --- | --- |
| `00_quickstart_setup.py` | Install package, verify import, run health check |
| `01_register_dataset.py` | Load and validate a dataset contract |
| `02_seed_or_import_baseline.py` | Seed or import a baseline snapshot for drift monitoring |
| `03_run_intake_controls.py` | Run intake certification controls |
| `04_run_drift_gate.py` | Measure distribution drift and emit gate verdicts |
| `05_run_control_benchmark.py` | Run dual-track control effectiveness benchmark |
| `06_review_evidence.py` | List and inspect evidence artifacts from prior runs |

Each notebook installs DriftSentinel via `%pip install`, preferring the
deployed bundle files when available and falling back to GitHub for standalone
imports. The package includes bundled example templates for bootstrap runs,
and the dataset registration plus benchmark notebooks also accept optional
workspace YAML paths for customized policies. Notebook logic is intentionally
thin -- domain logic lives in `src/driftsentinel/`.
