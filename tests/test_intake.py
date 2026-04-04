"""Tests for the intake domain -- contract checks, batch evaluation, and demo metrics.

All data is deterministic and local to DriftSentinel.
"""

from __future__ import annotations

from driftsentinel.intake.contracts import (
    ContractViolation,
    evaluate_batch,
    evaluate_dataframe_contract,
    evaluate_row,
)
from driftsentinel.intake.demo_metrics import compute_demo_metrics
from driftsentinel.intake.sample_data import (
    batch_001_clean,
    batch_002_schema_drift,
    batch_003_replay,
    batch_004_partial,
)

# --- Contract checks on individual rows ---


def test_clean_row_passes_all_checks() -> None:
    row = batch_001_clean()[0]
    violations = evaluate_row(row)
    assert violations == []


_TS = "2026-01-01T00:00:00+00:00"


def test_null_batch_id_detected() -> None:
    row = {"batch_id": None, "order_id": "X", "customer_id": "Y", "order_total": 10, "event_ts": _TS}
    violations = evaluate_row(row)
    names = [v.check_name for v in violations]
    assert "batch_id_not_null" in names


def test_negative_order_total_detected() -> None:
    row = {"batch_id": "B", "order_id": "X", "customer_id": "Y", "order_total": -5, "event_ts": _TS}
    violations = evaluate_row(row)
    names = [v.check_name for v in violations]
    assert "order_total_positive" in names


def test_rescued_data_detected() -> None:
    row = {
        "batch_id": "B", "order_id": "X", "customer_id": "Y",
        "order_total": 10, "event_ts": _TS, "_rescued_data": "{}",
    }
    violations = evaluate_row(row)
    names = [v.check_name for v in violations]
    assert "no_rescued_data" in names


def test_unparseable_event_ts() -> None:
    row = {"batch_id": "B", "order_id": "X", "customer_id": "Y", "order_total": 10, "event_ts": "not-a-date"}
    violations = evaluate_row(row)
    names = [v.check_name for v in violations]
    assert "event_ts_parseable" in names


def test_violation_dataclass_fields() -> None:
    v = ContractViolation(check_name="test", row_index=0, field="f", value=None)
    assert v.check_name == "test"
    assert v.row_index == 0


# --- Batch evaluation ---


def test_batch_001_all_ready() -> None:
    rows = batch_001_clean()
    ready, quarantined, violations = evaluate_batch(rows)
    assert len(ready) == 10
    assert len(quarantined) == 0
    assert len(violations) == 0


def test_batch_002_all_quarantined() -> None:
    rows = batch_002_schema_drift()
    ready, quarantined, violations = evaluate_batch(rows)
    assert len(quarantined) == 8
    assert len(ready) == 0
    assert len(violations) > 0


def test_batch_004_partial_failures() -> None:
    rows = batch_004_partial()
    ready, quarantined, violations = evaluate_batch(rows)
    assert len(quarantined) == 5
    assert len(ready) == 0


def test_evaluate_dataframe_contract_detects_duplicates_and_batch_gaps() -> None:
    import pandas as pd

    df = pd.DataFrame([
        {"id": 1, "batch_id": "B-1", "amount": 10.0},
        {"id": 1, "batch_id": "B-1", "amount": 11.0},
        {"id": 2, "batch_id": None, "amount": 12.0},
    ])
    contract = {
        "contract": {
            "required_columns": [
                {"column_name": "id", "type": "long", "nullable": False},
                {"column_name": "amount", "type": "double", "nullable": False},
            ],
            "business_key": ["id"],
            "batch_identifier": "batch_id",
        }
    }

    result = evaluate_dataframe_contract(df, contract)

    assert result["quarantined"] == 3
    assert result["duplicate_rows"] == 2
    assert result["violation_counts"]["business_key_unique"] == 2
    assert result["violation_counts"]["batch_identifier_not_null"] == 1


def test_evaluate_dataframe_contract_detects_missing_required_columns() -> None:
    import pandas as pd

    df = pd.DataFrame([{"id": 1, "batch_id": "B-1"}])
    contract = {
        "contract": {
            "required_columns": [
                {"column_name": "id", "type": "long", "nullable": False},
                {"column_name": "amount", "type": "double", "nullable": False},
            ],
            "business_key": ["id"],
            "batch_identifier": "batch_id",
        }
    }

    result = evaluate_dataframe_contract(df, contract)

    assert result["schema_valid"] is False
    assert result["schema_missing_columns"] == ["amount"]
    assert result["quarantined"] == 1


# --- Demo metrics ---


def test_demo_metrics_deterministic() -> None:
    summary, registry = compute_demo_metrics()
    assert summary.total_landed == 33
    assert summary.total_batches > 0
    assert summary.replay_batches == 1
    assert summary.replay_duplicates == 10
    assert summary.ready_ratio + summary.quarantine_ratio <= 1.0001


def test_demo_metrics_replay_detection() -> None:
    summary, registry = compute_demo_metrics()
    replay_entries = [e for e in registry if e.is_replay]
    assert len(replay_entries) > 0
    assert any(e.batch_id == "B-001" for e in replay_entries)


def test_batch_003_is_replay_of_001() -> None:
    rows = batch_003_replay()
    assert all(r["batch_id"] == "B-001" for r in rows)
    assert all("_source_file_hint" in r for r in rows)
