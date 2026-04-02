"""Ground-truth scoring -- compare detector output against injection manifests.

Ported from Chapter 3 (measurable-control-effectiveness) as first-party DriftSentinel code.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class QualityScore:
    """Precision, recall, F1 for quality fault detection."""

    true_positives: int
    false_positives: int
    false_negatives: int
    recall: float
    precision: float
    f1: float
    fpr: float
    schema_drop_detected: bool


@dataclass(frozen=True)
class DriftScore:
    """Per-scenario drift detection results."""

    sudden_detected: bool
    gradual_detected: bool
    new_category_detected: bool
    stable_false_positive: bool
    sudden_sensitivity: float
    gradual_sensitivity: float
    new_category_sensitivity: float
    drift_fpr: float
    combined_score: float


def score_quality(
    flagged_indices: list[int],
    manifest: dict[str, Any],
    total_clean_rows: int,
) -> QualityScore:
    """Score quality detection against ground truth."""
    true_faulted = set(manifest.get("faulted_row_indices", []))
    dup_indices = set(manifest.get("duplicate_indices", []))
    all_known_bad = true_faulted | {
        total_clean_rows + i for i in range(len(dup_indices))
    }

    flagged_set = set(flagged_indices)

    tp = len(flagged_set & all_known_bad)
    fp = len(flagged_set - all_known_bad)
    fn = len(all_known_bad - flagged_set)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    fpr = fp / max(1, total_clean_rows - len(true_faulted))
    schema_dropped = "schema_dropped" in manifest

    return QualityScore(
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        recall=round(recall, 4),
        precision=round(precision, 4),
        f1=round(f1, 4),
        fpr=round(fpr, 4),
        schema_drop_detected=schema_dropped,
    )


def score_drift(
    sudden_result: dict[str, Any],
    gradual_result: dict[str, Any],
    new_cat_result: dict[str, Any],
    stable_result: dict[str, Any],
) -> DriftScore:
    """Score drift detection across all four scenarios."""
    sudden_ok = sudden_result.get("drifted", False)
    gradual_ok = gradual_result.get("drifted", False)
    new_cat_ok = new_cat_result.get("drifted", False)
    stable_fp = stable_result.get("drifted", False)

    sudden_sens = 1.0 if sudden_ok else 0.0
    gradual_sens = 1.0 if gradual_ok else 0.0
    new_cat_sens = 1.0 if new_cat_ok else 0.0
    fpr = 1.0 if stable_fp else 0.0

    combined = round(
        (sudden_sens + gradual_sens + new_cat_sens) / 3.0 * (1.0 - fpr * 0.5),
        4,
    )

    return DriftScore(
        sudden_detected=sudden_ok,
        gradual_detected=gradual_ok,
        new_category_detected=new_cat_ok,
        stable_false_positive=stable_fp,
        sudden_sensitivity=sudden_sens,
        gradual_sensitivity=gradual_sens,
        new_category_sensitivity=new_cat_sens,
        drift_fpr=fpr,
        combined_score=combined,
    )
