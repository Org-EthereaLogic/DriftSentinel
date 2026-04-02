"""Shared configuration loader for dataset contracts, drift policies, and benchmark policies.

Loads YAML configuration files and validates required fields. All three
domain packages (intake, drift, benchmark) use this shared surface
instead of maintaining separate config parsers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class ConfigError(Exception):
    """Raised when a configuration file is missing required fields."""


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load and parse a YAML file."""
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ConfigError(f"Expected a YAML mapping in {path}, got {type(data).__name__}")
    return data


def _require_keys(data: dict[str, Any], keys: list[str], context: str) -> None:
    """Raise ConfigError if any required key is missing from data."""
    missing = [k for k in keys if k not in data]
    if missing:
        raise ConfigError(f"Missing required keys in {context}: {', '.join(missing)}")


def load_dataset_contract(path: str | Path) -> dict[str, Any]:
    """Load a dataset contract YAML and validate required fields.

    Required top-level keys: dataset, contract.
    Required contract keys: required_columns, business_key, batch_identifier.
    """
    p = Path(path)
    data = _load_yaml(p)
    _require_keys(data, ["dataset", "contract"], f"dataset contract ({p.name})")
    _require_keys(
        data["contract"],
        ["required_columns", "business_key", "batch_identifier"],
        f"contract section ({p.name})",
    )
    return data


def load_drift_policy(path: str | Path) -> dict[str, Any]:
    """Load a drift policy YAML and validate required fields.

    Required top-level key: drift_policy.
    Required drift_policy keys: name, dataset, monitored_columns, gates.
    """
    p = Path(path)
    data = _load_yaml(p)
    _require_keys(data, ["drift_policy"], f"drift policy ({p.name})")
    _require_keys(
        data["drift_policy"],
        ["name", "dataset", "monitored_columns", "gates"],
        f"drift_policy section ({p.name})",
    )
    return data


def load_benchmark_policy(path: str | Path) -> dict[str, Any]:
    """Load a benchmark policy YAML and validate required fields.

    Required top-level key: benchmark_policy.
    Required benchmark_policy keys: name, dataset, seed, gates.
    """
    p = Path(path)
    data = _load_yaml(p)
    _require_keys(data, ["benchmark_policy"], f"benchmark policy ({p.name})")
    _require_keys(
        data["benchmark_policy"],
        ["name", "dataset", "seed", "gates"],
        f"benchmark_policy section ({p.name})",
    )
    return data
