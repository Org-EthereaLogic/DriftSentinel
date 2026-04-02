"""Workflow sequencing for the DriftSentinel control pipeline."""

from driftsentinel.orchestration.runner import run_dataset_pipeline, run_local_pipeline

__all__ = [
    "run_dataset_pipeline",
    "run_local_pipeline",
]
