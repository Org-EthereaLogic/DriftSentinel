# orchestration

Workflow sequencing for the DriftSentinel control pipeline.

Responsibilities:
- Coordinating intake, drift, and benchmark stages in order
- Managing run context and configuration propagation
- Routing results to the evidence writer
- Dataset-aware execution with registry-backed validation and version checks

Key exports: `run_local_pipeline`, `run_dataset_pipeline`.

Key file: `runner.py`.
