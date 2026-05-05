"""Tests for driftsentinel.databricks.files — runtime volume layout and uploads.

Coverage focus: canonical on-volume policy filenames so that
'databricks run' (DS-PATCH-033) can resolve them deterministically.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable
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


@pytest.fixture
def volume_layout_factory() -> Callable[..., dict[str, str]]:
    """Build a consistent mocked runtime-volume layout for file sync tests."""

    def _factory(
        *,
        catalog: str = "c",
        schema: str = "s",
        volume_name: str = "v",
        dataset_id: str = "d",
    ) -> dict[str, str]:
        root = f"/Volumes/{catalog}/{schema}/{volume_name}"
        return {
            "root": root,
            "state": f"{root}/state",
            "policies": f"{root}/policies",
            "dataset_policies": f"{root}/policies/{dataset_id}",
            "evidence": f"{root}/evidence",
            "registry": f"{root}/state/registry.json",
            "landing": f"{root}/landing/{dataset_id}",
            "baseline": f"{root}/baseline/{dataset_id}",
        }

    return _factory


def _write_yaml(tmp_path: Path, name: str, body: str = "policy: {}\n") -> Path:
    p = tmp_path / name
    p.write_text(body, encoding="utf-8")
    return p


def test_sync_files_uploads_drift_policy_to_canonical_name(
    fake_client: mock.MagicMock,
    tmp_path: Path,
    volume_layout_factory: Callable[..., dict[str, str]],
) -> None:
    """Local filename is irrelevant — drift policy lands at policies/drift_policy.yml."""
    local = _write_yaml(tmp_path, "my_random_drift_name.yml")

    with mock.patch.object(files, "ensure_volume_layout") as ensure_layout:
        ensure_layout.return_value = volume_layout_factory()
        remote = files.sync_files(
            fake_client,
            catalog="c",
            schema="s",
            volume_name="v",
            dataset_id="d",
            drift_policy_path=local,
        )

    expected = runtime_drift_policy_path("c", "s", "d", volume_name="v")
    assert remote["drift_policy"] == expected
    fake_client.files.upload.assert_called_once()
    upload_kwargs = fake_client.files.upload.call_args
    assert upload_kwargs.args[0] == expected


def test_sync_files_uploads_benchmark_policy_to_canonical_name(
    fake_client: mock.MagicMock,
    tmp_path: Path,
    volume_layout_factory: Callable[..., dict[str, str]],
) -> None:
    """Local filename is irrelevant — benchmark policy lands at canonical name."""
    local = _write_yaml(tmp_path, "weird_bench_filename.yml")

    with mock.patch.object(files, "ensure_volume_layout") as ensure_layout:
        ensure_layout.return_value = volume_layout_factory()
        remote = files.sync_files(
            fake_client,
            catalog="c",
            schema="s",
            volume_name="v",
            dataset_id="d",
            benchmark_policy_path=local,
        )

    expected = runtime_benchmark_policy_path("c", "s", "d", volume_name="v")
    assert remote["benchmark_policy"] == expected
    fake_client.files.upload.assert_called_once()
    upload_kwargs = fake_client.files.upload.call_args
    assert upload_kwargs.args[0] == expected


def test_sync_files_canonical_paths_match_default_volume_layout(
    fake_client: mock.MagicMock,
    tmp_path: Path,
    volume_layout_factory: Callable[..., dict[str, str]],
) -> None:
    """Default volume name canonical paths agree with runtime_paths helpers."""
    drift_local = _write_yaml(tmp_path, "drift.yml")
    bench_local = _write_yaml(tmp_path, "bench.yml")

    with mock.patch.object(files, "ensure_volume_layout") as ensure_layout:
        ensure_layout.return_value = volume_layout_factory(
            catalog="main",
            schema="default",
            volume_name=DEFAULT_RUNTIME_VOLUME_NAME,
        )
        remote = files.sync_files(
            fake_client,
            catalog="main",
            schema="default",
            dataset_id="d",
            drift_policy_path=drift_local,
            benchmark_policy_path=bench_local,
        )

    assert remote["drift_policy"] == runtime_drift_policy_path("main", "default", "d")
    assert remote["benchmark_policy"] == runtime_benchmark_policy_path("main", "default", "d")


def test_sync_files_keeps_dataset_policy_paths_isolated(
    fake_client: mock.MagicMock,
    tmp_path: Path,
    volume_layout_factory: Callable[..., dict[str, str]],
) -> None:
    """Different datasets get distinct remote policy paths under the shared runtime volume."""
    local = _write_yaml(tmp_path, "drift.yml")

    with mock.patch.object(files, "ensure_volume_layout") as ensure_layout:
        ensure_layout.side_effect = [
            volume_layout_factory(dataset_id="dataset_a"),
            volume_layout_factory(dataset_id="dataset_b"),
        ]
        remote_a = files.sync_files(
            fake_client,
            catalog="c",
            schema="s",
            volume_name="v",
            dataset_id="dataset_a",
            drift_policy_path=local,
        )
        remote_b = files.sync_files(
            fake_client,
            catalog="c",
            schema="s",
            volume_name="v",
            dataset_id="dataset_b",
            drift_policy_path=local,
        )

    assert remote_a["drift_policy"] == runtime_drift_policy_path("c", "s", "dataset_a", volume_name="v")
    assert remote_b["drift_policy"] == runtime_drift_policy_path("c", "s", "dataset_b", volume_name="v")
    assert remote_a["drift_policy"] != remote_b["drift_policy"]
