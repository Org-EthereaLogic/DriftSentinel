"""Tests for the drift domain -- entropy, baseline, detection, and gates.

All data is deterministic and local to DriftSentinel.
"""

from __future__ import annotations

import math

import pandas as pd
import pytest

from driftsentinel.drift.baseline import BaselineSnapshot
from driftsentinel.drift.detection import (
    DriftClassification,
    DriftResult,
    detect_drift,
)
from driftsentinel.drift.entropy import _shannon_entropy, column_stability_score
from driftsentinel.drift.gates import (
    GateConfig,
    GateVerdict,
    evaluate_gates,
)
from driftsentinel.drift.sample_data import (
    MONITORED_COLUMNS,
    generate_baseline,
    generate_drifted,
)
from driftsentinel.drift.scoring import DriftMethod
from driftsentinel.evidence.writer import build_provenance_envelope

FIXED_TS = "2026-04-02T00:00:00+00:00"


# --- Entropy ---


def test_uniform_distribution_has_full_stability() -> None:
    series = pd.Series(["A", "B", "C", "D", "E"] * 5)
    score = column_stability_score(series)
    assert score == 1.0


def test_collapsed_column_has_zero_stability() -> None:
    series = pd.Series(["X"] * 25)
    score = column_stability_score(series)
    assert score == 0.0


def test_partial_diversity() -> None:
    series = pd.Series(["A"] * 20 + ["B"] * 5)
    score = column_stability_score(series)
    assert 0.0 < score < 1.0


def test_vectorized_entropy_matches_loop_implementation() -> None:
    """Verify the numpy-vectorized entropy matches a reference loop calculation."""

    def _reference_entropy(series: pd.Series) -> float:
        counts = series.value_counts(dropna=False)
        total = counts.sum()
        if total == 0:
            return 0.0
        probs = counts / total
        return -sum(p * math.log2(p) for p in probs if p > 0)

    test_cases: list[pd.Series] = [  # type: ignore[type-arg]
        pd.Series(["A", "B", "C", "D", "E"] * 100),
        pd.Series(["X"] * 500),
        pd.Series(["A"] * 400 + ["B"] * 100),
        pd.Series(list(range(200))),
        pd.Series([1.0, 2.0, 3.0, None, 1.0, 2.0, None] * 50),
        pd.Series([True, False, True, True, False] * 100),
    ]
    for series in test_cases:
        vectorized = _shannon_entropy(series)
        reference = _reference_entropy(series)
        assert abs(vectorized - reference) < 1e-10, (
            f"Entropy mismatch: vectorized={vectorized}, reference={reference}"
        )


# --- Baseline ---


def test_baseline_from_dataframe() -> None:
    rows = generate_baseline()
    df = pd.DataFrame(rows)
    baseline = BaselineSnapshot.from_dataframe(df, MONITORED_COLUMNS)
    assert baseline.row_count == 25
    assert len(baseline.columns) == 5
    for col in MONITORED_COLUMNS:
        assert baseline.scores[col] == 1.0


# --- Drift detection ---


def test_detect_drift_stable() -> None:
    rows = generate_baseline()
    df = pd.DataFrame(rows)
    baseline = BaselineSnapshot.from_dataframe(df, MONITORED_COLUMNS)
    result = detect_drift(baseline, df)
    assert result.columns_drifted == 0
    assert result.schema_match is True


def test_detect_drift_collapsed() -> None:
    baseline_rows = generate_baseline()
    drifted_rows = generate_drifted()
    baseline_df = pd.DataFrame(baseline_rows)
    drifted_df = pd.DataFrame(drifted_rows)
    baseline = BaselineSnapshot.from_dataframe(baseline_df, MONITORED_COLUMNS)
    result = detect_drift(baseline, drifted_df, baseline_df=baseline_df)
    assert result.columns_drifted == 4
    assert result.health_score < 1.0
    collapsed = [r for r in result.column_results if r.classification == DriftClassification.COLLAPSED]
    assert len(collapsed) == 4


