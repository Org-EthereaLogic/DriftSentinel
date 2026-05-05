"""Tests for shared Databricks runtime path helpers."""

from __future__ import annotations

import pytest

from driftsentinel.runtime_paths import (
    DEFAULT_RUNTIME_VOLUME_NAME,
    runtime_benchmark_policy_path,
    runtime_drift_policy_path,
    runtime_evidence_dir,
    runtime_policies_dir,
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
    assert runtime_registry_path("main", "governed") == (f"{root}/state/registry.json")
    assert runtime_evidence_dir("main", "governed") == f"{root}/evidence"


def test_canonical_policy_paths_are_under_policies_dir() -> None:
    root = runtime_volume_root("main", "governed")
    assert runtime_policies_dir("main", "governed") == f"{root}/policies"
    assert runtime_drift_policy_path("main", "governed") == f"{root}/policies/drift_policy.yml"
    assert runtime_benchmark_policy_path("main", "governed") == f"{root}/policies/benchmark_policy.yml"
