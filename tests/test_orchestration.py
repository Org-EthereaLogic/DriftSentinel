"""Tests for the minimal Phase 1 orchestration layer.

Verifies that the local pipeline connects all three domains
and produces deterministic results.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from driftsentinel.orchestration.runner import (
    _validate_dataset_readiness,
    run_drift_demo,
    run_intake_demo,
    run_local_pipeline,
)

FIXED_TS = "2026-04-02T00:00:00+00:00"


def _readiness_contract(*, quarantine_max_ratio: float | None = None) -> dict[str, Any]:
    contract: dict[str, Any] = {
        "dataset": {"name": "ds", "contract_version": "1.0.0"},
        "contract": {
            "required_columns": [
                {"column_name": "id", "type": "long", "nullable": False},
                {"column_name": "amount", "type": "double", "nullable": False},
            ],
            "business_key": ["id"],
            "batch_identifier": "batch_id",
        },
    }
    if quarantine_max_ratio is not None:
        contract["contract"]["quarantine_max_ratio"] = quarantine_max_ratio
    return contract


def _frame_with_dupes(total_rows: int, duplicate_rows: int) -> pd.DataFrame:
    """Return a frame with `duplicate_rows` colliding business keys.

    Duplicates are produced by repeating a single id value across the first
    `duplicate_rows` records; pandas `duplicated(keep=False)` flags every
    row in a colliding group, so total quarantined rows == duplicate_rows.
    """
    if duplicate_rows < 0 or duplicate_rows > total_rows:
        raise AssertionError("duplicate_rows must be within [0, total_rows]")
    if duplicate_rows == 1:
        raise AssertionError("duplicate_rows == 1 cannot produce a colliding group")
    rows: list[dict[str, Any]] = []
    for index in range(duplicate_rows):
        rows.append({"id": 1, "batch_id": "B-1", "amount": float(index)})
    for index in range(total_rows - duplicate_rows):
        rows.append({"id": index + 2, "batch_id": "B-1", "amount": float(index)})
    return pd.DataFrame(rows)


def test_intake_demo_deterministic() -> None:
    r1 = run_intake_demo()
    r2 = run_intake_demo()
    assert r1 == r2
    assert r1["total_rows"] == 33
    assert r1["ready"] > 0
    assert r1["quarantined"] > 0


def test_drift_demo_deterministic() -> None:
    r1 = run_drift_demo(run_ts=FIXED_TS)
    r2 = run_drift_demo(run_ts=FIXED_TS)
    assert r1 == r2
    assert r1["columns_drifted"] == 4
    assert r1["overall_verdict"] in ("PASS", "WARN", "FAIL")


def test_drift_demo_provenance() -> None:
    result = run_drift_demo(run_ts=FIXED_TS)
    prov = result["provenance"]
    assert prov["run_ts"] == FIXED_TS
    assert prov["columns_checked"] == 5


def test_local_pipeline_deterministic() -> None:
    r1 = run_local_pipeline(run_ts=FIXED_TS)
    r2 = run_local_pipeline(run_ts=FIXED_TS)
    assert r1 == r2


def test_local_pipeline_has_all_domains() -> None:
    result = run_local_pipeline(run_ts=FIXED_TS)
    assert "intake" in result
    assert "drift" in result
    assert "benchmark" in result
    assert result["intake"]["total_rows"] > 0
    assert result["drift"]["columns_drifted"] > 0
    assert result["benchmark"]["overall_verdict"] in ("PASS", "WARN", "FAIL")


def test_local_pipeline_writes_evidence(tmp_path: Path) -> None:
    run_local_pipeline(evidence_dir=tmp_path, run_ts=FIXED_TS)
    evidence_files = list(tmp_path.glob("*.json"))
    assert len(evidence_files) >= 2  # benchmark bundle + pipeline summary
    summary = tmp_path / "pipeline_summary.json"
    assert summary.exists()
    data = json.loads(summary.read_text())
    assert data["meta"]["generated_at"] == FIXED_TS
    assert "intake" in data["payload"]


class TestValidateDatasetReadiness:
    """Coverage for DS-PATCH-036 — quarantine_max_ratio tolerance gate."""

    def test_default_threshold_passes_clean_frame(self) -> None:
        contract = _readiness_contract()
        frame = _frame_with_dupes(total_rows=10, duplicate_rows=0)
        result = _validate_dataset_readiness(contract, frame, dataset_label="Current dataset")
        assert result["quarantine_max_ratio"] == 0.0
        assert result["tolerance_applied"] is False
        assert result["quarantined"] == 0

    def test_default_threshold_rejects_any_quarantine(self) -> None:
        contract = _readiness_contract()
        frame = _frame_with_dupes(total_rows=10, duplicate_rows=2)
        with pytest.raises(ValueError, match="quarantined=2"):
            _validate_dataset_readiness(contract, frame, dataset_label="Current dataset")

    def test_tolerance_passes_when_ratio_below_threshold(self) -> None:
        contract = _readiness_contract(quarantine_max_ratio=0.05)
        frame = _frame_with_dupes(total_rows=100, duplicate_rows=3)
        result = _validate_dataset_readiness(contract, frame, dataset_label="Current dataset")
        assert result["quarantined"] == 3
        assert result["quarantine_ratio"] == pytest.approx(0.03, abs=1e-6)
        assert result["quarantine_max_ratio"] == 0.05
        assert result["tolerance_applied"] is True

    def test_tolerance_fails_when_ratio_above_threshold(self) -> None:
        contract = _readiness_contract(quarantine_max_ratio=0.05)
        frame = _frame_with_dupes(total_rows=100, duplicate_rows=7)
        with pytest.raises(ValueError) as excinfo:
            _validate_dataset_readiness(contract, frame, dataset_label="Current dataset")
        message = str(excinfo.value)
        assert "quarantine_ratio=0.0700" in message
        assert "quarantine_max_ratio=0.0500" in message
        assert "quarantined=7" in message

    def test_schema_violation_fails_regardless_of_tolerance(self) -> None:
        contract = _readiness_contract(quarantine_max_ratio=1.0)
        frame = pd.DataFrame([{"id": 1, "batch_id": "B-1"}])  # missing `amount`
        with pytest.raises(ValueError, match="missing_columns=\\['amount'\\]"):
            _validate_dataset_readiness(contract, frame, dataset_label="Current dataset")

    def test_tolerance_applied_false_when_threshold_zero_and_no_quarantine(self) -> None:
        contract = _readiness_contract(quarantine_max_ratio=0.0)
        frame = _frame_with_dupes(total_rows=10, duplicate_rows=0)
        result = _validate_dataset_readiness(contract, frame, dataset_label="Current dataset")
        assert result["tolerance_applied"] is False
        assert result["quarantined"] == 0

    def test_tolerance_records_threshold_on_pass_path(self) -> None:
        contract = _readiness_contract(quarantine_max_ratio=0.10)
        frame = _frame_with_dupes(total_rows=10, duplicate_rows=0)
        result = _validate_dataset_readiness(contract, frame, dataset_label="Current dataset")
        assert result["quarantine_max_ratio"] == 0.10
        assert result["tolerance_applied"] is False  # nothing was tolerated
        assert "_schema_invalid" not in result
        assert "_over_threshold" not in result
