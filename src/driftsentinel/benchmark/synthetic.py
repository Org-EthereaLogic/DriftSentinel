"""Deterministic synthetic data generation with controlled fault and drift injection.

Every generated dataset carries a manifest of exactly what was injected,
enabling ground-truth scoring without heuristics.

Ported from Chapter 3 (measurable-control-effectiveness) as first-party DriftSentinel code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class FaultProfile:
    """Defines quality fault injection parameters."""

    null_rate: float = 0.05
    null_columns: tuple[str, ...] = ("customer_id", "amount")
    duplicate_rate: float = 0.03
    type_error_rate: float = 0.02
    type_error_column: str = "amount"
    schema_drop_column: str | None = "priority"


@dataclass(frozen=True)
class DriftProfile:
    """Defines drift injection parameters."""

    sudden_shift_column: str = "department"
    sudden_shift_value: str = "Engineering"
    gradual_column: str = "region"
    gradual_target: str = "West"
    gradual_strength: float = 0.7
    new_category_column: str = "status"
    new_category_value: str = "Archived"
    new_category_rate: float = 0.15


@dataclass
class GeneratedDataset:
    """Container for a generated dataset with its injection manifest."""

    clean_df: pd.DataFrame
    faulted_df: pd.DataFrame
    drifted_sudden_df: pd.DataFrame
    drifted_gradual_df: pd.DataFrame
    drifted_new_cat_df: pd.DataFrame
    stable_df: pd.DataFrame
    fault_manifest: dict[str, Any] = field(default_factory=dict)
    drift_manifest: dict[str, Any] = field(default_factory=dict)


_DEPARTMENTS = ["Engineering", "Sales", "Marketing", "Finance", "Operations"]
_REGIONS = ["West", "East", "Central", "South", "North"]
_CATEGORIES = ["Enterprise", "Mid-Market", "SMB", "Startup", "Government"]
_STATUSES = ["Active", "Pending", "Review", "Approved", "Closed"]
_PRIORITIES = ["Critical", "High", "Medium", "Low", "Deferred"]


def _make_clean(rng: np.random.Generator, n_rows: int) -> pd.DataFrame:
    """Generate a clean baseline dataset with uniform distributions."""
    return pd.DataFrame({
        "record_id": [f"REC-{i:05d}" for i in range(n_rows)],
        "customer_id": [f"CUST-{rng.integers(1000, 9999)}" for _ in range(n_rows)],
        "department": [_DEPARTMENTS[i % 5] for i in range(n_rows)],
        "region": [_REGIONS[i % 5] for i in range(n_rows)],
        "product_category": [_CATEGORIES[i % 5] for i in range(n_rows)],
        "status": [_STATUSES[i % 5] for i in range(n_rows)],
        "priority": [_PRIORITIES[i % 5] for i in range(n_rows)],
        "amount": rng.uniform(10.0, 500.0, size=n_rows).round(2),
        "row_order": list(range(n_rows)),
    })


def _inject_faults(
    df: pd.DataFrame,
    rng: np.random.Generator,
    profile: FaultProfile,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Inject quality faults and return the faulted df + manifest."""
    faulted = df.copy()
    manifest: dict[str, Any] = {"null_indices": {}, "duplicate_indices": [], "type_error_indices": []}

    n = len(faulted)

    for col in profile.null_columns:
        n_nulls = max(1, int(n * profile.null_rate))
        indices = rng.choice(n, size=n_nulls, replace=False).tolist()
        faulted.loc[indices, col] = None
        manifest["null_indices"][col] = sorted(indices)

    n_dups = max(1, int(n * profile.duplicate_rate))
    dup_indices = rng.choice(n, size=n_dups, replace=False).tolist()
    dup_rows = faulted.iloc[dup_indices].copy()
    faulted = pd.concat([faulted, dup_rows], ignore_index=True)
    manifest["duplicate_indices"] = sorted(dup_indices)

    n_type = max(1, int(n * profile.type_error_rate))
    type_indices = rng.choice(n, size=n_type, replace=False).tolist()
    faulted[profile.type_error_column] = faulted[profile.type_error_column].astype(object)
    faulted.loc[type_indices, profile.type_error_column] = "INVALID"
    manifest["type_error_indices"] = sorted(type_indices)

    if profile.schema_drop_column and profile.schema_drop_column in faulted.columns:
        faulted = faulted.drop(columns=[profile.schema_drop_column])
        manifest["schema_dropped"] = profile.schema_drop_column

    manifest["faulted_row_indices"] = sorted(set(
        [i for indices in manifest["null_indices"].values() for i in indices]
        + manifest["type_error_indices"]
    ))

    return faulted, manifest


