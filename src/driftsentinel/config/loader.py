"""Shared configuration loader for dataset contracts, drift policies, and benchmark policies.

Loads YAML configuration files and validates required fields. All three
domain packages (intake, drift, benchmark) use this shared surface
instead of maintaining separate config parsers.
"""

from __future__ import annotations

from importlib import resources
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import Any

import yaml


class ConfigError(Exception):
    """Raised when a configuration file is missing required fields."""


def _load_yaml(source: Path | Traversable, *, source_name: str | None = None) -> dict[str, Any]:
    """Load and parse a YAML file from disk or packaged resources."""
    with source.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    label = source_name or getattr(source, "name", str(source))
    if not isinstance(data, dict):
        raise ConfigError(f"Expected a YAML mapping in {label}, got {type(data).__name__}")
    return data


def _require_keys(data: dict[str, Any], keys: list[str], context: str) -> None:
    """Raise ConfigError if any required key is missing from data."""
    missing = [k for k in keys if k not in data]
    if missing:
        raise ConfigError(f"Missing required keys in {context}: {', '.join(missing)}")


def _packaged_template(template_name: str) -> Traversable:
    """Return a packaged template resource, falling back to the source tree."""
    template = resources.files("driftsentinel").joinpath("templates").joinpath(template_name)
    if template.is_file():
        return template

    source_template = Path(__file__).resolve().parents[3] / "templates" / template_name
    if source_template.is_file():
        return source_template

    raise ConfigError(f"Packaged template not found: {template_name}")


def _validate_dataset_contract(data: dict[str, Any], context: str) -> dict[str, Any]:
    _require_keys(data, ["dataset", "contract"], context)
    _require_keys(
        data["contract"],
        ["required_columns", "business_key", "batch_identifier"],
        f"contract section ({context})",
    )
    return data


def load_dataset_contract(path: str | Path) -> dict[str, Any]:
    """Load a dataset contract YAML and validate required fields.

    Required top-level keys: dataset, contract.
    Required contract keys: required_columns, business_key, batch_identifier.
    """
    p = Path(path)
    data = _load_yaml(p)
    return _validate_dataset_contract(data, f"dataset contract ({p.name})")


def load_packaged_dataset_contract(template_name: str = "dataset_contract.yml") -> dict[str, Any]:
    """Load the example dataset contract packaged with DriftSentinel."""
    template = _packaged_template(template_name)
    data = _load_yaml(template, source_name=template_name)
    return _validate_dataset_contract(data, f"dataset contract ({template_name})")


def _validate_drift_policy(data: dict[str, Any], context: str) -> dict[str, Any]:
    _require_keys(data, ["drift_policy"], context)
    _require_keys(
        data["drift_policy"],
        ["name", "dataset", "monitored_columns", "gates"],
        f"drift_policy section ({context})",
    )
    return data


def load_drift_policy(path: str | Path) -> dict[str, Any]:
    """Load a drift policy YAML and validate required fields.

    Required top-level key: drift_policy.
    Required drift_policy keys: name, dataset, monitored_columns, gates.
    """
    p = Path(path)
    data = _load_yaml(p)
    return _validate_drift_policy(data, f"drift policy ({p.name})")


def load_packaged_drift_policy(template_name: str = "drift_policy.yml") -> dict[str, Any]:
    """Load the example drift policy packaged with DriftSentinel."""
    template = _packaged_template(template_name)
    data = _load_yaml(template, source_name=template_name)
    return _validate_drift_policy(data, f"drift policy ({template_name})")


def _validate_benchmark_policy(data: dict[str, Any], context: str) -> dict[str, Any]:
    _require_keys(data, ["benchmark_policy"], context)
    _require_keys(
        data["benchmark_policy"],
        ["name", "dataset", "seed", "gates"],
        f"benchmark_policy section ({context})",
    )
    return data


def load_benchmark_policy(path: str | Path) -> dict[str, Any]:
    """Load a benchmark policy YAML and validate required fields.

    Required top-level key: benchmark_policy.
    Required benchmark_policy keys: name, dataset, seed, gates.
    """
    p = Path(path)
    data = _load_yaml(p)
    return _validate_benchmark_policy(data, f"benchmark policy ({p.name})")


def load_packaged_benchmark_policy(template_name: str = "benchmark_policy.yml") -> dict[str, Any]:
    """Load the example benchmark policy packaged with DriftSentinel."""
    template = _packaged_template(template_name)
    data = _load_yaml(template, source_name=template_name)
    return _validate_benchmark_policy(data, f"benchmark policy ({template_name})")


_GATE_REQUIRED_KEYS = ["name", "type", "operator", "threshold"]


def normalize_benchmark_gates(policy: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert loaded benchmark policy gates into evaluator-compatible gate dicts.

    Each gate dict must have: name, type, operator, threshold, track, description.
    Raises ``ConfigError`` if any gate is missing required keys.
    """
    raw_gates = policy.get("benchmark_policy", {}).get("gates", [])
    if not isinstance(raw_gates, list):
        raise ConfigError(
            f"Expected 'gates' to be a list of gate definitions, "
            f"got {type(raw_gates).__name__}"
        )

    normalized: list[dict[str, Any]] = []
    for i, gate in enumerate(raw_gates):
        if not isinstance(gate, dict):
            raise ConfigError(
                f"Gate at index {i} must be a mapping, got {type(gate).__name__}"
            )
        missing = [k for k in _GATE_REQUIRED_KEYS if k not in gate]
        if missing:
            raise ConfigError(
                f"Gate at index {i} ({gate.get('name', '?')}) missing keys: "
                f"{', '.join(missing)}"
            )
        normalized.append({
            "name": gate["name"],
            "type": gate["type"],
            "operator": gate["operator"],
            "threshold": float(gate["threshold"]),
            "track": gate.get("track", ""),
            "description": gate.get("description", ""),
        })

    return normalized
