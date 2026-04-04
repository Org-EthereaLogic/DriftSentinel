"""Trusted data-loading helpers for dataset-backed orchestration."""

from __future__ import annotations

import gzip
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import pandas as pd

from driftsentinel.paths import resolve_trusted_dir, resolve_trusted_path

_JSON_SUFFIXES = (".json", ".jsonl", ".ndjson", ".json.gz", ".jsonl.gz", ".ndjson.gz")
_CSV_SUFFIXES = (".csv", ".csv.gz", ".csv.zip")
_TSV_SUFFIXES = (".tsv", ".tab", ".tsv.gz", ".tab.gz")
_TXT_SUFFIXES = (".txt", ".txt.gz")
_EXCEL_SUFFIXES = (".xlsx", ".xlsm", ".xls", ".xlsb")
_PARQUET_SUFFIXES = (".parquet",)
_AVRO_SUFFIXES = (".avro", ".avro.gz")
_ORC_SUFFIXES = (".orc",)
_TABLE_FORMATS = {"table", "spark_table", "unity_catalog_table"}
_FORMAT_ALIASES = {
    "csv": "csv",
    "json": "json",
    "jsonl": "json",
    "ndjson": "json",
    "parquet": "parquet",
    "delta": "delta",
    "tsv": "tsv",
    "tab": "tsv",
    "txt": "txt",
    "text": "txt",
    "excel": "excel",
    "xlsx": "excel",
    "xlsm": "excel",
    "xls": "excel",
    "xlsb": "excel",
    "avro": "avro",
    "orc": "orc",
    "table": "table",
    "spark_table": "table",
    "unity_catalog_table": "table",
}


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
    fmt = _normalize_format(source.get("format"))
    if not source.get("format"):
        raise ValueError("Dataset contract source.format is required for real-data execution.")
    if fmt == "table":
        if _resolve_contract_table_name(contract, source=source) is None:
            raise ValueError(
                "Dataset contract source.format=table requires source.table_name or "
                "dataset.catalog + dataset.schema + dataset.table."
            )
        return source
    if not source.get("landing_path"):
        raise ValueError("Dataset contract source.landing_path is required for real-data execution.")
    return source


def _normalize_format(raw_format: Any) -> str:
    fmt = str(raw_format or "").strip().lower()
    if not fmt:
        raise ValueError("Dataset source format is empty.")
    return _FORMAT_ALIASES.get(fmt, fmt)


def _normalize_table_name(raw_table_name: str) -> str:
    table_name = str(raw_table_name or "").strip()
    if not table_name:
        raise ValueError("Table-backed dataset execution requires a non-empty table name.")
    if any(token in table_name for token in (";", "\n", "\r")):
        raise ValueError(f"Table-backed dataset execution received an unsafe table name: {table_name}")
    parts = table_name.split(".")
    if len(parts) != 3:
        raise ValueError(
            "Table-backed dataset execution requires a fully qualified three-part table name "
            f"(catalog.schema.table), got: {table_name}"
        )
    normalized_parts: list[str] = []
    for part in parts:
        if part != part.strip():
            raise ValueError(
                "Table-backed dataset execution requires table identifiers without surrounding "
                f"whitespace, got: {table_name}"
            )
        clean = part.strip()
        if not clean or any(char.isspace() for char in clean):
            raise ValueError(f"Table-backed dataset execution received an invalid table name: {table_name}")
        normalized_parts.append(clean)
    return ".".join(normalized_parts)


def _resolve_contract_table_name(
    contract: dict[str, Any],
    *,
    source: dict[str, Any] | None = None,
) -> str | None:
    source_section = source if source is not None else contract.get("source", {})
    if isinstance(source_section, dict) and source_section.get("table_name"):
        return _normalize_table_name(str(source_section["table_name"]))

    dataset = contract.get("dataset", {})
    if not isinstance(dataset, dict):
        return None
    catalog = str(dataset.get("catalog") or "").strip()
    schema = str(dataset.get("schema") or "").strip()
    table = str(dataset.get("table") or "").strip()
    if catalog and schema and table:
        return _normalize_table_name(f"{catalog}.{schema}.{table}")
    return None


