"""Tests for Phase 3 dataset registry and policy versioning."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from driftsentinel import paths as ds_paths
from driftsentinel.config.loader import (
    ConfigError,
    DatasetRegistry,
    RegistryError,
    check_policy_compatibility,
    load_dataset_contract,
    load_drift_policy,
)
from driftsentinel.paths import PathSecurityError

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"


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


def _make_benchmark_policy(
    dataset: str = "test_ds",
    contract_version: str = "1.0.0",
    policy_version: str = "1.0.0",
) -> dict[str, Any]:
    return {
        "benchmark_policy": {
            "name": f"{dataset}_bench",
            "dataset": dataset,
            "contract_version": contract_version,
            "policy_version": policy_version,
            "seed": 42,
            "gates": [
                {"name": "g1", "type": "FAIL", "operator": ">=", "threshold": 0.5},
            ],
        },
    }


# --- Registration ---


class TestDatasetRegistration:
    def test_register_and_get(self) -> None:
        reg = DatasetRegistry()
        contract = _make_contract("ds_a", "1.0.0")
        key = reg.register(contract)
        assert key == ("ds_a", "1.0.0")
        assert reg.get("ds_a") == contract

    def test_register_multiple_datasets(self) -> None:
        reg = DatasetRegistry()
        reg.register(_make_contract("ds_a", "1.0.0"))
        reg.register(_make_contract("ds_b", "1.0.0"))
        assert len(reg.list_datasets()) == 2

    def test_register_multiple_versions(self) -> None:
        reg = DatasetRegistry()
        reg.register(_make_contract("ds_a", "1.0.0"))
        reg.register(_make_contract("ds_a", "2.0.0"))
        assert len(reg.list_datasets()) == 2
        latest = reg.get("ds_a")
        assert latest["dataset"]["contract_version"] == "2.0.0"

    def test_get_latest_uses_semver_not_lexicographic(self) -> None:
        reg = DatasetRegistry()
        reg.register(_make_contract("ds_a", "2.0.0"))
        reg.register(_make_contract("ds_a", "10.0.0"))
        latest = reg.get("ds_a")
        assert latest["dataset"]["contract_version"] == "10.0.0"

    def test_duplicate_registration_rejected(self) -> None:
        reg = DatasetRegistry()
        reg.register(_make_contract("ds_a", "1.0.0"))
        with pytest.raises(RegistryError, match="already registered"):
            reg.register(_make_contract("ds_a", "1.0.0"))

    def test_get_unknown_dataset_rejected(self) -> None:
        reg = DatasetRegistry()
        with pytest.raises(RegistryError, match="not registered"):
            reg.get("nonexistent")

    def test_get_specific_version(self) -> None:
        reg = DatasetRegistry()
        reg.register(_make_contract("ds_a", "1.0.0"))
        reg.register(_make_contract("ds_a", "2.0.0"))
        v1 = reg.get("ds_a", "1.0.0")
        assert v1["dataset"]["contract_version"] == "1.0.0"

    def test_get_unknown_version_rejected(self) -> None:
        reg = DatasetRegistry()
        reg.register(_make_contract("ds_a", "1.0.0"))
        with pytest.raises(RegistryError, match="not registered"):
            reg.get("ds_a", "9.9.9")

    def test_contains(self) -> None:
        reg = DatasetRegistry()
        reg.register(_make_contract("ds_a", "1.0.0"))
        assert reg.contains("ds_a")
        assert reg.contains("ds_a", "1.0.0")
        assert not reg.contains("ds_a", "2.0.0")
        assert not reg.contains("ds_b")

    def test_remove(self) -> None:
        reg = DatasetRegistry()
        reg.register(_make_contract("ds_a", "1.0.0"))
        reg.remove("ds_a", "1.0.0")
        assert not reg.contains("ds_a")

    def test_remove_unknown_rejected(self) -> None:
        reg = DatasetRegistry()
        with pytest.raises(RegistryError, match="not registered"):
            reg.remove("ds_a", "1.0.0")

    def test_register_invalid_contract_rejected(self) -> None:
        reg = DatasetRegistry()
        with pytest.raises(ConfigError):
            reg.register({"dataset": {"name": "x"}})


# --- Serialization ---


class TestRegistrySerialization:
    def test_save_and_load(self, tmp_path: Path) -> None:
        reg = DatasetRegistry()
        reg.register(_make_contract("ds_a", "1.0.0"))
        reg.register(_make_contract("ds_b", "1.0.0"))
        path = reg.save(tmp_path / "registry.json")
        loaded = DatasetRegistry.load(path)
        assert loaded.list_datasets() == reg.list_datasets()
        assert loaded.get("ds_a") == reg.get("ds_a")
        assert loaded.get("ds_b") == reg.get("ds_b")

    def test_load_missing_file_rejected(self, tmp_path: Path) -> None:
        with pytest.raises(RegistryError, match="not found"):
            DatasetRegistry.load(tmp_path / "missing.json")

    def test_load_invalid_format_rejected(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.json"
        bad.write_text('["not a registry"]')
        with pytest.raises(RegistryError, match="Invalid registry"):
            DatasetRegistry.load(bad)

    def test_load_untrusted_path_rejected(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "driftsentinel.paths.trusted_roots",
            lambda extra_roots=(): (str(tmp_path / "_no_match_"),),
        )
        bad = tmp_path / "registry.json"
        bad.write_text('{"registry": []}', encoding="utf-8")
        with pytest.raises(PathSecurityError, match="trusted roots"):
            DatasetRegistry.load(bad)

    def test_save_untrusted_path_rejected(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "driftsentinel.paths.trusted_roots",
            lambda extra_roots=(): (str(tmp_path / "_no_match_"),),
        )
        reg = DatasetRegistry()
        reg.register(_make_contract("ds_a", "1.0.0"))
        with pytest.raises(PathSecurityError, match="trusted roots"):
            reg.save(tmp_path / "registry.json")

    def test_load_supports_dbfs_uri_when_root_is_allowed(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        reg = DatasetRegistry()
        reg.register(_make_contract("ds_a", "1.0.0"))
        dbfs_root = tmp_path / "dbfs"
        registry_path = dbfs_root / "tmp" / "registry.json"
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        reg.save(registry_path)

        original_normalized_path = ds_paths._normalized_path

        def _fake_normalized_path(value: str | Path) -> str:
            if str(value) == "dbfs:/tmp/registry.json":
                return str(registry_path)
            return original_normalized_path(value)

        monkeypatch.setattr(ds_paths, "_normalized_path", _fake_normalized_path)
        loaded = DatasetRegistry.load("dbfs:/tmp/registry.json")

        assert loaded.contains("ds_a", "1.0.0")


# --- Policy Compatibility ---


class TestPolicyCompatibility:
    def test_compatible_drift_policy(self) -> None:
        reg = DatasetRegistry()
        reg.register(_make_contract("ds_a", "1.0.0"))
        policy = _make_drift_policy("ds_a", "1.0.0", "1.0.0")
        result = check_policy_compatibility(reg, policy["drift_policy"], "Drift policy")
        assert result["dataset_id"] == "ds_a"
        assert result["contract_version"] == "1.0.0"
        assert result["policy_version"] == "1.0.0"

    def test_compatible_benchmark_policy(self) -> None:
        reg = DatasetRegistry()
        reg.register(_make_contract("ds_a", "1.0.0"))
        policy = _make_benchmark_policy("ds_a", "1.0.0", "1.0.0")
        result = check_policy_compatibility(reg, policy["benchmark_policy"], "Benchmark policy")
        assert result["dataset_id"] == "ds_a"

    def test_version_mismatch_rejected(self) -> None:
        reg = DatasetRegistry()
        reg.register(_make_contract("ds_a", "1.0.0"))
        policy = _make_drift_policy("ds_a", "2.0.0", "1.0.0")
        with pytest.raises(RegistryError, match="version '2.0.0'"):
            check_policy_compatibility(reg, policy["drift_policy"], "Drift policy")

    def test_unknown_dataset_rejected(self) -> None:
        reg = DatasetRegistry()
        reg.register(_make_contract("ds_a", "1.0.0"))
        policy = _make_drift_policy("ds_x", "1.0.0", "1.0.0")
        with pytest.raises(RegistryError, match="not registered"):
            check_policy_compatibility(reg, policy["drift_policy"], "Drift policy")


# --- Template version metadata ---


class TestTemplateVersionMetadata:
    def test_dataset_contract_has_version(self) -> None:
        data = load_dataset_contract(TEMPLATES / "dataset_contract.yml")
        assert "contract_version" in data["dataset"]
        assert data["dataset"]["contract_version"] == "1.0.0"

    def test_drift_policy_has_versions(self) -> None:
        data = load_drift_policy(TEMPLATES / "drift_policy.yml")
        dp = data["drift_policy"]
        assert "contract_version" in dp
        assert "policy_version" in dp

    def test_benchmark_policy_has_versions(self) -> None:
        bp_path = TEMPLATES / "benchmark_policy.yml"
        with open(bp_path) as f:
            data = yaml.safe_load(f)
        bp = data["benchmark_policy"]
        assert "contract_version" in bp
        assert "policy_version" in bp
