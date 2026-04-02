"""Tests for Phase 3 dataset-aware orchestration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from driftsentinel.config.loader import DatasetRegistry, RegistryError
from driftsentinel.orchestration.runner import run_dataset_pipeline

FIXED_TS = "2026-04-02T00:00:00+00:00"


def _make_contract(
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
        "contract": {
            "required_columns": [{"column_name": "id", "type": "long", "nullable": False}],
            "business_key": ["id"],
            "batch_identifier": "batch_id",
        },
    }


def _make_drift_policy(
    dataset: str = "test_ds",
    contract_version: str = "1.0.0",
    policy_version: str = "1.0.0",
) -> dict[str, Any]:
    return {
        "drift_policy": {
            "name": f"{dataset}_drift",
            "dataset": dataset,
            "contract_version": contract_version,
            "policy_version": policy_version,
            "monitored_columns": [{"column_name": "amt", "method": "shannon_entropy"}],
            "gates": {"health_score_threshold": 0.70},
        },
    }


class TestDatasetPipeline:
    def test_runs_for_registered_dataset(self, tmp_path: Path) -> None:
        reg = DatasetRegistry()
        reg.register(_make_contract("ds_a", "1.0.0"))
        result = run_dataset_pipeline(
            reg, "ds_a", run_ts=FIXED_TS, run_id="test-run-1",
        )
        assert result["dataset_id"] == "ds_a"
        assert result["contract_version"] == "1.0.0"
        assert result["run_id"] == "test-run-1"
        assert "intake" in result
        assert "drift" in result
        assert "benchmark" in result

    def test_rejects_unregistered_dataset(self) -> None:
        reg = DatasetRegistry()
        with pytest.raises(RegistryError, match="not registered"):
            run_dataset_pipeline(reg, "ds_nonexistent", run_ts=FIXED_TS)

    def test_writes_evidence_with_metadata(self, tmp_path: Path) -> None:
        reg = DatasetRegistry()
        reg.register(_make_contract("ds_a", "1.0.0"))
        run_dataset_pipeline(
            reg, "ds_a",
            evidence_dir=tmp_path,
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
        reg = DatasetRegistry()
        reg.register(_make_contract("ds_a", "1.0.0"))
        run_dataset_pipeline(
            reg, "ds_a",
            evidence_dir=tmp_path,
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
        reg = DatasetRegistry()
        reg.register(_make_contract("ds_a", "1.0.0"))
        policy = _make_drift_policy("ds_a", "1.0.0", "2.0.0")
        result = run_dataset_pipeline(
            reg, "ds_a",
            drift_policy=policy,
            run_ts=FIXED_TS,
        )
        assert result["drift_policy_version"] == "2.0.0"

    def test_rejects_incompatible_drift_policy(self) -> None:
        reg = DatasetRegistry()
        reg.register(_make_contract("ds_a", "1.0.0"))
        policy = _make_drift_policy("ds_a", "9.0.0", "1.0.0")
        with pytest.raises(RegistryError, match="version '9.0.0'"):
            run_dataset_pipeline(reg, "ds_a", drift_policy=policy, run_ts=FIXED_TS)

    def test_multiple_datasets_independent(self, tmp_path: Path) -> None:
        reg = DatasetRegistry()
        reg.register(_make_contract("ds_a", "1.0.0"))
        reg.register(_make_contract("ds_b", "1.0.0"))
        r_a = run_dataset_pipeline(
            reg, "ds_a", evidence_dir=tmp_path, run_ts=FIXED_TS, run_id="run-a",
        )
        r_b = run_dataset_pipeline(
            reg, "ds_b", evidence_dir=tmp_path, run_ts=FIXED_TS, run_id="run-b",
        )
        assert r_a["dataset_id"] == "ds_a"
        assert r_b["dataset_id"] == "ds_b"
        assert r_a["run_id"] != r_b["run_id"]
        files = list(tmp_path.glob("*.json"))
        assert len(files) >= 2


class TestDemoBehaviorPreserved:
    def test_demo_pipeline_still_deterministic(self, tmp_path: Path) -> None:
        from driftsentinel.orchestration.runner import run_local_pipeline
        r1 = run_local_pipeline(run_ts=FIXED_TS)
        r2 = run_local_pipeline(run_ts=FIXED_TS)
        assert r1 == r2