def _resolve_existing_path(raw_path: str | Path, *, context: str) -> Path:
    path = resolve_trusted_path(raw_path, context=context)
    if not path.exists():
        raise FileNotFoundError(f"{context} not found: {path}")
    return path


def _matches_suffix(path: Path, suffixes: tuple[str, ...]) -> bool:
    return path.name.lower().endswith(suffixes)


def _discover_files(root: Path, *, suffixes: tuple[str, ...], context: str) -> list[Path]:
    if root.is_file():
        if not _matches_suffix(root, suffixes):
            expected = ", ".join(suffixes)
            raise ValueError(f"{context} must use one of {expected}, got: {root.name}")
        return [root]

    if not root.is_dir():
        raise FileNotFoundError(f"{context} not found: {root}")

    trusted_dir = resolve_trusted_dir(root, context=context)
    files = sorted(
        p for p in trusted_dir.rglob("*")
        if p.is_file() and _matches_suffix(p, suffixes)
    )
    if not files:
        expected = ", ".join(suffixes)
        raise FileNotFoundError(f"No {expected} files found under {trusted_dir}")
    return files


def _read_json_file(path: Path, read_options: dict[str, Any] | None = None) -> pd.DataFrame:
    options = dict(read_options or {})
    try:
        if "lines" not in options:
            options["lines"] = True
        options.setdefault("compression", "infer")
        return _ensure_dataframe(pd.read_json(path, **options), context=f"JSON input '{path.name}'")
    except ValueError:
        options.pop("lines", None)
        return _ensure_dataframe(pd.read_json(path, **options), context=f"JSON input '{path.name}'")


def _ensure_dataframe(frame: Any, *, context: str) -> pd.DataFrame:
    if isinstance(frame, pd.DataFrame):
        return frame
    raise ValueError(
        f"{context} must load into a pandas DataFrame. Adjust read_options to return tabular data, "
        f"got: {type(frame).__name__}."
    )


def _read_parquet_file(path: Path, read_options: dict[str, Any] | None = None) -> pd.DataFrame:
    try:
        return _ensure_dataframe(
            pd.read_parquet(path, **dict(read_options or {})),
            context=f"Parquet input '{path.name}'",
        )
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


def _read_excel_file(path: Path, read_options: dict[str, Any] | None = None) -> pd.DataFrame:
    try:
        return _ensure_dataframe(
            pd.read_excel(path, **dict(read_options or {})),
            context=f"Excel input '{path.name}'",
        )
    except ImportError as exc:
        raise ImportError(
            "Excel support requires spreadsheet engines to be installed, such as "
            "'openpyxl', 'pyxlsb', or 'xlrd'."
        ) from exc


def _read_avro_file(path: Path, read_options: dict[str, Any] | None = None) -> pd.DataFrame:
    try:
        from fastavro import reader
    except ImportError as exc:
        raise ImportError("Avro support requires the 'fastavro' package to be installed.") from exc

    if read_options:
        raise ValueError("Avro reader does not currently accept read_options.")

    opener = gzip.open if path.name.lower().endswith(".gz") else open
    with opener(path, "rb") as handle:
        records = cast(list[dict[str, Any]], list(reader(cast(Any, handle))))
    return pd.DataFrame.from_records(records)


def _read_orc_file(path: Path, read_options: dict[str, Any] | None = None) -> pd.DataFrame:
    try:
        return _ensure_dataframe(
            pd.read_orc(path, **dict(read_options or {})),
            context=f"ORC input '{path.name}'",
        )
    except ImportError as exc:
        raise ImportError(
            "ORC support requires an installed ORC-capable engine such as 'pyarrow'."
        ) from exc


def _active_spark_session() -> Any:
    try:
        from pyspark.sql import SparkSession  # type: ignore[import-not-found]
    except ImportError:
        return None
    return SparkSession.getActiveSession()


