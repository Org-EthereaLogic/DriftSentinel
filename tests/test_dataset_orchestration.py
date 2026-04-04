"""Tests for Phase 3 dataset-aware orchestration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from driftsentinel.config.loader import DatasetRegistry, RegistryError
from driftsentinel.orchestration import dataset_runtime
from driftsentinel.orchestration.runner import run_dataset_pipeline

FIXED_TS = "2026-04-02T00:00:00+00:00"


def _make_contract(
    landing_path: str,
    name: str = "test_ds",
    version: str = "1.0.0",
) -> dict[str, Any]:
    return {
        "dataset": {
            "name": name,
            "contract_version": version,
            "catalog": "cat",
            "schema": "sch",
            "table": "tbl",
        },
        "source": {
            "system": "pytest",
            "format": "csv",
            "landing_path": landing_path,
        },
        "contract": {
            "required_columns": [{"column_name": "id", "type": "long", "nullable": False}],
            "business_key": ["id"],
            "batch_identifier": "batch_id",
        },
    }


def _make_drift_policy(
    baseline_path: str,
    dataset: str = "test_ds",
    contract_version: str = "1.0.0",
    policy_version: str = "1.0.0",
    baseline_format: str = "csv",
) -> dict[str, Any]:
    return {
        "drift_policy": {
            "name": f"{dataset}_drift",
            "dataset": dataset,
            "contract_version": contract_version,
            "policy_version": policy_version,
            "monitored_columns": [{"column_name": "amount", "method": "shannon_entropy"}],
            "baseline": {"path": baseline_path, "format": baseline_format, "min_rows": 1},
            "gates": {"health_score_threshold": 0.70, "max_columns_failed": 1},
        },
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> str:
    pd.DataFrame(rows).to_csv(path, index=False)
    return str(path)


def _dataset_files(tmp_path: Path, name: str) -> tuple[str, str]:
    current_path = tmp_path / f"{name}_current.csv"
    baseline_path = tmp_path / f"{name}_baseline.csv"
    _write_csv(
        baseline_path,
        [
            {"id": 1, "batch_id": "B-1", "amount": 10.0},
            {"id": 2, "batch_id": "B-1", "amount": 20.0},
            {"id": 3, "batch_id": "B-1", "amount": 30.0},
            {"id": 4, "batch_id": "B-1", "amount": 40.0},
        ],
    )
    _write_csv(
        current_path,
        [
            {"id": 1, "batch_id": "B-2", "amount": 10.0},
            {"id": 2, "batch_id": "B-2", "amount": 20.0},
            {"id": 3, "batch_id": "B-2", "amount": 20.0},
            {"id": 4, "batch_id": "B-2", "amount": 20.0},
        ],
    )
    return str(current_path), str(baseline_path)


class TestDatasetPipeline:
    def test_runs_for_registered_dataset(self, tmp_path: Path) -> None:
        current_path, baseline_path = _dataset_files(tmp_path, "ds_a")
        reg = DatasetRegistry()
        reg.register(_make_contract(current_path, "ds_a", "1.0.0"))
        result = run_dataset_pipeline(
            reg,
            "ds_a",
            drift_policy=_make_drift_policy(baseline_path, "ds_a", "1.0.0"),
            run_ts=FIXED_TS,
            run_id="test-run-1",
        )
        assert result["dataset_id"] == "ds_a"
        assert result["contract_version"] == "1.0.0"
        assert result["run_id"] == "test-run-1"
        assert result["execution_mode"] == "dataset_backed"
        assert "intake" in result
        assert "drift" in result
        assert "benchmark" in result

    def test_rejects_unregistered_dataset(self, tmp_path: Path) -> None:
        _, baseline_path = _dataset_files(tmp_path, "ds_missing")
        reg = DatasetRegistry()
        with pytest.raises(RegistryError, match="not registered"):
            run_dataset_pipeline(
                reg,
                "ds_nonexistent",
                drift_policy=_make_drift_policy(baseline_path, "ds_nonexistent", "1.0.0"),
                run_ts=FIXED_TS,
            )

    def test_rejects_missing_drift_policy(self, tmp_path: Path) -> None:
        current_path, _ = _dataset_files(tmp_path, "ds_a")
        reg = DatasetRegistry()
        reg.register(_make_contract(current_path, "ds_a", "1.0.0"))
        with pytest.raises(ValueError, match="requires a drift policy"):
            run_dataset_pipeline(reg, "ds_a", run_ts=FIXED_TS)

    def test_writes_evidence_with_metadata(self, tmp_path: Path) -> None:
        current_path, baseline_path = _dataset_files(tmp_path, "ds_a")
        reg = DatasetRegistry()
        reg.register(_make_contract(current_path, "ds_a", "1.0.0"))
        run_dataset_pipeline(
            reg,
            "ds_a",
            evidence_dir=tmp_path,
            drift_policy=_make_drift_policy(baseline_path, "ds_a", "1.0.0"),
            run_ts=FIXED_TS,
            run_id="test-run-2",
        )
        files = list(tmp_path.glob("pipeline_ds_a*.json"))
        assert len(files) >= 1
        data = json.loads(files[0].read_text())
        assert data["meta"]["dataset_id"] == "ds_a"
        assert data["meta"]["run_id"] == "test-run-2"
        assert data["meta"]["run_kind"] == "pipeline"

    def test_benchmark_evidence_carries_dataset_metadata(self, tmp_path: Path) -> None:
        current_path, baseline_path = _dataset_files(tmp_path, "ds_a")
        reg = DatasetRegistry()
        reg.register(_make_contract(current_path, "ds_a", "1.0.0"))
        run_dataset_pipeline(
            reg,
            "ds_a",
            evidence_dir=tmp_path,
            drift_policy=_make_drift_policy(baseline_path, "ds_a", "1.0.0"),
            run_ts=FIXED_TS,
            run_id="test-run-bench",
        )
        bench_files = list(tmp_path.glob("bench_*.json"))
        assert len(bench_files) >= 1
        data = json.loads(bench_files[0].read_text())
        assert data["meta"]["dataset_id"] == "ds_a"
        assert data["meta"]["contract_version"] == "1.0.0"
        assert data["meta"]["run_id"] == "test-run-bench"
        assert data["meta"]["run_kind"] == "benchmark"

    def test_with_compatible_drift_policy(self, tmp_path: Path) -> None:
        current_path, baseline_path = _dataset_files(tmp_path, "ds_a")
        reg = DatasetRegistry()
        reg.register(_make_contract(current_path, "ds_a", "1.0.0"))
        policy = _make_drift_policy(baseline_path, "ds_a", "1.0.0", "2.0.0")
        result = run_dataset_pipeline(
            reg,
            "ds_a",
            drift_policy=policy,
            run_ts=FIXED_TS,
        )
        assert result["drift_policy_version"] == "2.0.0"

    def test_rejects_incompatible_drift_policy(self, tmp_path: Path) -> None:
        current_path, baseline_path = _dataset_files(tmp_path, "ds_a")
        reg = DatasetRegistry()
        reg.register(_make_contract(current_path, "ds_a", "1.0.0"))
        policy = _make_drift_policy(baseline_path, "ds_a", "9.0.0", "1.0.0")
        with pytest.raises(RegistryError, match="version '9.0.0'"):
            run_dataset_pipeline(reg, "ds_a", drift_policy=policy, run_ts=FIXED_TS)

    def test_rejects_current_data_that_fails_contract(self, tmp_path: Path) -> None:
        current_path = tmp_path / "ds_bad_current.csv"
        baseline_path = tmp_path / "ds_bad_baseline.csv"
        _write_csv(baseline_path, [{"id": 1, "batch_id": "B-1", "amount": 10.0}])
        pd.DataFrame([{"id": "", "batch_id": "B-2", "amount": 10.0}]).to_csv(current_path, index=False)
        reg = DatasetRegistry()
        reg.register(_make_contract(str(current_path), "ds_bad", "1.0.0"))

        with pytest.raises(ValueError, match="Current dataset does not satisfy the registered contract"):
            run_dataset_pipeline(
                reg,
                "ds_bad",
                drift_policy=_make_drift_policy(str(baseline_path), "ds_bad", "1.0.0"),
                run_ts=FIXED_TS,
            )

    def test_multiple_datasets_independent(self, tmp_path: Path) -> None:
        current_a, baseline_a = _dataset_files(tmp_path, "ds_a")
        current_b, baseline_b = _dataset_files(tmp_path, "ds_b")
        reg = DatasetRegistry()
        reg.register(_make_contract(current_a, "ds_a", "1.0.0"))
        reg.register(_make_contract(current_b, "ds_b", "1.0.0"))
        r_a = run_dataset_pipeline(
            reg,
            "ds_a",
            evidence_dir=tmp_path,
            drift_policy=_make_drift_policy(baseline_a, "ds_a", "1.0.0"),
            run_ts=FIXED_TS,
            run_id="run-a",
        )
        r_b = run_dataset_pipeline(
            reg,
            "ds_b",
            evidence_dir=tmp_path,
            drift_policy=_make_drift_policy(baseline_b, "ds_b", "1.0.0"),
            run_ts=FIXED_TS,
            run_id="run-b",
        )
        assert r_a["dataset_id"] == "ds_a"
        assert r_b["dataset_id"] == "ds_b"
        assert r_a["run_id"] != r_b["run_id"]
        files = list(tmp_path.glob("*.json"))
        assert len(files) >= 2

    def test_runs_pipeline_for_table_backed_dataset(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        baseline_table_name = "adb_dev.default.orders_baseline"
        current_table_name = "adb_dev.default.orders_current"
        reg = DatasetRegistry()
        reg.register({
            "dataset": {
                "name": "orders",
                "contract_version": "1.0.0",
                "catalog": "adb_dev",
                "schema": "default",
                "table": "orders_current",
            },
            "source": {
                "system": "pytest",
                "format": "table",
                "table_name": current_table_name,
            },
            "contract": {
                "required_columns": [{"column_name": "id", "type": "long", "nullable": False}],
                "business_key": ["id"],
                "batch_identifier": "batch_id",
            },
        })

        current_df = pd.DataFrame([
            {"id": 1, "batch_id": "B-2", "amount": 10.0},
            {"id": 2, "batch_id": "B-2", "amount": 20.0},
            {"id": 3, "batch_id": "B-2", "amount": 20.0},
            {"id": 4, "batch_id": "B-2", "amount": 20.0},
        ])
        baseline_df = pd.DataFrame([
            {"id": 1, "batch_id": "B-1", "amount": 10.0},
            {"id": 2, "batch_id": "B-1", "amount": 20.0},
            {"id": 3, "batch_id": "B-1", "amount": 30.0},
            {"id": 4, "batch_id": "B-1", "amount": 40.0},
        ])

        class FakeSparkFrame:
            def __init__(self, frame: pd.DataFrame) -> None:
                self._frame = frame

            def toPandas(self) -> pd.DataFrame:
                return self._frame.copy()

        class FakeSparkSession:
            def table(self, table_name: str) -> FakeSparkFrame:
                if table_name == current_table_name:
                    return FakeSparkFrame(current_df)
                if table_name == baseline_table_name:
                    return FakeSparkFrame(baseline_df)
                raise AssertionError(table_name)

        monkeypatch.setattr(dataset_runtime, "_active_spark_session", lambda: FakeSparkSession())
        drift_policy = _make_drift_policy(
            baseline_table_name,
            dataset="orders",
            contract_version="1.0.0",
            baseline_format="table",
        )

        result = run_dataset_pipeline(
            reg,
            "orders",
            evidence_dir=tmp_path,
            drift_policy=drift_policy,
            run_ts=FIXED_TS,
            run_id="table-run-1",
        )

        assert result["execution_mode"] == "dataset_backed"
        assert result["current_source"]["format"] == "table"
        assert result["baseline_source"]["path"] == baseline_table_name


class TestDemoBehaviorPreserved:
    def test_demo_pipeline_still_deterministic(self, tmp_path: Path) -> None:
        from driftsentinel.orchestration.runner import run_local_pipeline
        r1 = run_local_pipeline(run_ts=FIXED_TS)
        r2 = run_local_pipeline(run_ts=FIXED_TS)
        assert r1 == r2
