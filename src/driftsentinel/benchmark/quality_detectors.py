"""Quality detectors -- baseline (rule-based) and challenger (distribution-aware).

Ported from Chapter 3 (measurable-control-effectiveness) as first-party DriftSentinel code.
"""

from __future__ import annotations

from typing import Any

import pandas as pd


def baseline_quality_check(
    df: pd.DataFrame,
    reference_df: pd.DataFrame,
    expected_columns: list[str] | None = None,
) -> dict[str, Any]:
    """Industry-standard rule-based quality check."""
    flagged_indices: set[object] = set()

    biz_cols = [c for c in df.columns if c not in ("record_id", "row_order")]
    for col in biz_cols:
        null_mask = df[col].isna()
        flagged_indices.update(df.index[null_mask].tolist())

    dup_mask = df.duplicated(subset=["record_id"], keep="first")
    flagged_indices.update(df.index[dup_mask].tolist())

    schema_missing: list[str] = []
    if expected_columns:
        schema_missing = [c for c in expected_columns if c not in df.columns]

    return {
        "flagged_indices": sorted(flagged_indices),
        "total_flagged": len(flagged_indices),
        "total_rows": len(df),
        "schema_missing": schema_missing,
        "schema_drop_detected": len(schema_missing) > 0,
    }


def challenger_quality_check(
    df: pd.DataFrame,
    reference_df: pd.DataFrame,
    expected_columns: list[str] | None = None,
) -> dict[str, Any]:
    """Distribution-aware quality check -- catches what rule-based misses."""
    flagged_indices: set[object] = set()

    biz_cols = [c for c in df.columns if c not in ("record_id", "row_order")]

    for col in biz_cols:
        null_mask = df[col].isna()
        flagged_indices.update(df.index[null_mask].tolist())

    dup_mask = df.duplicated(subset=["record_id"], keep="first")
    flagged_indices.update(df.index[dup_mask].tolist())

    schema_missing: list[str] = []
    if expected_columns:
        schema_missing = [c for c in expected_columns if c not in df.columns]

    for col in biz_cols:
        if col not in reference_df.columns:
            continue
        ref_series = reference_df[col]
        if ref_series.dtype in ("float64", "int64", "float32", "int32"):
            for idx, val in df[col].items():
                if val is None or pd.isna(val):
                    continue
                try:
                    float(val)
                except (ValueError, TypeError):
                    flagged_indices.add(idx)

    for col in biz_cols:
        if col not in reference_df.columns:
            continue
        ref_series = reference_df[col]
        if ref_series.dtype == "object":
            known_values = set(ref_series.dropna().unique())
            if not known_values:
                continue
            for idx, val in df[col].items():
                if pd.notna(val) and val not in known_values:
                    flagged_indices.add(idx)

    return {
        "flagged_indices": sorted(flagged_indices),
        "total_flagged": len(flagged_indices),
        "total_rows": len(df),
        "schema_missing": schema_missing,
        "schema_drop_detected": len(schema_missing) > 0,
    }
