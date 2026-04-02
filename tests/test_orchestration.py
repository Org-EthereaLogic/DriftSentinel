"""Tests for the minimal Phase 1 orchestration layer.

Verifies that the local pipeline connects all three domains
and produces deterministic results.
"""

from __future__ import annotations

import json
from pathlib import Path

from driftsentinel.orchestration.runner import (
    run_drift_demo,
    run_intake_demo,
    run_local_pipeline,
)

FIXED_TS = "2026-04-02T00:00:00+00:00"


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
