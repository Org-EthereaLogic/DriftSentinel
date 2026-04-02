"""Deterministic sample data generator for the four intake test scenarios.

Each batch exercises a specific enterprise intake failure mode:
  - batch_001_clean:        All rows valid, no drift, no replay
  - batch_002_schema_drift: Extra column, type mismatch, field rename
  - batch_003_replay:       Same batch_id as batch_001, different file name
  - batch_004_partial:      Null required fields, negative order_total

Ported from Chapter 1 (trusted-source-intake) as first-party DriftSentinel code.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

_BASE_TS = datetime(2026, 3, 15, 8, 0, 0, tzinfo=timezone.utc)


def _ts(offset_hours: int) -> str:
    return (_BASE_TS + timedelta(hours=offset_hours)).isoformat()


def batch_001_clean() -> list[dict[str, Any]]:
    """10 valid order rows -- baseline for downstream counts."""
    return [
        {
            "batch_id": "B-001",
            "order_id": f"ORD-{1000 + i}",
            "customer_id": f"CUST-{200 + i}",
            "order_total": round(50.0 + i * 12.5, 2),
            "event_ts": _ts(i),
            "product_category": ["Electronics", "Apparel", "Home", "Grocery", "Auto"][i % 5],
            "region": ["West", "East", "Central", "South", "North"][i % 5],
        }
        for i in range(10)
    ]


def batch_002_schema_drift() -> list[dict[str, Any]]:
    """8 rows with schema problems Auto Loader would rescue."""
    rows: list[dict[str, Any]] = []
    for i in range(3):
        rows.append({
            "batch_id": "B-002",
            "order_id": f"ORD-{2000 + i}",
            "customer_id": f"CUST-{300 + i}",
            "order_total": round(75.0 + i * 10, 2),
            "event_ts": _ts(20 + i),
            "product_category": "Electronics",
            "region": "West",
            "loyalty_tier": "Gold",
            "_rescued_data": json.dumps({"loyalty_tier": "Gold"}),
        })
    for i in range(3):
        rows.append({
            "batch_id": "B-002",
            "order_id": f"ORD-{2010 + i}",
            "customer_id": f"CUST-{310 + i}",
            "order_total": None,
            "event_ts": _ts(23 + i),
            "product_category": "Apparel",
            "region": "East",
            "_rescued_data": json.dumps({"order_total": "N/A"}),
        })
    for i in range(2):
        rows.append({
            "batch_id": "B-002",
            "order_id": f"ORD-{2020 + i}",
            "customer_id": f"CUST-{320 + i}",
            "order_total": 99.99,
            "event_ts": None,
            "product_category": "Home",
            "region": "Central",
            "_rescued_data": json.dumps({"Event_TS": _ts(26 + i)}),
        })
    return rows


def batch_003_replay() -> list[dict[str, Any]]:
    """10 rows with the same batch_id as batch_001 -- duplicate replay."""
    rows = batch_001_clean()
    for row in rows:
        row["_source_file_hint"] = "batch_003_replay_of_001.json"
    return rows


def batch_004_partial() -> list[dict[str, Any]]:
    """5 rows with missing required fields and invalid amounts."""
    return [
        {
            "batch_id": None,
            "order_id": "ORD-4000",
            "customer_id": "CUST-400",
            "order_total": 25.00,
            "event_ts": _ts(40),
            "product_category": "Grocery",
            "region": "South",
        },
        {
            "batch_id": "B-004",
            "order_id": None,
            "customer_id": "CUST-401",
            "order_total": 30.00,
            "event_ts": _ts(41),
            "product_category": "Auto",
            "region": "North",
        },
        {
            "batch_id": "B-004",
            "order_id": "ORD-4002",
            "customer_id": None,
            "order_total": 35.00,
            "event_ts": _ts(42),
            "product_category": "Electronics",
            "region": "West",
        },
        {
            "batch_id": "B-004",
            "order_id": "ORD-4003",
            "customer_id": "CUST-403",
            "order_total": -15.00,
            "event_ts": _ts(43),
            "product_category": "Apparel",
            "region": "East",
        },
        {
            "batch_id": "B-004",
            "order_id": "ORD-4004",
            "customer_id": "CUST-404",
            "order_total": 40.00,
            "event_ts": None,
            "product_category": "Home",
            "region": "Central",
        },
    ]


ALL_BATCHES: dict[str, Any] = {
    "batch_001_clean": batch_001_clean,
    "batch_002_schema_drift": batch_002_schema_drift,
    "batch_003_replay": batch_003_replay,
    "batch_004_partial": batch_004_partial,
}