def _inject_sudden_drift(
    df: pd.DataFrame,
    profile: DriftProfile,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Inject sudden distribution shift -- collapse a column to one value."""
    drifted = df.copy()
    drifted[profile.sudden_shift_column] = profile.sudden_shift_value
    return drifted, {"type": "sudden", "column": profile.sudden_shift_column}


def _inject_gradual_drift(
    df: pd.DataFrame,
    rng: np.random.Generator,
    profile: DriftProfile,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Inject gradual drift -- progressively shift distribution toward target."""
    drifted = df.copy()
    n = len(drifted)
    col = profile.gradual_column
    changed_indices: list[int] = []

    for i in range(n):
        prob = profile.gradual_strength * (i / max(n - 1, 1))
        if rng.random() < prob:
            drifted.at[i, col] = profile.gradual_target
            changed_indices.append(i)

    return drifted, {
        "type": "gradual",
        "column": col,
        "target": profile.gradual_target,
        "changed_count": len(changed_indices),
        "total_rows": n,
    }


def _inject_new_category(
    df: pd.DataFrame,
    rng: np.random.Generator,
    profile: DriftProfile,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Inject new category values into a column."""
    drifted = df.copy()
    n = len(drifted)
    col = profile.new_category_column
    n_new = max(1, int(n * profile.new_category_rate))
    indices = rng.choice(n, size=n_new, replace=False).tolist()
    drifted.loc[indices, col] = profile.new_category_value
    return drifted, {
        "type": "new_category",
        "column": col,
        "new_value": profile.new_category_value,
        "count": n_new,
    }


def generate_dataset(
    seed: int = 42,
    n_rows: int = 1000,
    fault_profile: FaultProfile | None = None,
    drift_profile: DriftProfile | None = None,
) -> GeneratedDataset:
    """Generate a complete benchmark dataset with controlled injections."""
    rng = np.random.default_rng(seed)

    if fault_profile is None:
        fault_profile = FaultProfile()
    if drift_profile is None:
        drift_profile = DriftProfile()

    clean = _make_clean(rng, n_rows)
    stable = _make_clean(np.random.default_rng(seed + 1), n_rows)

    faulted, fault_manifest = _inject_faults(clean.copy(), rng, fault_profile)

    sudden, sudden_manifest = _inject_sudden_drift(clean.copy(), drift_profile)

    gradual_rng = np.random.default_rng(seed + 10)
    gradual, gradual_manifest = _inject_gradual_drift(
        clean.copy(), gradual_rng, drift_profile
    )

    new_cat_rng = np.random.default_rng(seed + 20)
    new_cat, new_cat_manifest = _inject_new_category(
        clean.copy(), new_cat_rng, drift_profile
    )

    return GeneratedDataset(
        clean_df=clean,
        faulted_df=faulted,
        drifted_sudden_df=sudden,
        drifted_gradual_df=gradual,
        drifted_new_cat_df=new_cat,
        stable_df=stable,
        fault_manifest=fault_manifest,
        drift_manifest={
            "sudden": sudden_manifest,
            "gradual": gradual_manifest,
            "new_category": new_cat_manifest,
        },
    )
