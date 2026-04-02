"""Tests for the benchmark domain -- synthetic data, detectors, scoring, orchestrator.

All data is deterministic (seed-controlled) and local to DriftSentinel.
"""

from __future__ import annotations

import json
from pathlib import Path

from driftsentinel.benchmark.drift_detectors import baseline_drift_check, challenger_drift_check
from driftsentinel.benchmark.gates import GateVerdict, evaluate_gates_from_dicts
from driftsentinel.benchmark.orchestrator import run_benchmark
from driftsentinel.benchmark.quality_detectors import baseline_quality_check, challenger_quality_check
from driftsentinel.benchmark.scoring import score_drift, score_quality
from driftsentinel.benchmark.synthetic import generate_dataset

SEED = 42
N_ROWS = 200
MONITORED = ["department", "region", "product_category", "status", "priority"]
EXPECTED = ["record_id", "customer_id", "department", "region", "product_category", "status", "priority", "amount"]
FIXED_TS = "2026-04-02T00:00:00+00:00"


# --- Synthetic data ---


def test_generate_dataset_deterministic() -> None:
    ds1 = generate_dataset(seed=SEED, n_rows=N_ROWS)
    ds2 = generate_dataset(seed=SEED, n_rows=N_ROWS)
    assert ds1.clean_df.equals(ds2.clean_df)
    assert ds1.fault_manifest == ds2.fault_manifest


def test_generated_dataset_has_all_variants() -> None:
    ds = generate_dataset(seed=SEED, n_rows=N_ROWS)
    assert ds.clean_df is not None
    assert ds.faulted_df is not None
    assert ds.drifted_sudden_df is not None
    assert ds.drifted_gradual_df is not None
    assert ds.drifted_new_cat_df is not None
    assert ds.stable_df is not None


def test_fault_manifest_has_indices() -> None:
    ds = generate_dataset(seed=SEED, n_rows=N_ROWS)
    assert "faulted_row_indices" in ds.fault_manifest
    assert len(ds.fault_manifest["faulted_row_indices"]) > 0


# --- Quality detectors ---


def test_baseline_quality_detects_faults() -> None:
    ds = generate_dataset(seed=SEED, n_rows=N_ROWS)
    result = baseline_quality_check(ds.faulted_df, ds.clean_df, EXPECTED)
    assert result["total_flagged"] > 0
    assert result["schema_drop_detected"] is True


def test_challenger_quality_finds_more() -> None:
    ds = generate_dataset(seed=SEED, n_rows=N_ROWS)
    bl = baseline_quality_check(ds.faulted_df, ds.clean_df, EXPECTED)
    ch = challenger_quality_check(ds.faulted_df, ds.clean_df, EXPECTED)
    assert ch["total_flagged"] >= bl["total_flagged"]


# --- Drift detectors ---


def test_baseline_drift_detects_sudden() -> None:
    ds = generate_dataset(seed=SEED, n_rows=N_ROWS)
    result = baseline_drift_check(ds.clean_df, ds.drifted_sudden_df, MONITORED)
    assert result["drifted"] is True


def test_challenger_drift_detects_gradual() -> None:
    ds = generate_dataset(seed=SEED, n_rows=N_ROWS)
    result = challenger_drift_check(ds.clean_df, ds.drifted_gradual_df, MONITORED)
    assert result["drifted"] is True


def test_challenger_drift_detects_new_category() -> None:
    ds = generate_dataset(seed=SEED, n_rows=N_ROWS)
    result = challenger_drift_check(ds.clean_df, ds.drifted_new_cat_df, MONITORED)
    assert result["drifted"] is True


def test_stable_data_no_drift() -> None:
    ds = generate_dataset(seed=SEED, n_rows=N_ROWS)
    result = baseline_drift_check(ds.clean_df, ds.stable_df, MONITORED)
    assert result["drifted"] is False


# --- Scoring ---


def test_quality_scoring() -> None:
    ds = generate_dataset(seed=SEED, n_rows=N_ROWS)
    ch = challenger_quality_check(ds.faulted_df, ds.clean_df, EXPECTED)
    score = score_quality(ch["flagged_indices"], ds.fault_manifest, N_ROWS)
    assert score.recall > 0
    assert score.precision > 0


def test_drift_scoring() -> None:
    ds = generate_dataset(seed=SEED, n_rows=N_ROWS)
    sudden = challenger_drift_check(ds.clean_df, ds.drifted_sudden_df, MONITORED)
    gradual = challenger_drift_check(ds.clean_df, ds.drifted_gradual_df, MONITORED)
    newcat = challenger_drift_check(ds.clean_df, ds.drifted_new_cat_df, MONITORED)
    stable = challenger_drift_check(ds.clean_df, ds.stable_df, MONITORED)
    score = score_drift(sudden, gradual, newcat, stable)
    assert score.sudden_detected is True
    assert score.combined_score > 0


# --- Gate evaluation ---


def test_benchmark_gates() -> None:
    gates = [
        {
            "name": "quality_recall", "type": "FAIL", "operator": ">=",
            "threshold": 0.5, "track": "quality", "description": "test",
        },
    ]
    results, overall = evaluate_gates_from_dicts(gates, {"quality_recall": 0.8})
    assert overall == GateVerdict.PASS


# --- Full orchestrator ---


def test_run_benchmark_deterministic() -> None:
    r1 = run_benchmark(seed=SEED, n_rows=N_ROWS)
    r2 = run_benchmark(seed=SEED, n_rows=N_ROWS)
    assert r1["measured"] == r2["measured"]
    assert r1["overall_verdict"] == r2["overall_verdict"]


def test_run_benchmark_with_evidence(tmp_path: Path) -> None:
    result = run_benchmark(seed=SEED, n_rows=N_ROWS, evidence_dir=tmp_path, run_ts=FIXED_TS)
    assert result["evidence_path"] is not None
    assert result["evidence_path"].exists()
    data = json.loads(result["evidence_path"].read_text())
    assert data["meta"]["generated_at"] == FIXED_TS
    assert "payload" in data
