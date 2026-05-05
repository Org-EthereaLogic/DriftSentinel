"""Tests for driftsentinel.databricks.files — runtime volume layout and uploads.

Coverage focus: canonical on-volume policy filenames so that
'databricks run' (DS-PATCH-033) can resolve them deterministically.
"""

from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from driftsentinel.databricks import files
from driftsentinel.runtime_paths import (
    DEFAULT_RUNTIME_VOLUME_NAME,
    runtime_benchmark_policy_path,
    runtime_drift_policy_path,
)


@pytest.fixture
def fake_client() -> mock.MagicMock:
    """Mock Databricks workspace client whose files API is a MagicMock."""
    client = mock.MagicMock()
    client.files = mock.MagicMock()
    return client


def _write_yaml(tmp_path: Path, name: str, body: str = "policy: {}\n") -> Path:
    p = tmp_path / name
    p.write_text(body, encoding="utf-8")
    return p


def test_sync_files_uploads_drift_policy_to_canonical_name(fake_client: mock.MagicMock, tmp_path: Path) -> None:
    """Local filename is irrelevant — drift policy lands at policies/drift_policy.yml."""
    local = _write_yaml(tmp_path, "my_random_drift_name.yml")

    with mock.patch.object(files, "ensure_volume_layout") as ensure_layout:
        ensure_layout.return_value = {
            "root": "/Volumes/c/s/v",
            "state": "/Volumes/c/s/v/state",
            "policies": "/Volumes/c/s/v/policies",
            "evidence": "/Volumes/c/s/v/evidence",
            "registry": "/Volumes/c/s/v/state/registry.json",
            "landing": "/Volumes/c/s/v/landing/d",
            "baseline": "/Volumes/c/s/v/baseline/d",
        }
        remote = files.sync_files(
            fake_client,
            catalog="c",
            schema="s",
            volume_name="v",
            dataset_id="d",
            drift_policy_path=local,
        )

    expected = runtime_drift_policy_path("c", "s", volume_name="v")
    assert remote["drift_policy"] == expected
    fake_client.files.upload.assert_called_once()
    upload_kwargs = fake_client.files.upload.call_args
    assert upload_kwargs.args[0] == expected


def test_sync_files_uploads_benchmark_policy_to_canonical_name(fake_client: mock.MagicMock, tmp_path: Path) -> None:
    """Local filename is irrelevant — benchmark policy lands at canonical name."""
    local = _write_yaml(tmp_path, "weird_bench_filename.yml")

    with mock.patch.object(files, "ensure_volume_layout") as ensure_layout:
        ensure_layout.return_value = {
            "root": "/Volumes/c/s/v",
            "state": "/Volumes/c/s/v/state",
            "policies": "/Volumes/c/s/v/policies",
            "evidence": "/Volumes/c/s/v/evidence",
            "registry": "/Volumes/c/s/v/state/registry.json",
            "landing": "/Volumes/c/s/v/landing/d",
            "baseline": "/Volumes/c/s/v/baseline/d",
        }
        remote = files.sync_files(
            fake_client,
            catalog="c",
            schema="s",
            volume_name="v",
            dataset_id="d",
            benchmark_policy_path=local,
        )

    expected = runtime_benchmark_policy_path("c", "s", volume_name="v")
    assert remote["benchmark_policy"] == expected
    fake_client.files.upload.assert_called_once()
    upload_kwargs = fake_client.files.upload.call_args
    assert upload_kwargs.args[0] == expected


def test_sync_files_canonical_paths_match_default_volume_layout(fake_client: mock.MagicMock, tmp_path: Path) -> None:
    """Default volume name canonical paths agree with runtime_paths helpers."""
    drift_local = _write_yaml(tmp_path, "drift.yml")
    bench_local = _write_yaml(tmp_path, "bench.yml")

    with mock.patch.object(files, "ensure_volume_layout") as ensure_layout:
        ensure_layout.return_value = {
            "root": f"/Volumes/main/default/{DEFAULT_RUNTIME_VOLUME_NAME}",
            "state": f"/Volumes/main/default/{DEFAULT_RUNTIME_VOLUME_NAME}/state",
            "policies": f"/Volumes/main/default/{DEFAULT_RUNTIME_VOLUME_NAME}/policies",
            "evidence": f"/Volumes/main/default/{DEFAULT_RUNTIME_VOLUME_NAME}/evidence",
            "registry": f"/Volumes/main/default/{DEFAULT_RUNTIME_VOLUME_NAME}/state/registry.json",
            "landing": f"/Volumes/main/default/{DEFAULT_RUNTIME_VOLUME_NAME}/landing/d",
            "baseline": f"/Volumes/main/default/{DEFAULT_RUNTIME_VOLUME_NAME}/baseline/d",
        }
        remote = files.sync_files(
            fake_client,
            catalog="main",
            schema="default",
            dataset_id="d",
            drift_policy_path=drift_local,
            benchmark_policy_path=bench_local,
        )

    assert remote["drift_policy"] == runtime_drift_policy_path("main", "default")
    assert remote["benchmark_policy"] == runtime_benchmark_policy_path("main", "default")