def _read_spark_table(table_name: str, read_options: dict[str, Any] | None = None) -> pd.DataFrame:
    session = _active_spark_session()
    if session is None:
        raise ImportError(
            "Table-backed dataset execution requires an active Spark session, such as a Databricks notebook "
            "or job cluster with PySpark available."
        )

    options = dict(read_options or {})
    supported = {"columns", "limit"}
    unsupported = sorted(set(options) - supported)
    if unsupported:
        raise ValueError(
            "Table read_options support only 'columns' and 'limit'; "
            f"unsupported options: {', '.join(unsupported)}"
        )

    columns = options.get("columns")
    limit = options.get("limit")
    spark_frame = session.table(table_name)
    if columns is not None:
        if not isinstance(columns, list) or not all(isinstance(item, str) and item.strip() for item in columns):
            raise ValueError("Table read_options.columns must be a list of column names.")
        spark_frame = spark_frame.select(*columns)
    if limit is not None:
        spark_frame = spark_frame.limit(int(limit))
    return _ensure_dataframe(
        cast(pd.DataFrame, spark_frame.toPandas()),
        context=f"Table input '{table_name}'",
    )


def _read_delimited_files(
    files: list[Path],
    *,
    context: str,
    read_options: dict[str, Any] | None = None,
    default_separator: str | None = None,
    sniff_delimiter: bool = False,
) -> pd.DataFrame:
    options = dict(read_options or {})
    options.setdefault("compression", "infer")
    if default_separator is not None:
        options.setdefault("sep", default_separator)
        options.setdefault("low_memory", False)
    elif sniff_delimiter and "sep" not in options and "delimiter" not in options:
        options.setdefault("sep", None)
        options.setdefault("engine", "python")
    else:
        options.setdefault("low_memory", False)
    return _concat_named_frames(
        [(str(file), pd.read_csv(file, **options)) for file in files],
        context=context,
    )


def _concat_named_frames(
    named_frames: list[tuple[str, pd.DataFrame]],
    *,
    context: str,
) -> pd.DataFrame:
    if not named_frames:
        raise ValueError(f"{context} did not load any frames.")

    expected_columns = named_frames[0][1].columns.tolist()
    for source_name, frame in named_frames[1:]:
        actual_columns = frame.columns.tolist()
        if actual_columns != expected_columns:
            raise ValueError(
                f"{context} contains schema-mismatched files. Expected columns {expected_columns} "
                f"but '{source_name}' produced {actual_columns}."
            )
    return pd.concat((frame for _, frame in named_frames), ignore_index=True)


def load_tabular_dataset(
    path: str | Path,
    data_format: str,
    *,
    context: str,
    read_options: dict[str, Any] | None = None,
) -> LoadedDataset:
    """Load a trusted tabular dataset from a file or directory."""
    fmt = _normalize_format(data_format)
    files_loaded: tuple[str, ...]

    if fmt == "table":
        table_name = _normalize_table_name(str(path))
        frame = _read_spark_table(table_name, read_options)
        files_loaded = (table_name,)
        source_path = table_name
    else:
        resolved = _resolve_existing_path(path, context=context)
        if fmt == "csv":
            files = _discover_files(resolved, suffixes=_CSV_SUFFIXES, context=context)
            frame = _read_delimited_files(
                files,
                context=context,
                read_options=read_options,
                default_separator=",",
            )
        elif fmt == "tsv":
            files = _discover_files(resolved, suffixes=_TSV_SUFFIXES, context=context)
            frame = _read_delimited_files(
                files,
                context=context,
                read_options=read_options,
                default_separator="\t",
            )
        elif fmt == "txt":
            files = _discover_files(resolved, suffixes=_TXT_SUFFIXES, context=context)
            frame = _read_delimited_files(
                files,
                context=context,
                read_options=read_options,
                sniff_delimiter=True,
            )
        elif fmt == "json":
            files = _discover_files(resolved, suffixes=_JSON_SUFFIXES, context=context)
            frame = _concat_named_frames(
                [(str(file), _read_json_file(file, read_options)) for file in files],
                context=context,
            )
        elif fmt == "excel":
            files = _discover_files(resolved, suffixes=_EXCEL_SUFFIXES, context=context)
            frame = _concat_named_frames(
                [(str(file), _read_excel_file(file, read_options)) for file in files],
                context=context,
            )
        elif fmt == "parquet":
            files = _discover_files(resolved, suffixes=_PARQUET_SUFFIXES, context=context)
            frame = _concat_named_frames(
                [(str(file), _read_parquet_file(file, read_options)) for file in files],
                context=context,
            )
        elif fmt == "avro":
            files = _discover_files(resolved, suffixes=_AVRO_SUFFIXES, context=context)
            frame = _concat_named_frames(
                [(str(file), _read_avro_file(file, read_options)) for file in files],
                context=context,
            )
        elif fmt == "orc":
            files = _discover_files(resolved, suffixes=_ORC_SUFFIXES, context=context)
            frame = _concat_named_frames(
                [(str(file), _read_orc_file(file, read_options)) for file in files],
                context=context,
            )
        elif fmt == "delta":
            if resolved.is_file():
                raise ValueError("Delta inputs must be provided as a table directory, not a single file.")
            frame = _read_delta_table(resolved)
            files = [resolved]
        else:
            raise ValueError(
                f"Unsupported dataset format '{fmt}'. Supported formats: csv, tsv, txt, json, excel, parquet, "
                "avro, orc, delta, table."
            )
        files_loaded = tuple(str(file) for file in files)
        source_path = str(resolved)

    return LoadedDataset(
        frame=frame.reset_index(drop=True),
        source_path=source_path,
        source_format=fmt,
        files_loaded=files_loaded,
    )


