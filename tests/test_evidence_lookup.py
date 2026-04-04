"""Tests for Phase 3 evidence lookup and dataset-aware metadata."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from driftsentinel.evidence.writer import (
    generate_run_id,
    list_evidence,
    load_evidence,
    write_evidence,
)
from driftsentinel.paths import PathSecurityError

ROOT = Path(__file__).resolve().parent.parent
FIXED_TS = "2026-04-02T00:00:00+00:00"


class TestEvidenceMetadata:
    def test_write_with_dataset_metadata(self, tmp_path: Path) -> None:
        path = write_evidence(
            tmp_path,
            "test.json",
            {"result": "ok"},
            run_ts=FIXED_TS,
            dataset_id="ds_a",
            contract_version="1.0.0",
            policy_version="1.0.0",
            run_id="run-123",
            run_kind="intake",
            execution_mode="dataset_backed",
        )
        data = json.loads(path.read_text())
        meta = data["meta"]
        assert meta["dataset_id"] == "ds_a"
        assert meta["contract_version"] == "1.0.0"
        assert meta["policy_version"] == "1.0.0"
        assert meta["run_id"] == "run-123"
        assert meta["run_kind"] == "intake"
        assert meta["execution_mode"] == "dataset_backed"

    def test_write_without_metadata_is_backward_compatible(self, tmp_path: Path) -> None:
        path = write_evidence(tmp_path, "test.json", {"x": 1}, run_ts=FIXED_TS)
        data = json.loads(path.read_text())
        meta = data["meta"]
        assert "dataset_id" not in meta
        assert meta["generated_at"] == FIXED_TS

    def test_generate_run_id_unique(self) -> None:
        ids = {generate_run_id() for _ in range(100)}
        assert len(ids) == 100


class TestListEvidence:
    def _write_artifacts(self, tmp_path: Path) -> None:
        write_evidence(
            tmp_path, "a.json", {"v": 1},
            run_ts="2026-04-01T10:00:00+00:00",
            dataset_id="ds_a", run_kind="intake", run_id="r1", execution_mode="dataset_backed",
        )
        write_evidence(
            tmp_path, "b.json", {"v": 2},
            run_ts="2026-04-02T10:00:00+00:00",
            dataset_id="ds_b", run_kind="drift", run_id="r2", execution_mode="dataset_backed",
        )
        write_evidence(
            tmp_path, "c.json", {"v": 3},
            run_ts="2026-04-03T10:00:00+00:00",
            dataset_id="ds_a", run_kind="benchmark", run_id="r3", execution_mode="synthetic",
        )

    def test_list_all(self, tmp_path: Path) -> None:
        self._write_artifacts(tmp_path)
        results = list_evidence(tmp_path)
        assert len(results) == 3

    def test_filter_by_dataset(self, tmp_path: Path) -> None:
        self._write_artifacts(tmp_path)
        results = list_evidence(tmp_path, dataset_id="ds_a")
        assert len(results) == 2
        assert all(r["dataset_id"] == "ds_a" for r in results)

    def test_filter_by_run_kind(self, tmp_path: Path) -> None:
        self._write_artifacts(tmp_path)
        results = list_evidence(tmp_path, run_kind="drift")
        assert len(results) == 1
        assert results[0]["run_kind"] == "drift"

    def test_filter_by_execution_mode(self, tmp_path: Path) -> None:
        self._write_artifacts(tmp_path)
        results = list_evidence(tmp_path, execution_mode="synthetic")
        assert len(results) == 1
        assert results[0]["execution_mode"] == "synthetic"

    def test_filter_by_run_id(self, tmp_path: Path) -> None:
        self._write_artifacts(tmp_path)
        results = list_evidence(tmp_path, run_id="r2")
        assert len(results) == 1
        assert results[0]["run_id"] == "r2"

    def test_filter_by_date_range(self, tmp_path: Path) -> None:
        self._write_artifacts(tmp_path)
        results = list_evidence(
            tmp_path,
            date_from="2026-04-02T00:00:00",
            date_to="2026-04-02T23:59:59",
        )
        assert len(results) == 1
        assert results[0]["dataset_id"] == "ds_b"

    def test_filter_by_same_day_uses_inclusive_bounds(self, tmp_path: Path) -> None:
        self._write_artifacts(tmp_path)
        results = list_evidence(
            tmp_path,
            date_from="2026-04-02",
            date_to="2026-04-02",
        )
        assert len(results) == 1
        assert results[0]["dataset_id"] == "ds_b"

    def test_empty_directory(self, tmp_path: Path) -> None:
        results = list_evidence(tmp_path)
        assert results == []

    def test_missing_directory(self, tmp_path: Path) -> None:
        results = list_evidence(tmp_path / "nonexistent")
        assert results == []

    def test_untrusted_directory_rejected(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT.parent) as temp_dir:
            with pytest.raises(PathSecurityError, match="trusted roots"):
                list_evidence(temp_dir)

    def test_malformed_file_skipped(self, tmp_path: Path) -> None:
        (tmp_path / "bad.json").write_text("not json{{{")
        self._write_artifacts(tmp_path)
        results = list_evidence(tmp_path)
        malformed = [r for r in results if r.get("parse_error")]
        valid = [r for r in results if not r.get("parse_error")]
        assert len(malformed) == 1
        assert len(valid) == 3

    def test_sorted_descending_by_date(self, tmp_path: Path) -> None:
        self._write_artifacts(tmp_path)
        results = list_evidence(tmp_path)
        valid = [r for r in results if not r.get("parse_error")]
        dates = [r["generated_at"] for r in valid]
        assert dates == sorted(dates, reverse=True)

    def test_extracts_overall_verdict_when_present(self, tmp_path: Path) -> None:
        write_evidence(
            tmp_path,
            "verdict.json",
            {"overall_verdict": "PASS"},
            run_ts=FIXED_TS,
            dataset_id="ds_a",
            run_kind="benchmark",
            run_id="r1",
        )
        results = list_evidence(tmp_path)
        assert len(results) == 1
        assert results[0]["overall_verdict"] == "PASS"

    def test_missing_execution_mode_is_tagged_legacy_unknown(self, tmp_path: Path) -> None:
        path = write_evidence(tmp_path, "legacy.json", {"x": 1}, run_ts=FIXED_TS)
        data = json.loads(path.read_text())
        assert "execution_mode" not in data["meta"]
        results = list_evidence(tmp_path)
        assert results[0]["execution_mode"] == "legacy_or_unknown"


class TestLoadEvidence:
    def test_load_valid(self, tmp_path: Path) -> None:
        path = write_evidence(tmp_path, "test.json", {"x": 1}, run_ts=FIXED_TS)
        data = load_evidence(path)
        assert data["payload"]["x"] == 1

    def test_load_missing_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_evidence(tmp_path / "missing.json")

    def test_load_malformed_raises(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.json"
        bad.write_text("not json")
        with pytest.raises(ValueError, match="Malformed"):
            load_evidence(bad)

    def test_load_untrusted_path_raises(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT.parent) as temp_dir:
            artifact = Path(temp_dir) / "outside.json"
            artifact.write_text('{"meta": {}, "payload": {}}', encoding="utf-8")
            with pytest.raises(PathSecurityError, match="trusted roots"):
                load_evidence(artifact)
