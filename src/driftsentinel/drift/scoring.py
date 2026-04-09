"""Method-aware scoring helpers for drift detection."""

from __future__ import annotations

from enum import Enum

import numpy as np
import pandas as pd
from pandas.api.types import is_bool_dtype, is_datetime64_any_dtype, is_numeric_dtype

from driftsentinel.drift.entropy import column_stability_score


class DriftMethod(str, Enum):
    """Supported drift scoring methods."""

    SHANNON_ENTROPY = "shannon_entropy"
    WASSERSTEIN = "wasserstein"


SUPPORTED_DRIFT_METHODS = tuple(method.value for method in DriftMethod)


def normalize_drift_method(value: object) -> DriftMethod:
    """Normalize a drift method string into a supported enum value."""
    if isinstance(value, DriftMethod):
        return value
    normalized = str(value or DriftMethod.SHANNON_ENTROPY.value).strip().lower()
    try:
        return DriftMethod(normalized)
    except ValueError as exc:
        supported = ", ".join(SUPPORTED_DRIFT_METHODS)
        raise ValueError(f"Unsupported drift method '{value}'. Supported methods: {supported}.") from exc


def baseline_stability_score(
    series: pd.Series,  # type: ignore[type-arg]
    *,
    method: DriftMethod | str,
) -> float:
    """Return the baseline score recorded for a monitored column."""
    resolved = normalize_drift_method(method)
    if resolved is DriftMethod.SHANNON_ENTROPY:
        return column_stability_score(series)
    _numeric_values(series, allow_empty=False)
    return 1.0


def drift_stability_score(
    current_series: pd.Series,  # type: ignore[type-arg]
    *,
    method: DriftMethod | str,
    reference_series: pd.Series | None = None,  # type: ignore[type-arg]
) -> float:
    """Return a normalized stability score for the current column distribution."""
    resolved = normalize_drift_method(method)
    if resolved is DriftMethod.SHANNON_ENTROPY:
        return column_stability_score(current_series)
    if reference_series is None:
        raise ValueError("Wasserstein drift scoring requires a reference baseline series.")
    return _wasserstein_stability_score(reference_series, current_series)


def _numeric_values(
    series: pd.Series,  # type: ignore[type-arg]
    *,
    allow_empty: bool,
) -> np.ndarray:
    non_null = series.dropna()
    if non_null.empty:
        if allow_empty:
            return np.array([], dtype=float)
        raise ValueError("Wasserstein drift scoring requires at least one non-null value.")

    if is_datetime64_any_dtype(non_null):
        values = non_null.astype("int64").to_numpy(dtype=float, copy=False)
    elif is_numeric_dtype(non_null) or is_bool_dtype(non_null):
        values = non_null.to_numpy(dtype=float, copy=False)
    else:
        raise ValueError(
            "Wasserstein drift scoring requires numeric or datetime columns; "
            f"received dtype {series.dtype}."
        )

    if not np.isfinite(values).all():
        raise ValueError("Wasserstein drift scoring requires finite numeric values.")

    return np.sort(values)


def _wasserstein_stability_score(
    reference_series: pd.Series,  # type: ignore[type-arg]
    current_series: pd.Series,  # type: ignore[type-arg]
) -> float:
    reference = _numeric_values(reference_series, allow_empty=False)
    current = _numeric_values(current_series, allow_empty=True)
    if current.size == 0:
        return 0.0

    support = np.sort(np.concatenate((reference, current)))
    if support.size <= 1:
        return 1.0

    deltas = np.diff(support)
    if deltas.size == 0 or float(deltas.max()) == 0.0:
        return 1.0

    ref_cdf = np.searchsorted(reference, support[:-1], side="right") / reference.size
    cur_cdf = np.searchsorted(current, support[:-1], side="right") / current.size
    distance = float(np.sum(np.abs(ref_cdf - cur_cdf) * deltas))

    scale = float(support[-1] - support[0])
    if scale <= 0.0:
        return 1.0 if distance == 0.0 else 0.0

    return max(0.0, round(1.0 - min(distance / scale, 1.0), 4))
