"""Trusted data-loading helpers for dataset-backed orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import pandas as pd

from driftsentinel.paths import resolve_trusted_dir, resolve_trusted_path

_JSON_SUFFIXES = (".json", ".jsonl", ".ndjson")
_CSV_SUFFIXES = (".csv",)
_PARQUET_SUFFIXES = (".parquet",)


@dataclass(frozen=True)
class LoadedDataset:
    """A loaded dataset plus traceability metadata."""

    frame: pd.DataFrame
    source_path: str
    source_format: str
    files_loaded: tuple[str, ...]


def _require_source_section(contract: dict[str, Any]) -> dict[str, Any]:
    source = contract.get("source")
    if not isinstance(source, dict):
        raise ValueError(
            "Dataset contract is missing the required 'source' section needed for real-data execution."
        )
    if not source.get("format"):
        raise ValueError("Dataset contract source.format is required for real-data execution.")
    if not source.get("landing_path"):
        raise ValueError("Dataset contract source.landing_path is required for real-data execution.")
    return source


def _normalize_format(raw_format: Any) -> str:
    fmt = str(raw_format or "").strip().lower()
    if not fmt:
        raise ValueError("Dataset source format is empty.")
    return fmt


def _resolve_existing_path(raw_path: str | Path, *, context: str) -> Path:
    path = resolve_trusted_path(raw_path, context=context)
    if not path.exists():
        raise FileNotFoundError(f"{context} not found: {path}")
    return path


def _discover_files(root: Path, *, suffixes: tuple[str, ...], context: str) -> list[Path]:
    if root.is_file():
        if root.suffix.lower() not in suffixes:
            expected = ", ".join(suffixes)
            raise ValueError(f"{context} must use one of {expected}, got: {root.name}")
        return [root]

    if not root.is_dir():
        raise FileNotFoundError(f"{context} not found: {root}")

    trusted_dir = resolve_trusted_dir(root, context=context)
    files = sorted(
        p for p in trusted_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in suffixes
    )
    if not files:
        expected = ", ".join(suffixes)
        raise FileNotFoundError(f"No {expected} files found under {trusted_dir}")
    return files


def _read_json_file(path: Path) -> pd.DataFrame:
    try:
        return pd.read_json(path, lines=True)
    except ValueError:
        return pd.read_json(path)


def _read_parquet_file(path: Path) -> pd.DataFrame:
    try:
        return pd.read_parquet(path)
    except ImportError as exc:
        raise ImportError(
            "Parquet support requires an installed parquet engine such as 'pyarrow'."
        ) from exc


def _read_delta_table(path: Path) -> pd.DataFrame:
    try:
        from deltalake import DeltaTable  # type: ignore[import-not-found]
    except ImportError as exc:
        raise ImportError(
            "Delta support requires the 'deltalake' package to be installed."
        ) from exc

    table = DeltaTable(str(path))
    return cast(pd.DataFrame, table.to_pyarrow_table().to_pandas())


def load_tabular_dataset(
    path: str | Path,
    data_format: str,
    *,
    context: str,
) -> LoadedDataset:
    """Load a trusted tabular dataset from a file or directory."""
    fmt = _normalize_format(data_format)
    resolved = _resolve_existing_path(path, context=context)

    if fmt == "csv":
        files = _discover_files(resolved, suffixes=_CSV_SUFFIXES, context=context)
        frame = pd.concat((pd.read_csv(file) for file in files), ignore_index=True)
    elif fmt == "json":
        files = _discover_files(resolved, suffixes=_JSON_SUFFIXES, context=context)
        frame = pd.concat((_read_json_file(file) for file in files), ignore_index=True)
    elif fmt == "parquet":
        files = _discover_files(resolved, suffixes=_PARQUET_SUFFIXES, context=context)
        frame = pd.concat((_read_parquet_file(file) for file in files), ignore_index=True)
    elif fmt == "delta":
        if resolved.is_file():
            raise ValueError("Delta inputs must be provided as a table directory, not a single file.")
        frame = _read_delta_table(resolved)
        files = [resolved]
    else:
        raise ValueError(
            f"Unsupported dataset format '{fmt}'. Supported formats: csv, json, parquet, delta."
        )

    return LoadedDataset(
        frame=frame.reset_index(drop=True),
        source_path=str(resolved),
        source_format=fmt,
        files_loaded=tuple(str(file) for file in files),
    )


def load_current_dataset(contract: dict[str, Any]) -> LoadedDataset:
    """Load the current/raw dataset defined by a dataset contract."""
    source = _require_source_section(contract)
    return load_tabular_dataset(
        source["landing_path"],
        source["format"],
        context="Dataset landing path",
    )


def _resolve_baseline_config(
    contract: dict[str, Any],
    drift_policy: dict[str, Any],
) -> tuple[str, str]:
    policy = drift_policy.get("drift_policy", {})
    baseline = policy.get("baseline", {})
    if not isinstance(baseline, dict):
        baseline = {}

    baseline_path = (
        baseline.get("path")
        or baseline.get("landing_path")
        or contract.get("source", {}).get("baseline_path")
    )
    if not baseline_path:
        raise ValueError(
            "Dataset-backed drift execution requires a baseline path. "
            "Set drift_policy.baseline.path or contract.source.baseline_path."
        )

    baseline_format = baseline.get("format") or contract.get("source", {}).get("format")
    if not baseline_format:
        raise ValueError(
            "Dataset-backed drift execution requires a baseline format. "
            "Set drift_policy.baseline.format or contract.source.format."
        )

    return str(baseline_path), str(baseline_format)


def load_baseline_dataset(
    contract: dict[str, Any],
    drift_policy: dict[str, Any],
) -> LoadedDataset:
    """Load the trusted baseline dataset referenced by the drift policy."""
    baseline_path, baseline_format = _resolve_baseline_config(contract, drift_policy)
    return load_tabular_dataset(
        baseline_path,
        baseline_format,
        context="Drift baseline path",
    )


def deterministic_sample(df: pd.DataFrame, *, n_rows: int, seed: int) -> pd.DataFrame:
    """Return a deterministic sample no larger than ``n_rows``."""
    if n_rows <= 0:
        raise ValueError("Sample row count must be greater than zero.")
    if len(df) <= n_rows:
        return df.reset_index(drop=True).copy()
    return df.sample(n=n_rows, random_state=seed).reset_index(drop=True)
