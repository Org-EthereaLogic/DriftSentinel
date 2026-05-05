"""Tests for the benchmark domain -- synthetic data, detectors, scoring, orchestrator.

All data is deterministic (seed-controlled) and local to DriftSentinel.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from driftsentinel.benchmark.drift_detectors import baseline_drift_check, challenger_drift_check
from driftsentinel.benchmark.gates import GateVerdict, evaluate_gates_from_dicts
from driftsentinel.benchmark.orchestrator import run_benchmark
from driftsentinel.benchmark.quality_detectors import baseline_quality_check, challenger_quality_check
from driftsentinel.benchmark.reference_data import (
    ORDER_COLUMN,
    _inject_gradual_decay,
    _inject_new_category,
    _inject_quality_faults,
    _inject_sudden_shift,
)
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
            "name": "quality_recall",
            "type": "FAIL",
            "operator": ">=",
            "threshold": 0.5,
            "track": "quality",
            "description": "test",
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


def test_run_benchmark_at_default_n_rows_meets_recall_gate() -> None:
    """At the bundle default n=10000, challenger quality_recall must clear
    the 0.80 FAIL gate on the synthetic clean dataset (DS-PATCH-037)."""
    result = run_benchmark(seed=SEED, n_rows=10000)
    assert result["measured"]["quality_recall"] >= 0.80, (
        f"quality_recall {result['measured']['quality_recall']:.3f} below 0.80 PASS gate at n=10000 — see DS-PATCH-037"
    )


def test_run_benchmark_with_reference_data() -> None:
    reference_df = pd.DataFrame(
        [
            {"id": 1, "batch_id": "B-1", "category": "A", "amount": 10.0},
            {"id": 2, "batch_id": "B-1", "category": "B", "amount": 15.0},
            {"id": 3, "batch_id": "B-1", "category": "A", "amount": 20.0},
            {"id": 4, "batch_id": "B-1", "category": "C", "amount": 25.0},
        ]
    )

    result = run_benchmark(
        seed=SEED,
        n_rows=4,
        reference_df=reference_df,
        expected_columns=list(reference_df.columns),
        monitored_columns=["category", "amount"],
        business_key=["id"],
    )

    assert result["execution_mode"] == "reference_data"
    assert result["reference_row_count"] == 4
    assert result["overall_verdict"] in (GateVerdict.PASS, GateVerdict.WARN, GateVerdict.FAIL)


def test_run_benchmark_with_boolean_columns() -> None:
    """Benchmark fault injection must handle boolean dtype columns without crashing."""
    reference_df = pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "batch_id": ["B-1"] * 10,
            "is_active": [True, False, True, True, False, True, False, True, False, True],
            "is_verified": [False, True, False, True, True, False, True, False, True, False],
            "amount": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0],
        }
    )
    assert pd.api.types.is_bool_dtype(reference_df["is_active"])

    result = run_benchmark(
        seed=SEED,
        n_rows=10,
        reference_df=reference_df,
        expected_columns=list(reference_df.columns),
        monitored_columns=["is_active", "is_verified", "amount"],
        business_key=["id"],
        quality_faults=[
            {"type": "null_injection", "columns": ["is_active"], "rate": 0.30},
            {"type": "duplicate_inflation", "rate": 0.10},
            {"type": "type_corruption", "columns": ["is_verified"], "rate": 0.20},
        ],
        drift_patterns=[
            {"type": "sudden_shift", "columns": ["is_active"]},
            {"type": "gradual_decay", "columns": ["is_verified"]},
            {"type": "new_category", "columns": ["is_active"]},
        ],
    )

    assert result["execution_mode"] == "reference_data"
    assert result["overall_verdict"] in (GateVerdict.PASS, GateVerdict.WARN, GateVerdict.FAIL)


# --- Boolean dtype fault injection (unit tests) ---


def _bool_df() -> pd.DataFrame:
    """Return a small DataFrame with boolean columns for injection testing."""
    df = pd.DataFrame(
        {
            "id": range(20),
            "flag_a": [True, False] * 10,
            "flag_b": [False, True, True, False] * 5,
            "amount": [float(i) for i in range(20)],
            ORDER_COLUMN: range(20),
        }
    )
    assert pd.api.types.is_bool_dtype(df["flag_a"])
    assert pd.api.types.is_bool_dtype(df["flag_b"])
    return df


def test_null_injection_on_bool_column() -> None:
    """Null injection into a boolean column must not raise TypeError."""
    df = _bool_df()
    rng = np.random.default_rng(42)
    faulted, manifest = _inject_quality_faults(
        df,
        quality_faults=[{"type": "null_injection", "columns": ["flag_a"], "rate": 0.30}],
        business_key=["id"],
        rng=rng,
    )
    null_indices = manifest["null_indices"]["flag_a"]
    assert len(null_indices) > 0
    assert faulted.loc[null_indices, "flag_a"].isna().all()
    non_null_mask = ~faulted.index.isin(null_indices)
    assert faulted.loc[non_null_mask, "flag_a"].notna().all()


def test_sudden_shift_on_bool_column() -> None:
    """Sudden shift on a boolean column must not raise TypeError."""
    df = _bool_df()
    shifted, info = _inject_sudden_shift(df, ["flag_a"])
    assert "flag_a" in info["columns"]
    assert shifted["flag_a"].nunique() == 1


def test_gradual_decay_on_bool_column() -> None:
    """Gradual decay on a boolean column must not raise TypeError."""
    df = _bool_df()
    rng = np.random.default_rng(42)
    decayed, info = _inject_gradual_decay(df, ["flag_b"], rng=rng)
    assert "flag_b" in info["columns"]
    assert info["changed_rows"]["flag_b"] > 0


def test_new_category_on_bool_column() -> None:
    """New category injection on a boolean column must not raise TypeError."""
    df = _bool_df()
    rng = np.random.default_rng(42)
    injected, info = _inject_new_category(df, ["flag_a"], rng=rng)
    assert "flag_a" in info["columns"]
    assert (injected["flag_a"] == "__NEW_CATEGORY__").any()
