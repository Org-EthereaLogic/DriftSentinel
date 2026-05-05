"""Shared path helpers for DriftSentinel Databricks runtime state."""

from __future__ import annotations

from pathlib import PurePosixPath

DEFAULT_RUNTIME_VOLUME_NAME = "driftsentinel_runtime"


def runtime_volume_root(
    catalog: str,
    schema: str,
    *,
    volume_name: str = DEFAULT_RUNTIME_VOLUME_NAME,
) -> str:
    """Return the shared Unity Catalog volume root for DriftSentinel state."""
    cat = catalog.strip()
    sch = schema.strip()
    vol = volume_name.strip()
    if not cat:
        raise ValueError("Catalog is required to compute the DriftSentinel runtime volume path.")
    if not sch:
        raise ValueError("Schema is required to compute the DriftSentinel runtime volume path.")
    if not vol:
        raise ValueError("Volume name is required to compute the DriftSentinel runtime volume path.")
    return str(PurePosixPath("/Volumes") / cat / sch / vol)


def runtime_registry_path(
    catalog: str,
    schema: str,
    *,
    volume_name: str = DEFAULT_RUNTIME_VOLUME_NAME,
) -> str:
    """Return the shared dataset registry path inside the runtime volume."""
    return str(PurePosixPath(runtime_volume_root(catalog, schema, volume_name=volume_name)) / "state" / "registry.json")


def runtime_evidence_dir(
    catalog: str,
    schema: str,
    *,
    volume_name: str = DEFAULT_RUNTIME_VOLUME_NAME,
) -> str:
    """Return the shared evidence directory inside the runtime volume."""
    return str(PurePosixPath(runtime_volume_root(catalog, schema, volume_name=volume_name)) / "evidence")


def runtime_policies_dir(
    catalog: str,
    schema: str,
    *,
    volume_name: str = DEFAULT_RUNTIME_VOLUME_NAME,
) -> str:
    """Return the shared policies directory inside the runtime volume."""
    return str(PurePosixPath(runtime_volume_root(catalog, schema, volume_name=volume_name)) / "policies")


def runtime_drift_policy_path(
    catalog: str,
    schema: str,
    *,
    volume_name: str = DEFAULT_RUNTIME_VOLUME_NAME,
) -> str:
    """Return the canonical runtime-volume path for the drift policy YAML."""
    return str(PurePosixPath(runtime_policies_dir(catalog, schema, volume_name=volume_name)) / "drift_policy.yml")


def runtime_benchmark_policy_path(
    catalog: str,
    schema: str,
    *,
    volume_name: str = DEFAULT_RUNTIME_VOLUME_NAME,
) -> str:
    """Return the canonical runtime-volume path for the benchmark policy YAML."""
    return str(PurePosixPath(runtime_policies_dir(catalog, schema, volume_name=volume_name)) / "benchmark_policy.yml")