def _resolve_read_options(config: dict[str, Any]) -> dict[str, Any] | None:
    raw = config.get("read_options")
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError("Dataset read_options must be provided as a mapping.")
    return dict(raw)


def load_current_dataset(contract: dict[str, Any]) -> LoadedDataset:
    """Load the current/raw dataset defined by a dataset contract."""
    source = _require_source_section(contract)
    fmt = _normalize_format(source["format"])
    current_reference = (
        _resolve_contract_table_name(contract, source=source)
        if fmt == "table"
        else source["landing_path"]
    )
    if current_reference is None:
        raise ValueError("Dataset-backed execution could not resolve the current table reference.")
    return load_tabular_dataset(
        current_reference,
        fmt,
        context="Dataset landing path",
        read_options=_resolve_read_options(source),
    )


def _resolve_baseline_config(
    contract: dict[str, Any],
    drift_policy: dict[str, Any],
) -> tuple[str, str, dict[str, Any]]:
    policy = drift_policy.get("drift_policy", {})
    baseline = policy.get("baseline", {})
    if not isinstance(baseline, dict):
        baseline = {}

    baseline_format = _normalize_format(baseline.get("format") or contract.get("source", {}).get("format"))

    baseline_reference = (
        baseline.get("table_name") or baseline.get("path") or baseline.get("landing_path")
        if baseline_format == "table"
        else baseline.get("path") or baseline.get("landing_path")
    )
    if baseline_reference is None:
        baseline_reference = contract.get("source", {}).get(
            "baseline_table_name" if baseline_format == "table" else "baseline_path"
        )
    if not baseline_reference:
        raise ValueError(
            "Dataset-backed drift execution requires a baseline reference. "
            "Set drift_policy.baseline.path/table_name or contract.source.baseline_path/baseline_table_name."
        )
    if not baseline_format:
        raise ValueError(
            "Dataset-backed drift execution requires a baseline format. "
            "Set drift_policy.baseline.format or contract.source.format."
        )

    baseline_read_options = baseline.get("read_options")
    if baseline_read_options is None:
        baseline_read_options = contract.get("source", {}).get("read_options")
    if baseline_read_options is not None and not isinstance(baseline_read_options, dict):
        raise ValueError("Dataset-backed drift execution requires baseline read_options to be a mapping.")

    return str(baseline_reference), baseline_format, dict(baseline_read_options or {})


def load_baseline_dataset(
    contract: dict[str, Any],
    drift_policy: dict[str, Any],
) -> LoadedDataset:
    """Load the trusted baseline dataset referenced by the drift policy."""
    baseline_path, baseline_format, baseline_read_options = _resolve_baseline_config(
        contract, drift_policy
    )
    return load_tabular_dataset(
        baseline_path,
        baseline_format,
        context="Drift baseline path",
        read_options=baseline_read_options,
    )


def deterministic_sample(df: pd.DataFrame, *, n_rows: int, seed: int) -> pd.DataFrame:
    """Return a deterministic sample no larger than ``n_rows``."""
    if n_rows <= 0:
        raise ValueError("Sample row count must be greater than zero.")
    if len(df) <= n_rows:
        return df.reset_index(drop=True).copy()
    return df.sample(n=n_rows, random_state=seed).reset_index(drop=True)
