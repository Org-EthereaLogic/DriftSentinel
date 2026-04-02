"""Sample data generator for drift detection demos.

The baseline has 25 rows with 5 diverse business columns.
The drifted load has 25 rows with 4 of 5 columns collapsed to a single value.

Ported from Chapter 2 (silent-failure-prevention) as first-party DriftSentinel code.
"""

from __future__ import annotations

from typing import Any

MONITORED_COLUMNS = ["department", "region", "product_category", "status", "priority"]

_DEPARTMENTS = ["Engineering", "Sales", "Marketing", "Finance", "Operations"]
_REGIONS = ["West", "East", "Central", "South", "North"]
_CATEGORIES = ["Enterprise", "Mid-Market", "SMB", "Startup", "Government"]
_STATUSES = ["Active", "Pending", "Review", "Approved", "Closed"]
_PRIORITIES = ["Critical", "High", "Medium", "Low", "Deferred"]


def generate_baseline(n_rows: int = 25) -> list[dict[str, Any]]:
    """Generate a diverse baseline dataset."""
    rows: list[dict[str, Any]] = []
    for i in range(n_rows):
        rows.append({
            "record_id": f"REC-{1000 + i}",
            "department": _DEPARTMENTS[i % 5],
            "region": _REGIONS[i % 5],
            "product_category": _CATEGORIES[i % 5],
            "status": _STATUSES[i % 5],
            "priority": _PRIORITIES[i % 5],
            "amount": round(100.0 + i * 23.5, 2),
        })
    return rows


def generate_drifted(n_rows: int = 25) -> list[dict[str, Any]]:
    """Generate a drifted dataset -- 4 of 5 monitored columns collapse."""
    rows: list[dict[str, Any]] = []
    for i in range(n_rows):
        rows.append({
            "record_id": f"REC-{1000 + i}",
            "department": "Engineering",
            "region": "West",
            "product_category": "Enterprise",
            "status": "Active",
            "priority": _PRIORITIES[i % 5],
            "amount": round(100.0 + i * 23.5, 2),
        })
    return rows
