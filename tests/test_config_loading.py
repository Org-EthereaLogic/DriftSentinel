"""Tests for the shared config loader."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from driftsentinel.config.loader import (
    ConfigError,
    _substitute_placeholders,
    load_benchmark_policy,
    load_dataset_contract,
    load_drift_policy,
    load_packaged_benchmark_policy,
    load_packaged_dataset_contract,
    load_packaged_drift_policy,
    normalize_benchmark_gates,
)
from driftsentinel.paths import PathSecurityError

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


def test_load_packaged_dataset_contract() -> None:
    data = load_packaged_dataset_contract()
    assert "dataset" in data
    assert "contract" in data
    assert data["dataset"]["catalog"] == "${CATALOG}"


def test_load_packaged_dataset_contract_with_catalog() -> None:
    data = load_packaged_dataset_contract(catalog="my_catalog", schema="my_schema")
    assert data["dataset"]["catalog"] == "my_catalog"
    assert data["dataset"]["schema"] == "my_schema"
    assert "my_catalog" in data["source"]["landing_path"]
    assert "my_schema" in data["source"]["landing_path"]


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


def test_load_packaged_drift_policy() -> None:
    data = load_packaged_drift_policy()
    assert "drift_policy" in data
    assert data["drift_policy"]["name"] == "example_drift_policy"


def test_load_drift_policy_missing_required(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yml"
    bad.write_text(yaml.dump({"drift_policy": {"name": "x"}}))
    with pytest.raises(ConfigError, match="Missing required keys.*dataset"):
        load_drift_policy(bad)


def test_load_drift_policy_rejects_unknown_monitored_column_method(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yml"
    bad.write_text(
        yaml.dump(
            {
                "drift_policy": {
                    "name": "x",
                    "dataset": "orders",
                    "monitored_columns": [{"column_name": "amount", "method": "not_real"}],
                    "gates": {"health_score_threshold": 0.7},
                }
            }
        )
    )
    with pytest.raises(ConfigError, match="Unsupported drift method 'not_real'"):
        load_drift_policy(bad)


# --- Benchmark policy ---


def test_load_benchmark_policy_from_template() -> None:
    data = load_benchmark_policy(TEMPLATES / "benchmark_policy.yml")
    assert "benchmark_policy" in data
    policy = data["benchmark_policy"]
    assert policy["seed"] == 42
    assert "gates" in policy
    assert isinstance(policy["gates"], list)
    assert len(policy["gates"]) == 10


def test_load_packaged_benchmark_policy() -> None:
    data = load_packaged_benchmark_policy()
    assert "benchmark_policy" in data
    assert len(data["benchmark_policy"]["gates"]) == 10


def test_normalize_benchmark_gates_from_template() -> None:
    data = load_benchmark_policy(TEMPLATES / "benchmark_policy.yml")
    gates = normalize_benchmark_gates(data)
    assert len(gates) == 10
    for gate in gates:
        assert "name" in gate
        assert "type" in gate
        assert "operator" in gate
        assert "threshold" in gate
        assert "track" in gate
        assert "description" in gate
        assert isinstance(gate["threshold"], float)
    names = [g["name"] for g in gates]
    assert "quality_recall" in names
    assert "drift_fpr" in names


def test_normalize_benchmark_gates_rejects_flat_dict() -> None:
    policy = {"benchmark_policy": {"gates": {"min_recall": 0.80}}}
    with pytest.raises(ConfigError, match="Expected 'gates' to be a list"):
        normalize_benchmark_gates(policy)


def test_normalize_benchmark_gates_rejects_missing_keys() -> None:
    policy = {"benchmark_policy": {"gates": [{"name": "test"}]}}
    with pytest.raises(ConfigError, match="missing keys.*type"):
        normalize_benchmark_gates(policy)


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


# --- Token substitution (${CATALOG}, ${SCHEMA}, ${VOLUME}) ---


def test_substitute_placeholders_replaces_catalog_in_nested_string(tmp_path: Path) -> None:
    p = tmp_path / "contract.yml"
    p.write_text(
        "dataset:\n  name: ds\n  catalog: ${CATALOG}\n"
        "  schema: ${SCHEMA}\n"
        "source:\n  landing_path: /Volumes/${CATALOG}/${SCHEMA}/landing/ds/\n"
        "contract:\n  required_columns: []\n  business_key: [id]\n  batch_identifier: bid\n"
    )
    data = load_dataset_contract(p, catalog="prod", schema="analytics")
    assert data["dataset"]["catalog"] == "prod"
    assert data["dataset"]["schema"] == "analytics"
    assert data["source"]["landing_path"] == "/Volumes/prod/analytics/landing/ds/"


def test_substitute_placeholders_missing_kwarg_leaves_placeholder(tmp_path: Path) -> None:
    p = tmp_path / "contract.yml"
    p.write_text(
        "dataset:\n  name: ds\n  catalog: ${CATALOG}\n"
        "  schema: ${SCHEMA}\n"
        "contract:\n  required_columns: []\n  business_key: [id]\n  batch_identifier: bid\n"
    )
    data = load_dataset_contract(p, catalog="prod")
    assert data["dataset"]["catalog"] == "prod"
    assert data["dataset"]["schema"] == "${SCHEMA}"


def test_substitute_placeholders_no_kwargs_leaves_all_placeholders(tmp_path: Path) -> None:
    p = tmp_path / "contract.yml"
    p.write_text(
        "dataset:\n  name: ds\n  catalog: ${CATALOG}\n"
        "  schema: ${SCHEMA}\n"
        "contract:\n  required_columns: []\n  business_key: [id]\n  batch_identifier: bid\n"
    )
    data = load_dataset_contract(p)
    assert data["dataset"]["catalog"] == "${CATALOG}"
    assert data["dataset"]["schema"] == "${SCHEMA}"


def test_substitute_placeholders_volume_name(tmp_path: Path) -> None:
    policy = tmp_path / "drift.yml"
    policy.write_text(
        "drift_policy:\n  name: p\n  dataset: ds\n  contract_version: '1.0.0'\n"
        "  policy_version: '1.0.0'\n"
        "  monitored_columns:\n    - column_name: amount\n      method: shannon_entropy\n"
        "  baseline:\n    source: trusted_load\n"
        "    path: /Volumes/${CATALOG}/${SCHEMA}/${VOLUME}/baseline/\n"
        "    format: csv\n    min_rows: 10\n"
        "  gates:\n    health_score_threshold: 0.7\n    max_columns_failed: 1\n"
    )
    data = load_drift_policy(policy, catalog="c", schema="s", volume_name="vol")
    assert data["drift_policy"]["baseline"]["path"] == "/Volumes/c/s/vol/baseline/"


def test_substitute_placeholders_no_double_substitution() -> None:
    data = _substitute_placeholders(
        {"key": "${CATALOG}_suffix"},
        catalog="c",
        schema=None,
        volume_name=None,
    )
    assert data["key"] == "c_suffix"


def test_substitute_placeholders_drift_policy_from_template() -> None:
    data = load_packaged_drift_policy(catalog="my_catalog", schema="my_schema")
    assert "my_catalog" in data["drift_policy"]["baseline"]["path"]
    assert "my_schema" in data["drift_policy"]["baseline"]["path"]


def test_substitute_placeholders_benchmark_policy_from_template() -> None:
    data = load_packaged_benchmark_policy(catalog="my_catalog")
    assert "benchmark_policy" in data


def test_load_dataset_contract_rejects_untrusted_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "driftsentinel.paths.trusted_roots",
        lambda extra_roots=(): (str(tmp_path / "_no_match_"),),
    )
    bad = tmp_path / "dataset_contract.yml"
    bad.write_text(
        yaml.dump(
            {
                "dataset": {"name": "x"},
                "contract": {
                    "required_columns": [],
                    "business_key": ["id"],
                    "batch_identifier": "batch_id",
                },
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(PathSecurityError, match="trusted roots"):
        load_dataset_contract(bad)
