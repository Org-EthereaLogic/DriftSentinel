"""Baseline snapshot -- captures per-column stability scores from a trusted load.

Ported from Chapter 2 (silent-failure-prevention) as first-party DriftSentinel code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

import pandas as pd

from driftsentinel.drift.scoring import DriftMethod, baseline_stability_score, normalize_drift_method


@dataclass(frozen=True)
class BaselineSnapshot:
    """Immutable record of per-column stability scores from a trusted load.

    Attributes:
        scores: Mapping of column name to normalized stability score [0.0, 1.0].
        row_count: Number of rows in the baseline.
        columns: Ordered list of monitored column names.
    """

    scores: dict[str, float] = field(default_factory=dict)
    row_count: int = 0
    columns: tuple[str, ...] = ()
    methods: dict[str, DriftMethod] = field(default_factory=dict)

    @classmethod
    def from_dataframe(
        cls,
        df: pd.DataFrame,
        columns: list[str],
        *,
        methods: Mapping[str, DriftMethod | str] | None = None,
    ) -> "BaselineSnapshot":
        """Create a baseline snapshot from a DataFrame and list of columns to monitor."""
        scores: dict[str, float] = {}
        resolved_methods: dict[str, DriftMethod] = {}
        for col in columns:
            method = normalize_drift_method(
                (methods or {}).get(col, DriftMethod.SHANNON_ENTROPY.value)
            )
            resolved_methods[col] = method
            if col in df.columns:
                scores[col] = baseline_stability_score(df[col], method=method)
            else:
                scores[col] = 0.0
        return cls(
            scores=scores,
            row_count=len(df),
            columns=tuple(columns),
            methods=resolved_methods,
        )
