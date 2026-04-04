"""Benchmark orchestrator -- generates data, runs both tracks, scores, evaluates gates.

Ported from Chapter 3 (measurable-control-effectiveness) as first-party DriftSentinel code.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from driftsentinel.benchmark.drift_detectors import baseline_drift_check, challenger_drift_check
from driftsentinel.benchmark.gates import evaluate_gates_from_dicts
from driftsentinel.benchmark.quality_detectors import baseline_quality_check, challenger_quality_check
from driftsentinel.benchmark.reference_data import ORDER_COLUMN, build_reference_dataset
from driftsentinel.benchmark.scoring import score_drift, score_quality
from driftsentinel.benchmark.synthetic import generate_dataset
from driftsentinel.config.loader import (
    load_benchmark_policy,
    load_packaged_benchmark_policy,
    normalize_benchmark_gates,
)
from driftsentinel.evidence.writer import write_benchmark_bundle

_MONITORED_COLUMNS = [
    "department", "region", "product_category", "status", "priority",
]
_EXPECTED_COLUMNS = [
    "record_id", "customer_id", "department", "region",
    "product_category", "status", "priority", "amount",
]

def _load_default_gates() -> list[dict[str, Any]]:
    """Load gates from the packaged default benchmark policy template."""
    policy = load_packaged_benchmark_policy()
    return normalize_benchmark_gates(policy)


def run_benchmark(
    seed: int = 42,
    n_rows: int = 1000,
    evidence_dir: str | Path | None = None,
    gate_dicts: list[dict[str, Any]] | None = None,
    *,
    policy_path: str | Path | None = None,
    run_ts: str | None = None,
    dataset_id: str | None = None,
    contract_version: str | None = None,
    policy_version: str | None = None,
    run_id: str | None = None,
    reference_df: Any | None = None,
    expected_columns: list[str] | None = None,
    monitored_columns: list[str] | None = None,
    business_key: list[str] | None = None,
    quality_faults: list[dict[str, Any]] | None = None,
    drift_patterns: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Run the full dual-track benchmark and return structured results."""
    execution_mode = "synthetic"
    detector_business_key = business_key or ["record_id"]
    detector_expected_columns = list(expected_columns) if expected_columns is not None else list(_EXPECTED_COLUMNS)
    detector_monitored_columns = monitored_columns or list(_MONITORED_COLUMNS)
    order_column = "row_order"

    if reference_df is None:
        dataset = generate_dataset(seed=seed, n_rows=n_rows)
    else:
        execution_mode = "reference_data"
        dataset = build_reference_dataset(
            reference_df,
            seed=seed,
            n_rows=n_rows,
            business_key=detector_business_key,
            monitored_columns=detector_monitored_columns,
            quality_faults=quality_faults,
            drift_patterns=drift_patterns,
        )
        order_column = ORDER_COLUMN
        if expected_columns is None:
            detector_expected_columns = list(dataset.clean_df.columns)

    # --- Quality track ---
    baseline_q = baseline_quality_check(
        dataset.faulted_df,
        dataset.clean_df,
        detector_expected_columns,
        business_key=detector_business_key,
        metadata_columns=[order_column],
    )
    challenger_q = challenger_quality_check(
        dataset.faulted_df,
        dataset.clean_df,
        detector_expected_columns,
        business_key=detector_business_key,
        metadata_columns=[order_column],
    )
    baseline_q_score = score_quality(
        baseline_q["flagged_indices"], dataset.fault_manifest, len(dataset.clean_df),
    )
    challenger_q_score = score_quality(
        challenger_q["flagged_indices"], dataset.fault_manifest, len(dataset.clean_df),
    )

    # --- Drift track ---
    bl_sudden = baseline_drift_check(dataset.clean_df, dataset.drifted_sudden_df, detector_monitored_columns)
    ch_sudden = challenger_drift_check(
        dataset.clean_df,
        dataset.drifted_sudden_df,
        detector_monitored_columns,
        order_column=order_column,
    )
    bl_gradual = baseline_drift_check(dataset.clean_df, dataset.drifted_gradual_df, detector_monitored_columns)
    ch_gradual = challenger_drift_check(
        dataset.clean_df,
        dataset.drifted_gradual_df,
        detector_monitored_columns,
        order_column=order_column,
    )
    bl_newcat = baseline_drift_check(dataset.clean_df, dataset.drifted_new_cat_df, detector_monitored_columns)
    ch_newcat = challenger_drift_check(
        dataset.clean_df,
        dataset.drifted_new_cat_df,
        detector_monitored_columns,
        order_column=order_column,
    )
    bl_stable = baseline_drift_check(dataset.clean_df, dataset.stable_df, detector_monitored_columns)
    ch_stable = challenger_drift_check(
        dataset.clean_df,
        dataset.stable_df,
        detector_monitored_columns,
        order_column=order_column,
    )

    baseline_d_score = score_drift(bl_sudden, bl_gradual, bl_newcat, bl_stable)
    challenger_d_score = score_drift(ch_sudden, ch_gradual, ch_newcat, ch_stable)

    # --- Gate evaluation ---
    if gate_dicts is not None:
        gates = gate_dicts
    elif policy_path is not None:
        policy = load_benchmark_policy(policy_path)
        gates = normalize_benchmark_gates(policy)
    else:
        gates = _load_default_gates()
    q_recall_ratio = challenger_q_score.recall / max(baseline_q_score.recall, 0.001)
    d_combined_ratio = challenger_d_score.combined_score / max(baseline_d_score.combined_score, 0.001)

    measured = {
        "quality_recall": challenger_q_score.recall,
        "quality_precision": challenger_q_score.precision,
        "quality_f1": challenger_q_score.f1,
        "quality_fpr": challenger_q_score.fpr,
        "challenger_beats_baseline_quality": round(q_recall_ratio, 4),
        "sudden_drift_sensitivity": challenger_d_score.sudden_sensitivity,
        "gradual_drift_sensitivity": challenger_d_score.gradual_sensitivity,
        "drift_fpr": challenger_d_score.drift_fpr,
        "new_category_sensitivity": challenger_d_score.new_category_sensitivity,
        "challenger_beats_baseline_drift": round(d_combined_ratio, 4),
    }

    gate_results, overall_verdict = evaluate_gates_from_dicts(gates, measured)

    # --- Evidence bundle ---
    evidence_path = None
    if evidence_dir:
        evidence_path = write_benchmark_bundle(
            evidence_dir, seed, n_rows,
            baseline_q_score, challenger_q_score,
            baseline_d_score, challenger_d_score,
            gate_results, overall_verdict.value,
            run_ts=run_ts,
            dataset_id=dataset_id,
            contract_version=contract_version,
            policy_version=policy_version,
            run_id=run_id,
            execution_mode=execution_mode,
            reference_row_count=len(dataset.clean_df),
            business_key=detector_business_key,
            monitored_columns=detector_monitored_columns,
        )

    return {
        "seed": seed,
        "n_rows": n_rows,
        "execution_mode": execution_mode,
        "baseline_quality": baseline_q_score,
        "challenger_quality": challenger_q_score,
        "baseline_drift": baseline_d_score,
        "challenger_drift": challenger_d_score,
        "gate_results": gate_results,
        "overall_verdict": overall_verdict,
        "measured": measured,
        "evidence_path": evidence_path,
        "reference_row_count": len(dataset.clean_df),
    }
