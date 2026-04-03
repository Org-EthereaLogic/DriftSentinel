"""Shared configuration loader for dataset contracts, drift policies, and benchmark policies.

Loads YAML configuration files and validates required fields. All three
domain packages (intake, drift, benchmark) use this shared surface
instead of maintaining separate config parsers.

Phase 3 adds a first-party dataset registry, explicit version metadata,
and policy-to-dataset compatibility checks.
"""

from __future__ import annotations

import json
import os
from importlib import resources
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import Any

import yaml

from driftsentinel.paths import PathSecurityError, resolve_trusted_file, trusted_roots


class ConfigError(Exception):
    """Raised when a configuration file is missing required fields."""


class RegistryError(Exception):
    """Raised on dataset registry collisions, unknown lookups, or version mismatches."""


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
    p = resolve_trusted_file(
        path,
        context="Dataset contract",
        allowed_suffixes=(".yml", ".yaml"),
    )
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
    p = resolve_trusted_file(
        path,
        context="Drift policy",
        allowed_suffixes=(".yml", ".yaml"),
    )
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
    p = resolve_trusted_file(
        path,
        context="Benchmark policy",
        allowed_suffixes=(".yml", ".yaml"),
    )
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


# ---------------------------------------------------------------------------
# Phase 3: Dataset Registry
# ---------------------------------------------------------------------------


def _dataset_identity(contract: dict[str, Any]) -> tuple[str, str]:
    """Extract (dataset_id, contract_version) from a validated dataset contract."""
    ds = contract["dataset"]
    dataset_id = ds["name"]
    contract_version = ds.get("contract_version", "0.0.0")
    return dataset_id, contract_version


def _policy_dataset_binding(
    policy_section: dict[str, Any],
) -> tuple[str, str, str]:
    """Extract (dataset, contract_version, policy_version) from a policy section."""
    dataset = policy_section["dataset"]
    contract_version = policy_section.get("contract_version", "0.0.0")
    policy_version = policy_section.get("policy_version", "0.0.0")
    return dataset, contract_version, policy_version


def _semver_tuple(version: str) -> tuple[int, ...]:
    """Parse a version string into a tuple of ints for correct numeric ordering.

    Handles dotted numeric versions (e.g. "1.0.0", "10.0.0"). Non-numeric
    segments are treated as 0 so the function never raises.
    """
    parts: list[int] = []
    for segment in version.split("."):
        try:
            parts.append(int(segment))
        except ValueError:
            parts.append(0)
    return tuple(parts)


class DatasetRegistry:
    """First-party, serializable dataset registry for multi-dataset operation.

    Stores registered dataset contracts keyed by (dataset_id, contract_version).
    Prevents duplicate collisions and supports lookup by dataset_id with
    optional version filtering.
    """

    def __init__(self) -> None:
        self._entries: dict[tuple[str, str], dict[str, Any]] = {}

    def register(self, contract: dict[str, Any]) -> tuple[str, str]:
        """Register a validated dataset contract.

        Returns (dataset_id, contract_version).
        Raises RegistryError if the same (dataset_id, contract_version) is already registered.
        """
        _validate_dataset_contract(contract, "registry registration")
        dataset_id, contract_version = _dataset_identity(contract)
        key = (dataset_id, contract_version)
        if key in self._entries:
            raise RegistryError(
                f"Dataset '{dataset_id}' version '{contract_version}' is already registered. "
                f"Use a new contract_version or remove the existing entry first."
            )
        self._entries[key] = contract
        return key

    def get(self, dataset_id: str, contract_version: str | None = None) -> dict[str, Any]:
        """Retrieve a registered dataset contract.

        If contract_version is None, returns the latest registered version
        using semantic-version tuple ordering. Raises RegistryError if not found.
        """
        if contract_version is not None:
            key = (dataset_id, contract_version)
            if key not in self._entries:
                raise RegistryError(
                    f"Dataset '{dataset_id}' version '{contract_version}' is not registered."
                )
            return self._entries[key]

        matches = {k: v for k, v in self._entries.items() if k[0] == dataset_id}
        if not matches:
            raise RegistryError(f"Dataset '{dataset_id}' is not registered.")
        latest_key = max(matches.keys(), key=lambda k: _semver_tuple(k[1]))
        return matches[latest_key]

    def list_datasets(self) -> list[dict[str, str]]:
        """Return a list of registered dataset summaries."""
        return [
            {"dataset_id": did, "contract_version": ver}
            for did, ver in sorted(self._entries.keys())
        ]

    def contains(self, dataset_id: str, contract_version: str | None = None) -> bool:
        """Check whether a dataset is registered."""
        if contract_version is not None:
            return (dataset_id, contract_version) in self._entries
        return any(k[0] == dataset_id for k in self._entries)

    def remove(self, dataset_id: str, contract_version: str) -> None:
        """Remove a registered dataset entry. Raises RegistryError if not found."""
        key = (dataset_id, contract_version)
        if key not in self._entries:
            raise RegistryError(
                f"Dataset '{dataset_id}' version '{contract_version}' is not registered."
            )
        del self._entries[key]

    def save(self, path: str | Path) -> Path:
        """Serialize the registry to a JSON file."""
        p = resolve_trusted_file(
            path,
            context="Registry file",
            allowed_suffixes=(".json",),
        )
        p.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "registry": [
                {
                    "dataset_id": did,
                    "contract_version": ver,
                    "contract": contract,
                }
                for (did, ver), contract in sorted(self._entries.items())
            ]
        }
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return p

    @classmethod
    def load(cls, path: str | Path) -> DatasetRegistry:
        """Deserialize a registry from a JSON file."""
        raw_path = os.path.abspath(os.path.normpath(os.path.expanduser(os.fspath(path))))
        roots = trusted_roots()
        if not any(raw_path == root or raw_path.startswith(f"{root}{os.sep}") for root in roots):
            raise PathSecurityError(f"Registry file escapes trusted roots: {path}")
        p = Path(raw_path)
        if not p.is_file():
            raise RegistryError(f"Registry file not found: {p}")
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or "registry" not in data:
            raise RegistryError(f"Invalid registry file format: {p}")
        reg = cls()
        for entry in data["registry"]:
            reg._entries[(entry["dataset_id"], entry["contract_version"])] = entry["contract"]
        return reg


def check_policy_compatibility(
    registry: DatasetRegistry,
    policy_section: dict[str, Any],
    policy_kind: str,
) -> dict[str, str]:
    """Validate that a policy's dataset binding matches a registered contract.

    Returns a dict with dataset_id, contract_version, and policy_version
    on success. Raises RegistryError on mismatch.
    """
    dataset, contract_version, policy_version = _policy_dataset_binding(policy_section)

    if not registry.contains(dataset, contract_version):
        if registry.contains(dataset):
            registered = [
                e["contract_version"]
                for e in registry.list_datasets()
                if e["dataset_id"] == dataset
            ]
            raise RegistryError(
                f"{policy_kind} references dataset '{dataset}' version '{contract_version}', "
                f"but only versions {registered} are registered."
            )
        raise RegistryError(
            f"{policy_kind} references dataset '{dataset}' which is not registered."
        )

    return {
        "dataset_id": dataset,
        "contract_version": contract_version,
        "policy_version": policy_version,
    }
