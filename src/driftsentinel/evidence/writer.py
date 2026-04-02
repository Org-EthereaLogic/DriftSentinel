"""Append-only evidence writing and provenance helpers.

This shared surface is used by intake, drift, and benchmark domains to
produce auditable JSON evidence artifacts. Files are never overwritten
or deleted -- each write creates a new artifact.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _serialize(obj: Any) -> Any:
    """Make an object JSON-serializable by converting dataclass instances."""
    if hasattr(obj, "__dataclass_fields__"):
        return asdict(obj)
    if isinstance(obj, (list, tuple)):
        return [_serialize(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    return obj


def write_evidence(
    output_dir: str | Path,
    filename: str,
    payload: dict[str, Any],
    *,
    run_ts: str | None = None,
) -> Path:
    """Write a single evidence artifact as JSON.

    Creates the output directory if it does not exist. Never overwrites
    an existing file -- appends a numeric suffix if the filename already
    exists.

    Args:
        output_dir: Directory where the artifact will be written.
        filename: Base filename (should end in .json).
        payload: The evidence data to serialize.
        run_ts: Optional timestamp override for deterministic tests.
            Defaults to current UTC time.

    Returns:
        The path to the written file.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    ts = run_ts or datetime.now(timezone.utc).isoformat()

    envelope: dict[str, Any] = {
        "meta": {
            "generated_at": ts,
            "version": "0.1.0",
        },
        "payload": _serialize(payload),
    }

    target = out / filename
    if target.exists():
        stem = target.stem
        suffix = target.suffix
        counter = 1
        while target.exists():
            target = out / f"{stem}_{counter}{suffix}"
            counter += 1

    with open(target, "w", encoding="utf-8") as f:
        json.dump(envelope, f, indent=2, default=str)

    return target


def build_provenance_envelope(
    health_score: float,
    overall_verdict: str,
    columns_checked: int,
    columns_drifted: int,
    row_count_baseline: int,
    row_count_current: int,
    schema_match: bool,
    gate_results: list[dict[str, Any]],
    column_details: list[dict[str, Any]],
    *,
    run_ts: str | None = None,
) -> dict[str, Any]:
    """Build an audit-ready provenance envelope for drift runs.

    This replaces the Chapter 2 ProvenanceEnvelope dataclass with a
    plain dict so it can be written directly via write_evidence.
    """
    ts = run_ts or datetime.now(timezone.utc).isoformat()
    envelope: dict[str, Any] = {
        "run_ts": ts,
        "health_score": health_score,
        "overall_verdict": overall_verdict,
        "columns_checked": columns_checked,
        "columns_drifted": columns_drifted,
        "row_count_baseline": row_count_baseline,
        "row_count_current": row_count_current,
        "schema_match": schema_match,
        "gate_results": gate_results,
        "column_details": column_details,
    }
    return envelope


def write_benchmark_bundle(
    output_dir: str | Path,
    seed: int,
    n_rows: int,
    baseline_quality: Any,
    challenger_quality: Any,
    baseline_drift: Any,
    challenger_drift: Any,
    gate_results: list[Any],
    overall_verdict: str,
    *,
    run_ts: str | None = None,
) -> Path:
    """Write a structured benchmark evidence bundle.

    Adapted from Chapter 3 evidence writer. Uses the shared write_evidence
    surface for consistent append-only behavior.
    """
    ts = run_ts or datetime.now(timezone.utc).isoformat()

    gate_dicts = []
    for gr in gate_results:
        if hasattr(gr, "config"):
            gate_dicts.append({
                "name": gr.config.name,
                "track": getattr(gr.config, "track", ""),
                "type": gr.config.gate_type,
                "threshold": gr.config.threshold,
                "measured": gr.measured_value,
                "verdict": gr.verdict.value if hasattr(gr.verdict, "value") else str(gr.verdict),
            })
        else:
            gate_dicts.append(gr)

    payload = {
        "seed": seed,
        "n_rows": n_rows,
        "quality_track": {
            "baseline": _serialize(baseline_quality),
            "challenger": _serialize(challenger_quality),
        },
        "drift_track": {
            "baseline": _serialize(baseline_drift),
            "challenger": _serialize(challenger_drift),
        },
        "gates": gate_dicts,
        "overall_verdict": overall_verdict,
    }

    filename = f"bench_{seed}_{n_rows}.json"
    return write_evidence(output_dir, filename, payload, run_ts=ts)
