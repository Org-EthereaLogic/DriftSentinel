"""Baseline snapshot -- captures per-column stability scores from a trusted load.

Ported from Chapter 2 (silent-failure-prevention) as first-party DriftSentinel code.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from driftsentinel.drift.entropy import column_stability_score


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

    @classmethod
    def from_dataframe(cls, df: pd.DataFrame, columns: list[str]) -> "BaselineSnapshot":
        """Create a baseline snapshot from a DataFrame and list of columns to monitor."""
        scores: dict[str, float] = {}
        for col in columns:
            if col in df.columns:
                scores[col] = column_stability_score(df[col])
            else:
                scores[col] = 0.0
        return cls(
            scores=scores,
            row_count=len(df),
            columns=tuple(columns),
        )
