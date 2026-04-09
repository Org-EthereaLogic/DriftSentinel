# resources

Databricks Asset Bundle runtime volume, job, and app definitions.

| File | Type | Purpose |
| --- | --- | --- |
| `runtime_volume.yml` | Volume | Shared Unity Catalog volume for registry and evidence state |
| `intake_pipeline.yml` | Job | Intake certification job keyed as `intake_pipeline` for bundle-run compatibility |
| `drift_gate_job.yml` | Job | Distribution drift gate job |
| `benchmark_job.yml` | Job | Control effectiveness benchmark job |
| `dataset_pipeline_job.yml` | Job | Full intake + drift + benchmark dataset pipeline job |
| `driftsentinel_app.yml` | App | Databricks App resource definition with runtime volume injection |

These files are included by `databricks.yml` and define the operational
Databricks resources deployed via `databricks bundle deploy`. Bundle-backed
jobs use the shared runtime volume instead of cluster-local `/tmp` defaults and
are configured to fail closed when required dataset-backed inputs are missing.
