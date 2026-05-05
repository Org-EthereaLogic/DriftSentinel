"""Create runtime volume layout and upload files via the Databricks SDK Files API."""

from __future__ import annotations

import sys
from pathlib import Path, PurePosixPath
from typing import Any

from driftsentinel.runtime_paths import (
    DEFAULT_RUNTIME_VOLUME_NAME,
    runtime_benchmark_policy_path,
    runtime_drift_policy_path,
    runtime_evidence_dir,
    runtime_registry_path,
    runtime_volume_root,
)

VOLUME_SUBDIRS = ("state", "policies", "evidence")


def _volume_root(catalog: str, schema: str, volume_name: str) -> str:
    return runtime_volume_root(catalog, schema, volume_name=volume_name)


def ensure_volume_layout(
    client: Any,
    *,
    catalog: str,
    schema: str,
    volume_name: str = DEFAULT_RUNTIME_VOLUME_NAME,
    dataset_id: str | None = None,
    landing_subdir: str = "landing",
    baseline_subdir: str = "baseline",
) -> dict[str, str]:
    """Create the standard subdirectories inside the runtime volume.

    Returns a dict mapping logical names to volume paths.
    """
    root = _volume_root(catalog, schema, volume_name)
    paths: dict[str, str] = {
        "root": root,
        "state": str(PurePosixPath(root) / "state"),
        "policies": str(PurePosixPath(root) / "policies"),
        "evidence": runtime_evidence_dir(catalog, schema, volume_name=volume_name),
        "registry": runtime_registry_path(catalog, schema, volume_name=volume_name),
    }

    if dataset_id:
        paths["landing"] = str(PurePosixPath(root) / landing_subdir / dataset_id)
        paths["baseline"] = str(PurePosixPath(root) / baseline_subdir / dataset_id)

    for subdir in VOLUME_SUBDIRS:
        _ensure_dir(client, str(PurePosixPath(root) / subdir))

    if dataset_id:
        _ensure_dir(client, paths["landing"])
        _ensure_dir(client, paths["baseline"])

    return paths


def _ensure_dir(client: Any, path: str) -> None:
    """Create a directory marker in the volume (idempotent)."""
    marker = str(PurePosixPath(path) / ".driftsentinel_marker")
    try:
        client.files.get_status(marker)
    except Exception:
        try:
            client.files.upload(marker, b"", overwrite=True)
            print(f"  Created {path}/", file=sys.stderr)
        except Exception as exc:
            print(f"  Warning: could not create {path}/: {exc}", file=sys.stderr)


def upload_file(
    client: Any,
    local_path: str | Path,
    remote_path: str,
) -> str:
    """Upload a single file to the runtime volume. Returns the remote path."""
    local = Path(local_path)
    if not local.is_file():
        raise FileNotFoundError(f"Local file not found: {local}")

    with open(local, "rb") as fh:
        client.files.upload(remote_path, fh, overwrite=True)
    print(f"  Uploaded {local.name} -> {remote_path}", file=sys.stderr)
    return remote_path


def upload_directory(
    client: Any,
    local_dir: str | Path,
    remote_dir: str,
) -> list[str]:
    """Upload all files in a local directory to a remote volume directory."""
    local = Path(local_dir)
    if not local.is_dir():
        raise FileNotFoundError(f"Local directory not found: {local}")

    uploaded: list[str] = []
    for entry in sorted(local.iterdir()):
        if entry.is_file() and not entry.name.startswith("."):
            remote = str(PurePosixPath(remote_dir) / entry.name)
            upload_file(client, entry, remote)
            uploaded.append(remote)
    return uploaded


def sync_files(
    client: Any,
    *,
    catalog: str,
    schema: str,
    volume_name: str = DEFAULT_RUNTIME_VOLUME_NAME,
    dataset_id: str,
    registry_path: str | Path | None = None,
    drift_policy_path: str | Path | None = None,
    benchmark_policy_path: str | Path | None = None,
    landing_path: str | Path | None = None,
    baseline_path: str | Path | None = None,
) -> dict[str, str]:
    """Upload registry, policy, and data files to the runtime volume.

    Returns a dict mapping logical names to their remote volume paths.
    """
    layout = ensure_volume_layout(
        client,
        catalog=catalog,
        schema=schema,
        volume_name=volume_name,
        dataset_id=dataset_id,
    )
    remote: dict[str, str] = dict(layout)

    if registry_path:
        remote["registry"] = upload_file(client, registry_path, layout["registry"])

    if drift_policy_path:
        dest = runtime_drift_policy_path(catalog, schema, volume_name=volume_name)
        remote["drift_policy"] = upload_file(client, drift_policy_path, dest)

    if benchmark_policy_path:
        dest = runtime_benchmark_policy_path(catalog, schema, volume_name=volume_name)
        remote["benchmark_policy"] = upload_file(client, benchmark_policy_path, dest)

    if landing_path:
        uploaded = upload_directory(client, landing_path, layout["landing"])
        if uploaded:
            remote["landing_files"] = ", ".join(uploaded)

    if baseline_path:
        uploaded = upload_directory(client, baseline_path, layout["baseline"])
        if uploaded:
            remote["baseline_files"] = ", ".join(uploaded)

    return remote