def test_detect_drift_wasserstein_respects_policy_method() -> None:
    baseline_df = pd.DataFrame({"amount": [10.0, 11.0, 12.0, 13.0, 14.0]})
    current_df = pd.DataFrame({"amount": [100.0, 101.0, 102.0, 103.0, 104.0]})
    baseline = BaselineSnapshot.from_dataframe(
        baseline_df,
        ["amount"],
        methods={"amount": DriftMethod.WASSERSTEIN},
    )

    result = detect_drift(baseline, current_df, baseline_df=baseline_df)

    assert result.columns_drifted == 1
    assert result.column_results[0].method == "wasserstein"
    assert result.column_results[0].current_score < 0.7


def test_detect_drift_requires_reference_frame_for_wasserstein() -> None:
    baseline_df = pd.DataFrame({"amount": [10.0, 11.0, 12.0]})
    current_df = pd.DataFrame({"amount": [100.0, 101.0, 102.0]})
    baseline = BaselineSnapshot.from_dataframe(
        baseline_df,
        ["amount"],
        methods={"amount": DriftMethod.WASSERSTEIN},
    )

    with pytest.raises(ValueError, match="requires a reference baseline series"):
        detect_drift(baseline, current_df)


def test_drift_result_ratio() -> None:
    result = DriftResult(columns_checked=5, columns_drifted=2)
    assert result.columns_drifted_ratio == 0.4


# --- Gate evaluation ---


def test_gate_pass() -> None:
    configs = [
        GateConfig(name="health", gate_type="FAIL", operator=">=", threshold=0.70, description="health check"),
    ]
    results, overall = evaluate_gates(configs, {"health": 0.85})
    assert overall == GateVerdict.PASS
    assert results[0].verdict == GateVerdict.PASS


def test_gate_fail() -> None:
    configs = [
        GateConfig(name="health", gate_type="FAIL", operator=">=", threshold=0.70, description="health check"),
    ]
    results, overall = evaluate_gates(configs, {"health": 0.50})
    assert overall == GateVerdict.FAIL


def test_gate_warn() -> None:
    configs = [
        GateConfig(name="drift_ratio", gate_type="WARN", operator="<=", threshold=0.30, description="drift ratio"),
    ]
    results, overall = evaluate_gates(configs, {"drift_ratio": 0.50})
    assert overall == GateVerdict.WARN


def test_overall_verdict_fail_dominates_warn() -> None:
    configs = [
        GateConfig(name="g1", gate_type="WARN", operator=">=", threshold=0.90, description="warn gate"),
        GateConfig(name="g2", gate_type="FAIL", operator=">=", threshold=0.90, description="fail gate"),
    ]
    results, overall = evaluate_gates(configs, {"g1": 0.50, "g2": 0.50})
    assert overall == GateVerdict.FAIL


# --- Provenance envelope ---


def test_provenance_envelope_from_drift_run() -> None:
    baseline_rows = generate_baseline()
    drifted_rows = generate_drifted()
    baseline_df = pd.DataFrame(baseline_rows)
    drifted_df = pd.DataFrame(drifted_rows)
    baseline = BaselineSnapshot.from_dataframe(baseline_df, MONITORED_COLUMNS)
    drift_result = detect_drift(baseline, drifted_df)

    configs = [
        GateConfig(name="health", gate_type="FAIL", operator=">=", threshold=0.70, description="test"),
    ]
    gate_results, overall = evaluate_gates(configs, {"health": drift_result.health_score})

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
            "method": cr.method,
        }
        for cr in drift_result.column_results
    ]

    envelope = build_provenance_envelope(
        health_score=drift_result.health_score,
        overall_verdict=overall.value,
        columns_checked=drift_result.columns_checked,
        columns_drifted=drift_result.columns_drifted,
        row_count_baseline=drift_result.row_count_baseline,
        row_count_current=drift_result.row_count_current,
        schema_match=drift_result.schema_match,
        gate_results=gate_dicts,
        column_details=col_dicts,
        run_ts=FIXED_TS,
    )
    assert envelope["run_ts"] == FIXED_TS
    assert envelope["columns_drifted"] == 4
    assert envelope["overall_verdict"] in ("PASS", "WARN", "FAIL")
