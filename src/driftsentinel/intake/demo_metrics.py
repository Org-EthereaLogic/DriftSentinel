"""Local demo metrics -- mirrors the SQL handoff summary for offline verification.

Loads all four sample batches, runs contract checks, detects replays,
and produces the same metrics the Databricks pipeline would compute.

Ported from Chapter 1 (trusted-source-intake) as first-party DriftSentinel code.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

from driftsentinel.intake.contracts import evaluate_row
from driftsentinel.intake.sample_data import ALL_BATCHES


@dataclass(frozen=True)
class HandoffSummary:
    """Mirrors ops_handoff_summary fields."""

    total_landed: int
    total_ready: int
    total_quarantined: int
    replay_duplicates: int
    rescued_rows: int
    total_batches: int
    replay_batches: int
    ready_ratio: float
    quarantine_ratio: float


@dataclass(frozen=True)
class BatchRegistryEntry:
    """Mirrors a single row from ops_batch_registry."""

    batch_id: str | None
    file_count: int
    total_rows: int
    is_replay: bool


def compute_demo_metrics() -> tuple[HandoffSummary, list[BatchRegistryEntry]]:
    """Run the full intake demo and return summary + batch registry."""
    all_rows: list[dict[str, Any]] = []
    batch_sources: dict[str | None, list[str]] = {}

    for batch_name, generator in ALL_BATCHES.items():
        rows = generator()
        for row in rows:
            row["_batch_source"] = batch_name
        all_rows.extend(rows)

        for row in rows:
            bid = row.get("batch_id")
            if bid not in batch_sources:
                batch_sources[bid] = []
            if batch_name not in batch_sources[bid]:
                batch_sources[bid].append(batch_name)

    replay_batch_ids = {bid for bid, sources in batch_sources.items() if len(sources) > 1}

    batch_registry: list[BatchRegistryEntry] = []
    batch_row_counts: Counter[str | None] = Counter()
    for row in all_rows:
        batch_row_counts[row.get("batch_id")] += 1

    for bid, sources in batch_sources.items():
        batch_registry.append(BatchRegistryEntry(
            batch_id=bid,
            file_count=len(sources),
            total_rows=batch_row_counts[bid],
            is_replay=bid in replay_batch_ids,
        ))

    total_landed = len(all_rows)
    ready_count = 0
    quarantine_count = 0
    replay_dup_count = 0
    rescued_count = 0
    seen_orders: dict[tuple[str | None, str | None], int] = {}

    for row in all_rows:
        bid = row.get("batch_id")
        oid = row.get("order_id")
        key = (bid, oid)

        is_replay_dup = False
        if bid in replay_batch_ids:
            if key in seen_orders:
                is_replay_dup = True
                replay_dup_count += 1
            else:
                seen_orders[key] = 1

        if row.get("_rescued_data") is not None:
            rescued_count += 1

        violations = evaluate_row(row)

        if violations or is_replay_dup:
            quarantine_count += 1
        else:
            ready_count += 1

    summary = HandoffSummary(
        total_landed=total_landed,
        total_ready=ready_count,
        total_quarantined=quarantine_count,
        replay_duplicates=replay_dup_count,
        rescued_rows=rescued_count,
        total_batches=len(batch_sources),
        replay_batches=len(replay_batch_ids),
        ready_ratio=round(ready_count / total_landed, 4) if total_landed else 0.0,
        quarantine_ratio=round(quarantine_count / total_landed, 4) if total_landed else 0.0,
    )

    return summary, batch_registry
