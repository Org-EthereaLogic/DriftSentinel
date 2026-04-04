"""Benchmark scenario generation from real reference data."""

from __future__ import annotations

from typing import Any, Sequence

import numpy as np
import pandas as pd

from driftsentinel.benchmark.synthetic import GeneratedDataset

ORDER_COLUMN = "__driftsentinel_row_order"


def _pick_candidate_columns(df: pd.DataFrame, *, exclude: set[str]) -> list[str]:
    return [column for column in df.columns if column not in exclude]


def _default_quality_faults(df: pd.DataFrame, business_key: Sequence[str]) -> list[dict[str, Any]]:
    candidates = _pick_candidate_columns(df, exclude=set(business_key) | {ORDER_COLUMN})
    numeric = [
        column for column in candidates
        if pd.api.types.is_numeric_dtype(df[column])
    ]
    null_target = numeric[:1] or candidates[:1]
    type_target = numeric[:1] or candidates[:1]
    return [
        {"type": "null_injection", "columns": null_target, "rate": 0.10},
        {"type": "duplicate_inflation", "rate": 0.05},
        {"type": "type_corruption", "columns": type_target, "rate": 0.05},
    ]


def _default_drift_patterns(monitored_columns: Sequence[str]) -> list[dict[str, Any]]:
    columns = [column for column in monitored_columns if column != ORDER_COLUMN]
    if not columns:
        return []
    sudden_target = columns[:1]
    gradual_target = columns[1:2] or sudden_target
    new_category_target = columns[2:3] or sudden_target
    return [
        {"type": "sudden_shift", "columns": sudden_target},
        {"type": "gradual_decay", "columns": gradual_target},
        {"type": "new_category", "columns": new_category_target},
    ]


def _sample_reference(df: pd.DataFrame, *, n_rows: int, seed: int) -> pd.DataFrame:
    if n_rows <= 0:
        raise ValueError("Benchmark sample size must be greater than zero.")
    if df.empty:
        raise ValueError("Benchmark reference data is empty.")
    if len(df) <= n_rows:
        sample = df.copy()
    else:
        sample = df.sample(n=n_rows, random_state=seed)
    sample = sample.reset_index(drop=True).copy()
    sample[ORDER_COLUMN] = range(len(sample))
    return sample


def _invalid_value(series: pd.Series) -> Any:
    if pd.api.types.is_numeric_dtype(series):
        return "INVALID"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "not-a-timestamp"
    if pd.api.types.is_bool_dtype(series):
        return "not-a-bool"
    return "__INVALID_VALUE__"


