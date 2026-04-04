"""Trusted path helpers for DriftSentinel file surfaces.

The product reads and writes operator-controlled artifacts, but those path
inputs must stay inside explicit trusted roots. By default, the repository
root, temp directories, and the configured app registry/evidence locations are
trusted. Additional roots can be supplied through
``DRIFTSENTINEL_ALLOWED_PATH_ROOTS``.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Iterable

_REPO_ROOT = Path(__file__).resolve().parents[2]


class PathSecurityError(ValueError):
    """Raised when a path escapes DriftSentinel's trusted roots."""


def _normalized_path(value: str | Path) -> str:
    """Return a normalized absolute path string."""
    raw = os.path.expanduser(os.fspath(value))
    if raw.startswith("dbfs:/"):
        raw = os.path.join("/dbfs", raw[len("dbfs:/"):].lstrip("/"))
    return os.path.abspath(os.path.normpath(raw))


def _resolved_root(value: str | Path) -> str:
    """Return a symlink-resolved root path for trusted aliases."""
    return os.path.realpath(os.path.expanduser(os.fspath(value)))


def _has_path_prefix(path: str, root: str) -> bool:
    """Return True when ``path`` is equal to or nested under ``root``."""
    if root == os.sep:
        return path.startswith(root)
    root_prefix = root.rstrip(os.sep) + os.sep
    return path == root.rstrip(os.sep) or path.startswith(root_prefix)


def _configured_surface_roots() -> list[Path]:
    """Return trusted roots derived from explicit runtime configuration."""
    roots: list[Path] = []

    registry_path = os.environ.get("REGISTRY_PATH", "").strip()
    if registry_path:
        roots.append(Path(registry_path).expanduser().parent)

    evidence_dir = os.environ.get("EVIDENCE_DIR", "").strip()
    if evidence_dir:
        roots.append(Path(evidence_dir).expanduser())

    return roots


def _environment_roots(env_var: str) -> list[Path]:
    """Parse a path-list environment variable into Path objects."""
    raw = os.environ.get(env_var, "").strip()
    if not raw:
        return []
    return [Path(item).expanduser() for item in raw.split(os.pathsep) if item.strip()]


def trusted_roots(extra_roots: Iterable[str | Path] = ()) -> tuple[str, ...]:
    """Return normalized trusted root paths in precedence order."""
    candidates: list[Path] = [
        _REPO_ROOT,
        Path(tempfile.gettempdir()),
        Path("/tmp"),
        *_configured_surface_roots(),
        *_environment_roots("DRIFTSENTINEL_ALLOWED_PATH_ROOTS"),
        *[Path(root).expanduser() for root in extra_roots],
    ]

    roots: list[str] = []
    for candidate in candidates:
        aliases = (_normalized_path(candidate), _resolved_root(candidate))
        for normalized in aliases:
            if normalized not in roots:
                roots.append(normalized)
    return tuple(roots)


def resolve_trusted_path(
    path: str | Path,
    *,
    context: str,
    extra_roots: Iterable[str | Path] = (),
    allowed_suffixes: Iterable[str] | None = None,
) -> Path:
    """Normalize a path and ensure it stays within trusted roots."""
    raw = os.fspath(path).strip() if isinstance(path, str) else os.fspath(path)
    if not raw:
        raise PathSecurityError(f"{context} path is empty.")

    normalized = _normalized_path(raw)
    if allowed_suffixes is not None:
        suffixes = {suffix.lower() for suffix in allowed_suffixes}
        if Path(normalized).suffix.lower() not in suffixes:
            expected = ", ".join(sorted(suffixes))
            raise PathSecurityError(f"{context} must use one of {expected}, got: {raw}")

    roots = trusted_roots(extra_roots)
    if not any(_has_path_prefix(normalized, root) for root in roots):
        raise PathSecurityError(f"{context} escapes trusted roots: {raw}")

    return Path(normalized)


def resolve_trusted_dir(
    path: str | Path,
    *,
    context: str,
    extra_roots: Iterable[str | Path] = (),
) -> Path:
    """Normalize and validate a directory path against trusted roots."""
    return resolve_trusted_path(path, context=context, extra_roots=extra_roots)


def resolve_trusted_file(
    path: str | Path,
    *,
    context: str,
    allowed_suffixes: Iterable[str],
    extra_roots: Iterable[str | Path] = (),
) -> Path:
    """Normalize and validate a file path against trusted roots."""
    return resolve_trusted_path(
        path,
        context=context,
        extra_roots=extra_roots,
        allowed_suffixes=allowed_suffixes,
    )


def validate_simple_filename(
    filename: str,
    *,
    context: str,
    allowed_suffixes: Iterable[str] | None = None,
) -> str:
    """Accept only a bare filename, never a nested or absolute path."""
    name = filename.strip()
    if not name:
        raise PathSecurityError(f"{context} filename is empty.")

    normalized = os.path.normpath(name)
    parts = Path(name).parts
    if os.path.isabs(name) or normalized != name or len(parts) != 1 or Path(name).name != name:
        raise PathSecurityError(f"{context} must be a bare filename, got: {filename}")

    if allowed_suffixes is not None:
        suffixes = {suffix.lower() for suffix in allowed_suffixes}
        if Path(name).suffix.lower() not in suffixes:
            expected = ", ".join(sorted(suffixes))
            raise PathSecurityError(f"{context} must use one of {expected}, got: {filename}")

    return name


def resolve_trusted_child(
    root_dir: str | Path,
    child_name: str,
    *,
    context: str,
    extra_roots: Iterable[str | Path] = (),
    allowed_suffixes: Iterable[str] | None = None,
) -> Path:
    """Join a sanitized child filename to a trusted root directory."""
    root = resolve_trusted_dir(root_dir, context=f"{context} directory", extra_roots=extra_roots)
    name = validate_simple_filename(child_name, context=context, allowed_suffixes=allowed_suffixes)
    child = Path(_normalized_path(os.path.join(os.fspath(root), name)))
    if not _has_path_prefix(os.fspath(child), os.fspath(root)):
        raise PathSecurityError(f"{context} escapes trusted directory: {child_name}")
    return child
