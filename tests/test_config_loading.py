"""Tests for the shared config loader."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from driftsentinel.config.loader import (
    ConfigError,
    load_benchmark_policy,
    load_dataset_contract,
    load_drift_policy,
)

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"


# --- Dataset contract ---


def test_load_dataset_contract_from_template() -> None:
    data = load_dataset_contract(TEMPLATES / "dataset_contract.yml")
    assert "dataset" in data
    assert "contract" in data
    assert "required_columns" in data["contract"]
    assert "business_key" in data["contract"]
    assert "batch_identifier" in data["contract"]


def test_load_dataset_contract_missing_dataset(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yml"
    bad.write_text(yaml.dump({"contract": {"required_columns": [], "business_key": [], "batch_identifier": "x"}}))
    with pytest.raises(ConfigError, match="Missing required keys.*dataset"):
        load_dataset_contract(bad)


def test_load_dataset_contract_missing_contract_keys(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yml"
    bad.write_text(yaml.dump({"dataset": {"name": "x"}, "contract": {"required_columns": []}}))
    with pytest.raises(ConfigError, match="Missing required keys.*business_key"):
        load_dataset_contract(bad)


# --- Drift policy ---


def test_load_drift_policy_from_template() -> None:
    data = load_drift_policy(TEMPLATES / "drift_policy.yml")
    assert "drift_policy" in data
    policy = data["drift_policy"]
    assert policy["name"] == "example_drift_policy"
    assert "monitored_columns" in policy
    assert "gates" in policy


def test_load_drift_policy_missing_required(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yml"
    bad.write_text(yaml.dump({"drift_policy": {"name": "x"}}))
    with pytest.raises(ConfigError, match="Missing required keys.*dataset"):
        load_drift_policy(bad)


# --- Benchmark policy ---


def test_load_benchmark_policy_from_template() -> None:
    data = load_benchmark_policy(TEMPLATES / "benchmark_policy.yml")
    assert "benchmark_policy" in data
    policy = data["benchmark_policy"]
    assert policy["seed"] == 42
    assert "gates" in policy


def test_load_benchmark_policy_missing_required(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yml"
    bad.write_text(yaml.dump({"benchmark_policy": {"name": "x", "dataset": "y"}}))
    with pytest.raises(ConfigError, match="Missing required keys.*seed"):
        load_benchmark_policy(bad)


# --- Edge cases ---


def test_load_non_mapping_yaml(tmp_path: Path) -> None:
    bad = tmp_path / "list.yml"
    bad.write_text("- item1\n- item2\n")
    with pytest.raises(ConfigError, match="Expected a YAML mapping"):
        load_dataset_contract(bad)
