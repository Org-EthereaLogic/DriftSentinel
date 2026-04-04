# resources

Databricks Asset Bundle job and pipeline definitions.

| File | Type | Purpose |
| --- | --- | --- |
| `intake_pipeline.yml` | Pipeline (DLT) | Intake certification pipeline |
| `drift_gate_job.yml` | Job | Distribution drift gate job |
| `benchmark_job.yml` | Job | Control effectiveness benchmark job |
| `driftsentinel_app.yml` | App | Databricks App resource definition (Gradio dashboard) |

These files are included by `databricks.yml` and define the operational
Databricks resources deployed via `databricks bundle deploy`.