def _inject_quality_faults(
    clean_df: pd.DataFrame,
    *,
    quality_faults: Sequence[dict[str, Any]],
    business_key: Sequence[str],
    rng: np.random.Generator,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    faulted = clean_df.copy()
    manifest: dict[str, Any] = {
        "null_indices": {},
        "duplicate_indices": [],
        "type_error_indices": [],
    }

    total_rows = len(clean_df)

    for fault in quality_faults:
        fault_type = str(fault.get("type", "")).strip().lower()
        rate = float(fault.get("rate", 0.0) or 0.0)
        columns = [str(column) for column in fault.get("columns", [])]
        count = max(1, int(total_rows * rate)) if rate > 0 else 0

        if fault_type == "null_injection":
            for column in columns:
                if column not in faulted.columns or count == 0:
                    continue
                indices = sorted(int(i) for i in rng.choice(total_rows, size=count, replace=False).tolist())
                if pd.api.types.is_bool_dtype(faulted[column]):
                    faulted[column] = faulted[column].astype(object)
                faulted.loc[indices, column] = None
                manifest["null_indices"][column] = indices

        elif fault_type == "duplicate_inflation":
            if count == 0 or not business_key:
                continue
            indices = sorted(int(i) for i in rng.choice(total_rows, size=count, replace=False).tolist())
            duplicates = clean_df.iloc[indices].copy()
            faulted = pd.concat([faulted, duplicates], ignore_index=True)
            if ORDER_COLUMN in faulted.columns:
                start = total_rows
                faulted.loc[start:, ORDER_COLUMN] = range(start, len(faulted))
            manifest["duplicate_indices"] = indices

        elif fault_type == "type_corruption":
            for column in columns:
                if column not in faulted.columns or count == 0:
                    continue
                indices = sorted(int(i) for i in rng.choice(total_rows, size=count, replace=False).tolist())
                invalid = _invalid_value(faulted[column])
                faulted[column] = faulted[column].astype(object)
                faulted.loc[indices, column] = invalid
                manifest["type_error_indices"].extend(indices)

        elif fault_type == "schema_drop":
            for column in columns:
                if column in faulted.columns:
                    faulted = faulted.drop(columns=[column])
                    manifest["schema_dropped"] = column
                    break

    manifest["type_error_indices"] = sorted(set(int(i) for i in manifest["type_error_indices"]))
    manifest["faulted_row_indices"] = sorted(set(
        index
        for indices in manifest["null_indices"].values()
        for index in indices
    ) | set(manifest["type_error_indices"]))

    return faulted.reset_index(drop=True), manifest


def _inject_sudden_shift(
    df: pd.DataFrame,
    columns: Sequence[str],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    drifted = df.copy()
    affected: list[str] = []
    for column in columns:
        if column not in drifted.columns or column == ORDER_COLUMN:
            continue
        series = drifted[column]
        if pd.api.types.is_bool_dtype(series):
            drifted[column] = drifted[column].astype(object)
            dominant = series.dropna().mode()
            drifted[column] = str(dominant.iloc[0]) if not dominant.empty else "__SUDDEN_SHIFT__"
        elif pd.api.types.is_numeric_dtype(series):
            non_null = series.dropna()
            drifted[column] = float(non_null.median()) if not non_null.empty else 0.0
        else:
            dominant = series.dropna().mode()
            drifted[column] = str(dominant.iloc[0]) if not dominant.empty else "__SUDDEN_SHIFT__"
        affected.append(column)
    return drifted, {"type": "sudden", "columns": affected}


def _inject_gradual_decay(
    df: pd.DataFrame,
    columns: Sequence[str],
    *,
    rng: np.random.Generator,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    drifted = df.copy()
    affected: list[str] = []
    changed_rows: dict[str, int] = {}

    for column in columns:
        if column not in drifted.columns or column == ORDER_COLUMN:
            continue
        affected.append(column)
        if pd.api.types.is_bool_dtype(drifted[column]):
            drifted[column] = drifted[column].astype(object)
        if pd.api.types.is_numeric_dtype(drifted[column]) and not pd.api.types.is_bool_dtype(drifted[column]):
            delta = pd.Series(np.linspace(0.0, 1.5, num=len(drifted)), index=drifted.index)
            drifted[column] = pd.to_numeric(drifted[column], errors="coerce").fillna(0) + delta
            changed_rows[column] = int(len(drifted))
            continue

        values = drifted[column].dropna().tolist()
        target = str(values[-1]) if values else "__GRADUAL_SHIFT__"
        probabilities = np.arange(len(drifted)) / max(len(drifted) - 1, 1)
        mask = pd.Series(rng.random(len(drifted)) < probabilities, index=drifted.index)
        drifted.loc[mask, column] = target
        changed_rows[column] = int(mask.sum())

    return drifted, {"type": "gradual", "columns": affected, "changed_rows": changed_rows}


def _inject_new_category(
    df: pd.DataFrame,
    columns: Sequence[str],
    *,
    rng: np.random.Generator,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    drifted = df.copy()
    affected: list[str] = []
    count = max(1, int(len(drifted) * 0.15))
    indices = sorted(int(i) for i in rng.choice(len(drifted), size=count, replace=False).tolist())

    for column in columns:
        if column not in drifted.columns or column == ORDER_COLUMN:
            continue
        affected.append(column)
        if pd.api.types.is_bool_dtype(drifted[column]):
            drifted[column] = drifted[column].astype(object)
            drifted.loc[indices, column] = "__NEW_CATEGORY__"
        elif pd.api.types.is_numeric_dtype(drifted[column]):
            base = pd.to_numeric(drifted[column], errors="coerce").max()
            next_value = float(base) + 9999 if pd.notna(base) else 9999.0
            drifted.loc[indices, column] = next_value
        else:
            drifted.loc[indices, column] = "__NEW_CATEGORY__"

    return drifted, {"type": "new_category", "columns": affected, "count": count}


def build_reference_dataset(
    reference_df: pd.DataFrame,
    *,
    seed: int,
    n_rows: int,
    business_key: Sequence[str],
    monitored_columns: Sequence[str],
    quality_faults: Sequence[dict[str, Any]] | None = None,
    drift_patterns: Sequence[dict[str, Any]] | None = None,
) -> GeneratedDataset:
    """Build deterministic benchmark scenarios from a real reference DataFrame."""
    clean = _sample_reference(reference_df, n_rows=n_rows, seed=seed)
    rng = np.random.default_rng(seed)
    gradual_rng = np.random.default_rng(seed + 10)
    newcat_rng = np.random.default_rng(seed + 20)

    resolved_quality_faults = list(quality_faults or _default_quality_faults(clean, business_key))
    resolved_drift_patterns = list(drift_patterns or _default_drift_patterns(monitored_columns))

    faulted, fault_manifest = _inject_quality_faults(
        clean,
        quality_faults=resolved_quality_faults,
        business_key=business_key,
        rng=rng,
    )

    sudden_df = clean.copy()
    gradual_df = clean.copy()
    newcat_df = clean.copy()
    drift_manifest: dict[str, Any] = {}

    for pattern in resolved_drift_patterns:
        pattern_type = str(pattern.get("type", "")).strip().lower()
        columns = [str(column) for column in pattern.get("columns", [])]
        if pattern_type == "sudden_shift":
            sudden_df, drift_manifest["sudden"] = _inject_sudden_shift(sudden_df, columns)
        elif pattern_type == "gradual_decay":
            gradual_df, drift_manifest["gradual"] = _inject_gradual_decay(
                gradual_df, columns, rng=gradual_rng
            )
        elif pattern_type == "new_category":
            newcat_df, drift_manifest["new_category"] = _inject_new_category(
                newcat_df, columns, rng=newcat_rng
            )

    drift_manifest.setdefault("sudden", {"type": "sudden", "columns": []})
    drift_manifest.setdefault("gradual", {"type": "gradual", "columns": []})
    drift_manifest.setdefault("new_category", {"type": "new_category", "columns": []})

    return GeneratedDataset(
        clean_df=clean.reset_index(drop=True),
        faulted_df=faulted.reset_index(drop=True),
        drifted_sudden_df=sudden_df.reset_index(drop=True),
        drifted_gradual_df=gradual_df.reset_index(drop=True),
        drifted_new_cat_df=newcat_df.reset_index(drop=True),
        stable_df=clean.copy().reset_index(drop=True),
        fault_manifest=fault_manifest,
        drift_manifest=drift_manifest,
    )
