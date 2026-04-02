"""Orchestration for DriftSentinel control pipeline execution.

Phase 1 provides deterministic demo helpers for local validation.
Phase 3 adds dataset-aware execution paths that accept a registered
dataset identity and route evidence through the shared metadata contract.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from driftsentinel.benchmark.orchestrator import run_benchmark
from driftsentinel.config.loader import DatasetRegistry, check_policy_compatibility
from driftsentinel.drift.baseline import BaselineSnapshot
from driftsentinel.drift.detection import detect_drift
from driftsentinel.drift.gates import GateConfig, evaluate_gates
from driftsentinel.drift.sample_data import MONITORED_COLUMNS, generate_baseline, generate_drifted
from driftsentinel.evidence.writer import build_provenance_envelope, generate_run_id, write_evidence
from driftsentinel.intake.contracts import evaluate_batch
from driftsentinel.intake.sample_data import ALL_BATCHES


def run_intake_demo() -> dict[str, Any]:
    """Run the intake domain using local sample data."""
    all_ready: list[dict[str, Any]] = []
    all_quarantined: list[dict[str, Any]] = []
    total_violations = 0

    for name, generator in ALL_BATCHES.items():
        rows = generator()
        ready, quarantined, violations = evaluate_batch(rows)
        all_ready.extend(ready)
        all_quarantined.extend(quarantined)
        total_violations += len(violations)

    return {
        "total_rows": len(all_ready) + len(all_quarantined),
        "ready": len(all_ready),
        "quarantined": len(all_quarantined),
        "violations": total_violations,
    }


def run_drift_demo(
    *,
    run_ts: str | None = None,
) -> dict[str, Any]:
    """Run the drift domain using local sample data."""
    baseline_rows = generate_baseline()
    drifted_rows = generate_drifted()

    baseline_df = pd.DataFrame(baseline_rows)
    drifted_df = pd.DataFrame(drifted_rows)

    baseline = BaselineSnapshot.from_dataframe(baseline_df, MONITORED_COLUMNS)
    drift_result = detect_drift(baseline, drifted_df)

    configs = [
        GateConfig(
            name="stability_health_score", gate_type="FAIL",
            operator=">=", threshold=0.70, description="Health score",
        ),
        GateConfig(
            name="columns_drifted_ratio", gate_type="WARN",
            operator="<=", threshold=0.50, description="Drift ratio",
        ),
    ]
    measured = {
        "stability_health_score": drift_result.health_score,
        "columns_drifted_ratio": drift_result.columns_drifted_ratio,
    }
    gate_results, overall = evaluate_gates(configs, measured)

    gate_dicts = [
        {
            "name": gr.config.name, "threshold": gr.config.threshold,
            "measured": gr.measured_value, "verdict": gr.verdict.value,
        }
        for gr in gate_results
    ]
    col_dicts = [
        {
            "column": cr.column, "baseline_score": cr.baseline_score,
            "current_score": cr.current_score, "classification": cr.classification.value,
        }
        for cr in drift_result.column_results
    ]

    provenance = build_provenance_envelope(
        health_score=drift_result.health_score,
        overall_verdict=overall.value,
        columns_checked=drift_result.columns_checked,
        columns_drifted=drift_result.columns_drifted,
        row_count_baseline=drift_result.row_count_baseline,
        row_count_current=drift_result.row_count_current,
        schema_match=drift_result.schema_match,
        gate_results=gate_dicts,
        column_details=col_dicts,
        run_ts=run_ts,
    )

    return {
        "health_score": drift_result.health_score,
        "columns_drifted": drift_result.columns_drifted,
        "overall_verdict": overall.value,
        "provenance": provenance,
    }


def run_local_pipeline(
    evidence_dir: str | Path | None = None,
    *,
    run_ts: str | None = None,
) -> dict[str, Any]:
    """Run all three domains in sequence and optionally write evidence.

    This is the Phase 1 local execution path. It exercises intake,
    drift, and benchmark in order and returns a combined result.
    """
    intake_result = run_intake_demo()
    drift_result = run_drift_demo(run_ts=run_ts)
    benchmark_result = run_benchmark(seed=42, n_rows=200, evidence_dir=evidence_dir, run_ts=run_ts)

    combined = {
        "intake": intake_result,
        "drift": drift_result,
        "benchmark": {
            "overall_verdict": benchmark_result["overall_verdict"].value,
            "measured": benchmark_result["measured"],
            "evidence_path": str(benchmark_result["evidence_path"]) if benchmark_result["evidence_path"] else None,
        },
    }

    if evidence_dir:
        write_evidence(
            evidence_dir,
            "pipeline_summary.json",
            combined,
            run_ts=run_ts,
        )

    return combined


# ---------------------------------------------------------------------------
# Phase 3: Dataset-Aware Execution
# ---------------------------------------------------------------------------


def run_dataset_pipeline(
    registry: DatasetRegistry,
    dataset_id: str,
    *,
    evidence_dir: str | Path | None = None,
    drift_policy: dict[str, Any] | None = None,
    benchmark_policy: dict[str, Any] | None = None,
    seed: int = 42,
    n_rows: int = 200,
    run_ts: str | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Execute intake, drift, and benchmark for a registered dataset.

    Validates the dataset exists in the registry and checks policy
    compatibility before execution. Uses deterministic demo data for
    the control runs (the same underlying domain logic), but tags all
    evidence with the selected dataset identity.
    """
    contract = registry.get(dataset_id)
    ds = contract["dataset"]
    contract_version = ds.get("contract_version", "0.0.0")
    rid = run_id or generate_run_id()

    drift_binding: dict[str, str] | None = None
    bench_binding: dict[str, str] | None = None

    if drift_policy is not None:
        drift_binding = check_policy_compatibility(
            registry, drift_policy["drift_policy"], "Drift policy"
        )

    if benchmark_policy is not None:
        bench_binding = check_policy_compatibility(
            registry, benchmark_policy["benchmark_policy"], "Benchmark policy"
        )

    intake_result = run_intake_demo()
    drift_result = run_drift_demo(run_ts=run_ts)

    bench_policy_version = bench_binding["policy_version"] if bench_binding else None
    bench_kwargs: dict[str, Any] = {
        "seed": seed,
        "n_rows": n_rows,
        "run_ts": run_ts,
        "dataset_id": dataset_id,
        "contract_version": contract_version,
        "policy_version": bench_policy_version,
        "run_id": rid,
    }
    if evidence_dir:
        bench_kwargs["evidence_dir"] = evidence_dir
    benchmark_result = run_benchmark(**bench_kwargs)

    combined: dict[str, Any] = {
        "dataset_id": dataset_id,
        "contract_version": contract_version,
        "run_id": rid,
        "intake": intake_result,
        "drift": {
            "health_score": drift_result["health_score"],
            "columns_drifted": drift_result["columns_drifted"],
            "overall_verdict": drift_result["overall_verdict"],
        },
        "benchmark": {
            "overall_verdict": benchmark_result["overall_verdict"].value,
            "measured": benchmark_result["measured"],
        },
    }

    if drift_binding:
        combined["drift_policy_version"] = drift_binding["policy_version"]
    if bench_binding:
        combined["benchmark_policy_version"] = bench_binding["policy_version"]

    if evidence_dir:
        write_evidence(
            evidence_dir,
            f"pipeline_{dataset_id}.json",
            combined,
            run_ts=run_ts,
            dataset_id=dataset_id,
            contract_version=contract_version,
            policy_version=drift_binding["policy_version"] if drift_binding else None,
            run_id=rid,
            run_kind="pipeline",
        )

    return combined
