"""Seven named contract checks mirroring the SQL quarantine rules.

Each check returns True if the row passes, False if it fails.
The check name matches the SQL CASE expression identifier.

Ported from Chapter 1 (trusted-source-intake) as first-party DriftSentinel code.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


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
