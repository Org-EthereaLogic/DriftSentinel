"""Contract checks for demo and dataset-backed intake certification.

Each check returns True if the row passes, False if it fails.
The check name matches the SQL CASE expression identifier.

Ported from Chapter 1 (trusted-source-intake) as first-party DriftSentinel code.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class ContractViolation:
    """A single contract check failure on a row."""

    check_name: str
    row_index: int
    field: str
    value: Any


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------


def batch_id_not_null(row: dict[str, Any]) -> bool:
    return row.get("batch_id") is not None


def order_id_not_null(row: dict[str, Any]) -> bool:
    return row.get("order_id") is not None


def customer_id_not_null(row: dict[str, Any]) -> bool:
    return row.get("customer_id") is not None


def order_total_positive(row: dict[str, Any]) -> bool:
    total = row.get("order_total")
    if total is None:
        return False
    try:
        return float(total) > 0
    except (ValueError, TypeError):
        return False


def event_ts_not_null(row: dict[str, Any]) -> bool:
    return row.get("event_ts") is not None


def event_ts_parseable(row: dict[str, Any]) -> bool:
    """Only applied when event_ts is non-null."""
    ts = row.get("event_ts")
    if ts is None:
        return True  # handled by event_ts_not_null
    try:
        from datetime import datetime

        datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        return True
    except (ValueError, TypeError):
        return False


def no_rescued_data(row: dict[str, Any]) -> bool:
    return row.get("_rescued_data") is None


# ---------------------------------------------------------------------------
# Registry of all checks in evaluation order
# ---------------------------------------------------------------------------

ALL_CHECKS: list[tuple[str, Any, str]] = [
    ("batch_id_not_null", batch_id_not_null, "batch_id"),
    ("order_id_not_null", order_id_not_null, "order_id"),
    ("customer_id_not_null", customer_id_not_null, "customer_id"),
    ("order_total_positive", order_total_positive, "order_total"),
    ("event_ts_not_null", event_ts_not_null, "event_ts"),
    ("event_ts_parseable", event_ts_parseable, "event_ts"),
    ("no_rescued_data", no_rescued_data, "_rescued_data"),
]


def evaluate_row(row: dict[str, Any], row_index: int = 0) -> list[ContractViolation]:
    """Run all 7 checks on a single row. Returns list of violations (empty = pass)."""
    violations: list[ContractViolation] = []
    for check_name, check_fn, field in ALL_CHECKS:
        if not check_fn(row):
            violations.append(
                ContractViolation(
                    check_name=check_name,
                    row_index=row_index,
                    field=field,
                    value=row.get(field),
                )
            )
    return violations


def evaluate_batch(
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[ContractViolation]]:
    """Evaluate a full batch. Returns (ready_rows, quarantined_rows, all_violations)."""
    ready: list[dict[str, Any]] = []
    quarantined: list[dict[str, Any]] = []
    all_violations: list[ContractViolation] = []

    for i, row in enumerate(rows):
        violations = evaluate_row(row, row_index=i)
        if violations:
            quarantined.append(row)
            all_violations.extend(violations)
        else:
            ready.append(row)

    return ready, quarantined, all_violations


_TYPE_ALIASES = {
    "bigint": "integer",
    "boolean": "boolean",
    "bool": "boolean",
    "date": "date",
    "datetime": "timestamp",
    "decimal": "float",
    "double": "float",
    "float": "float",
    "int": "integer",
    "integer": "integer",
    "long": "integer",
    "number": "float",
    "str": "string",
    "string": "string",
    "timestamp": "timestamp",
}


def _contract_type(raw_type: Any) -> str:
    normalized = str(raw_type or "").strip().lower()
    return _TYPE_ALIASES.get(normalized, normalized)


def _false_mask(index: pd.Index) -> pd.Series:
    return pd.Series(False, index=index, dtype=bool)


def _string_type_failures(series: pd.Series) -> pd.Series:
    if pd.api.types.is_string_dtype(series):
        return _false_mask(series.index)
    return series.notna() & ~series.map(lambda value: isinstance(value, str))


def _boolean_type_failures(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return _false_mask(series.index)

    def _is_valid(value: Any) -> bool:
        if pd.isna(value):
            return True
        if isinstance(value, bool):
            return True
        return str(value).strip().lower() in {"true", "false", "1", "0", "yes", "no", "y", "n", "t", "f"}

    return ~series.map(_is_valid)


def _type_failure_mask(series: pd.Series, expected_type: str) -> pd.Series:
    normalized = _contract_type(expected_type)
    non_null = series.notna()

    if normalized == "integer":
        numeric = pd.to_numeric(series, errors="coerce")
        return non_null & ~(numeric.notna() & (numeric % 1 == 0))
    if normalized == "float":
        numeric = pd.to_numeric(series, errors="coerce")
        return non_null & numeric.isna()
    if normalized in {"date", "timestamp"}:
        parsed = pd.to_datetime(series, errors="coerce")
        return non_null & parsed.isna()
    if normalized == "boolean":
        return _boolean_type_failures(series)
    if normalized == "string":
        return _string_type_failures(series)
    return _false_mask(series.index)


def evaluate_dataframe_contract(
    df: pd.DataFrame,
    contract: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate a DataFrame against a declarative dataset contract."""
    contract_spec = contract["contract"]
    required_columns = list(contract_spec.get("required_columns", []))
    business_key = list(contract_spec.get("business_key", []))
    batch_identifier = str(contract_spec.get("batch_identifier", "") or "")

    quarantine_mask = _false_mask(df.index)
    violation_counts: dict[str, int] = {}
    violation_examples: list[dict[str, Any]] = []

    def _record(check_name: str, field: str, mask: pd.Series) -> None:
        if not mask.any():
            return
        count = int(mask.sum())
        violation_counts[check_name] = violation_counts.get(check_name, 0) + count
        violation_examples.append({
            "check_name": check_name,
            "field": field,
            "count": count,
            "sample_row_indices": [int(i) for i in mask[mask].index[:20].tolist()],
        })

    required_names = [str(item["column_name"]) for item in required_columns]
    missing_columns = [name for name in required_names if name not in df.columns]
    if missing_columns:
        quarantine_mask[:] = True

    for column in required_columns:
        name = str(column["column_name"])
        if name not in df.columns:
            continue

        if not bool(column.get("nullable", True)):
            null_mask = df[name].isna()
            quarantine_mask |= null_mask
            _record(f"{name}_not_null", name, null_mask)

        type_mask = _type_failure_mask(df[name], str(column.get("type", "")))
        quarantine_mask |= type_mask
        _record(f"{name}_type_valid", name, type_mask)

    batch_identifier_missing = []
    if batch_identifier and batch_identifier in df.columns:
        batch_mask = df[batch_identifier].isna()
        quarantine_mask |= batch_mask
        _record("batch_identifier_not_null", batch_identifier, batch_mask)
    elif batch_identifier:
        batch_identifier_missing.append(batch_identifier)
        quarantine_mask[:] = True

    duplicate_rows = 0
    duplicate_business_keys: list[str] = []
    if business_key:
        if all(column in df.columns for column in business_key):
            duplicate_mask = df.duplicated(subset=business_key, keep=False)
            quarantine_mask |= duplicate_mask
            duplicate_rows = int(duplicate_mask.sum())
            _record("business_key_unique", ",".join(business_key), duplicate_mask)
        else:
            duplicate_business_keys = [column for column in business_key if column not in df.columns]
            quarantine_mask[:] = True

    rescued_rows = 0
    if "_rescued_data" in df.columns:
        rescued_mask = df["_rescued_data"].notna()
        quarantine_mask |= rescued_mask
        rescued_rows = int(rescued_mask.sum())
        _record("rescued_data_empty", "_rescued_data", rescued_mask)

    total_rows = int(len(df))
    quarantined = int(quarantine_mask.sum())
    ready = total_rows - quarantined

    return {
        "total_rows": total_rows,
        "ready": ready,
        "quarantined": quarantined,
        "violations": int(sum(violation_counts.values()) + len(missing_columns) + len(batch_identifier_missing)),
        "ready_ratio": round(ready / total_rows, 4) if total_rows else 0.0,
        "quarantine_ratio": round(quarantined / total_rows, 4) if total_rows else 0.0,
        "schema_valid": not missing_columns and not batch_identifier_missing and not duplicate_business_keys,
        "schema_missing_columns": missing_columns,
        "business_key_missing_columns": duplicate_business_keys,
        "batch_identifier_missing_columns": batch_identifier_missing,
        "batch_identifier": batch_identifier,
        "business_key": business_key,
        "duplicate_rows": duplicate_rows,
        "rescued_rows": rescued_rows,
        "violation_counts": violation_counts,
        "violation_examples": violation_examples,
        "quarantined_row_indices_sample": [int(i) for i in quarantine_mask[quarantine_mask].index[:50].tolist()],
    }
