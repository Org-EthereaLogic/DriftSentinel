"""Drift detection -- compare a current load against a trusted baseline.

Ported from Chapter 2 (silent-failure-prevention) as first-party DriftSentinel code.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import pandas as pd

from driftsentinel.drift.baseline import BaselineSnapshot
from driftsentinel.drift.entropy import column_stability_score


class DriftClassification(str, Enum):
    """Per-column drift classification."""

    STABLE = "stable"
    COLLAPSED = "collapsed"
    SPIKED = "spiked"


@dataclass(frozen=True)
class ColumnDriftResult:
    """Drift result for a single column."""

    column: str
    baseline_score: float
    current_score: float
    delta: float
    classification: DriftClassification


@dataclass(frozen=True)
class DriftResult:
    """Aggregate drift result across all monitored columns."""

    column_results: tuple[ColumnDriftResult, ...] = ()
    health_score: float = 0.0
    columns_checked: int = 0
    columns_drifted: int = 0
    row_count_baseline: int = 0
    row_count_current: int = 0
    schema_match: bool = True

    @property
    def columns_drifted_ratio(self) -> float:
        if self.columns_checked == 0:
            return 0.0
        return round(self.columns_drifted / self.columns_checked, 4)


def _classify(
    baseline_score: float,
    current_score: float,
    threshold: float = 0.3,
) -> DriftClassification:
    """Classify a column's drift based on score delta."""
    delta = current_score - baseline_score
    if abs(delta) <= threshold:
        return DriftClassification.STABLE
    if delta < -threshold:
        return DriftClassification.COLLAPSED
    return DriftClassification.SPIKED


def detect_drift(
    baseline: BaselineSnapshot,
    current_df: pd.DataFrame,
    collapse_threshold: float = 0.3,
) -> DriftResult:
    """Compare a current load against a trusted baseline.

    Returns a DriftResult with per-column classifications and an aggregate
    health score.
    """
    import concurrent.futures

    def _score_col(col: str) -> ColumnDriftResult:
        baseline_score = baseline.scores.get(col, 0.0)
        current_score = column_stability_score(current_df[col]) if col in current_df.columns else 0.0
        return ColumnDriftResult(
            column=col,
            baseline_score=baseline_score,
            current_score=current_score,
            delta=round(current_score - baseline_score, 4),
            classification=_classify(baseline_score, current_score, collapse_threshold),
        )

    with concurrent.futures.ThreadPoolExecutor() as executor:
        column_results = list(executor.map(_score_col, baseline.columns))

    current_scores = [r.current_score for r in column_results]

    columns_drifted = sum(
        1 for r in column_results if r.classification != DriftClassification.STABLE
    )

    health_score = (
        round(sum(current_scores) / len(current_scores), 4)
        if current_scores
        else 0.0
    )

    schema_match = all(col in current_df.columns for col in baseline.columns)

    return DriftResult(
        column_results=tuple(column_results),
        health_score=health_score,
        columns_checked=len(baseline.columns),
        columns_drifted=columns_drifted,
        row_count_baseline=baseline.row_count,
        row_count_current=len(current_df),
        schema_match=schema_match,
    )
