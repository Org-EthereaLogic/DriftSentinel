"""Tests for trusted dataset loading used by dataset-backed orchestration."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from deltalake import write_deltalake

from driftsentinel.orchestration.dataset_runtime import (
    load_baseline_dataset,
    load_current_dataset,
    load_tabular_dataset,
)


def _contract(path: str) -> dict[str, object]:
    return {
        "dataset": {"name": "runtime_ds", "contract_version": "1.0.0"},
        "source": {
            "system": "pytest",
            "format": "csv",
            "landing_path": path,
        },
        "contract": {
            "required_columns": [{"column_name": "id", "type": "long", "nullable": False}],
            "business_key": ["id"],
            "batch_identifier": "batch_id",
        },
    }


def test_load_current_dataset_csv(tmp_path: Path) -> None:
    path = tmp_path / "current.csv"
    pd.DataFrame([
        {"id": 1, "batch_id": "B-1", "amount": 10.0},
        {"id": 2, "batch_id": "B-1", "amount": 11.0},
    ]).to_csv(path, index=False)

    loaded = load_current_dataset(_contract(str(path)))

    assert loaded.source_format == "csv"
    assert loaded.frame.shape == (2, 3)
    assert loaded.files_loaded == (str(path),)


def test_load_tabular_dataset_parquet(tmp_path: Path) -> None:
    path = tmp_path / "baseline.parquet"
    expected = pd.DataFrame([
        {"id": 1, "batch_id": "B-1", "amount": 10.0},
        {"id": 2, "batch_id": "B-1", "amount": 11.0},
    ])
    expected.to_parquet(path, index=False)

    loaded = load_tabular_dataset(path, "parquet", context="Test parquet path")

    assert loaded.source_format == "parquet"
    assert loaded.frame.equals(expected)


def test_load_tabular_dataset_delta(tmp_path: Path) -> None:
    path = tmp_path / "delta_table"
    expected = pd.DataFrame([
        {"id": 1, "batch_id": "B-1", "amount": 10.0},
        {"id": 2, "batch_id": "B-1", "amount": 11.0},
    ])
    write_deltalake(str(path), expected, mode="overwrite")

    loaded = load_tabular_dataset(path, "delta", context="Test delta path")

    assert loaded.source_format == "delta"
    assert loaded.frame.equals(expected)


def test_load_baseline_dataset_from_policy_path(tmp_path: Path) -> None:
    current_path = tmp_path / "current.csv"
    baseline_path = tmp_path / "baseline.csv"
    pd.DataFrame([{"id": 1, "batch_id": "B-1"}]).to_csv(current_path, index=False)
    pd.DataFrame([{"id": 2, "batch_id": "B-0"}]).to_csv(baseline_path, index=False)

    contract = _contract(str(current_path))
    drift_policy = {
        "drift_policy": {
            "dataset": "runtime_ds",
            "contract_version": "1.0.0",
            "policy_version": "1.0.0",
            "name": "runtime_ds_drift",
            "monitored_columns": [{"column_name": "id", "method": "shannon_entropy"}],
            "baseline": {"path": str(baseline_path), "format": "csv", "min_rows": 1},
            "gates": {"health_score_threshold": 0.70},
        }
    }

    loaded = load_baseline_dataset(contract, drift_policy)

    assert loaded.source_path == str(baseline_path)
    assert loaded.frame.iloc[0]["id"] == 2
