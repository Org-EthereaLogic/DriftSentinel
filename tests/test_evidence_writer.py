"""Tests for the shared evidence writer."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from driftsentinel.evidence.writer import (
    build_provenance_envelope,
    write_benchmark_bundle,
    write_evidence,
)
from driftsentinel.paths import PathSecurityError

FIXED_TS = "2026-04-02T00:00:00+00:00"


def test_write_evidence_creates_file(tmp_path: Path) -> None:
    payload = {"result": "ok", "score": 0.95}
    path = write_evidence(tmp_path, "test.json", payload, run_ts=FIXED_TS)
    assert path.exists()
    data = json.loads(path.read_text())
    assert data["meta"]["generated_at"] == FIXED_TS
    assert data["payload"]["result"] == "ok"


def test_write_evidence_creates_directory(tmp_path: Path) -> None:
    nested = tmp_path / "a" / "b"
    path = write_evidence(nested, "test.json", {"x": 1}, run_ts=FIXED_TS)
    assert path.exists()
    assert nested.is_dir()


def test_write_evidence_never_overwrites(tmp_path: Path) -> None:
    p1 = write_evidence(tmp_path, "out.json", {"run": 1}, run_ts=FIXED_TS)
    p2 = write_evidence(tmp_path, "out.json", {"run": 2}, run_ts=FIXED_TS)
    assert p1 != p2
    assert p1.exists()
    assert p2.exists()
    d1 = json.loads(p1.read_text())
    d2 = json.loads(p2.read_text())
    assert d1["payload"]["run"] == 1
    assert d2["payload"]["run"] == 2


def test_write_evidence_deterministic_ts(tmp_path: Path) -> None:
    path = write_evidence(tmp_path, "ts.json", {}, run_ts=FIXED_TS)
    data = json.loads(path.read_text())
    assert data["meta"]["generated_at"] == FIXED_TS


def test_write_evidence_rejects_nested_filename(tmp_path: Path) -> None:
    with pytest.raises(PathSecurityError, match="bare filename"):
        write_evidence(tmp_path, "../escape.json", {"x": 1}, run_ts=FIXED_TS)


def test_build_provenance_envelope() -> None:
    envelope = build_provenance_envelope(
        health_score=0.85,
        overall_verdict="PASS",
        columns_checked=5,
        columns_drifted=1,
        row_count_baseline=25,
        row_count_current=25,
        schema_match=True,
        gate_results=[{"name": "health", "verdict": "PASS"}],
        column_details=[{"column": "dept", "classification": "stable"}],
        run_ts=FIXED_TS,
    )
    assert envelope["run_ts"] == FIXED_TS
    assert envelope["health_score"] == 0.85
    assert envelope["overall_verdict"] == "PASS"
    assert len(envelope["gate_results"]) == 1
    assert len(envelope["column_details"]) == 1


def test_write_benchmark_bundle(tmp_path: Path) -> None:
    path = write_benchmark_bundle(
        output_dir=tmp_path,
        seed=42,
        n_rows=100,
        baseline_quality={"recall": 0.8},
        challenger_quality={"recall": 0.95},
        baseline_drift={"combined": 0.5},
        challenger_drift={"combined": 0.9},
        gate_results=[],
        overall_verdict="PASS",
        run_ts=FIXED_TS,
    )
    assert path.exists()
    assert "bench_42_100" in path.name
    data = json.loads(path.read_text())
    assert data["payload"]["overall_verdict"] == "PASS"
    assert data["payload"]["seed"] == 42
