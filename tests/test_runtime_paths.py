"""Tests for shared Databricks runtime path helpers."""

from __future__ import annotations

import pytest

from driftsentinel.runtime_paths import (
    DEFAULT_RUNTIME_VOLUME_NAME,
    runtime_evidence_dir,
    runtime_registry_path,
    runtime_volume_root,
)


def test_runtime_volume_root_requires_catalog_and_schema() -> None:
    with pytest.raises(ValueError):
        runtime_volume_root("", "default")
    with pytest.raises(ValueError):
        runtime_volume_root("main", "")


def test_runtime_paths_use_expected_shared_volume_layout() -> None:
    root = runtime_volume_root("main", "governed")
    assert root == f"/Volumes/main/governed/{DEFAULT_RUNTIME_VOLUME_NAME}"
    assert runtime_registry_path("main", "governed") == (
        f"{root}/state/registry.json"
    )
    assert runtime_evidence_dir("main", "governed") == f"{root}/evidence"
