# notebooks

Databricks notebooks for onboarding, execution, and evidence review.

| Notebook | Purpose |
| --- | --- |
| `00_quickstart_setup.py` | Environment setup and dataset registration |
| `01_register_dataset.py` | Register a new dataset contract |
| `02_seed_or_import_baseline.py` | Seed or import a baseline snapshot |
| `03_run_intake_controls.py` | Run intake certification controls |
| `04_run_drift_gate.py` | Run distribution drift gate |
| `05_run_control_benchmark.py` | Run control effectiveness benchmark |
| `06_review_evidence.py` | Review evidence artifacts from prior runs |

All notebooks are scaffold stubs that fail closed with a DS-IP-001 Phase 2
runtime error until implementation lands.
