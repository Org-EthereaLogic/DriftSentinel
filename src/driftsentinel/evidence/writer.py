"""Append-only evidence writing and provenance helpers.

This shared surface is used by intake, drift, and benchmark domains to
produce auditable JSON evidence artifacts. Files are never overwritten
or deleted -- each write creates a new artifact.

Phase 3 adds dataset identity metadata, run IDs, and local lookup helpers.
Phase 4 adds an in-memory metadata cache for O(1) repeated lookups.
"""

from __future__ import annotations

import json
import threading
import uuid
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# In-memory metadata cache for evidence lookups
# ---------------------------------------------------------------------------
# Evidence is append-only, so cached metadata never becomes stale.
# The cache tracks which files have been parsed and stores their extracted
# metadata to avoid re-reading on every query.  Thread-safe via a lock.

_cache_lock = threading.Lock()
_metadata_cache: dict[str, dict[str, Any] | None] = {}
# Maps file path string -> parsed summary dict, or None for malformed files


def _serialize(obj: Any) -> Any:
    """Make an object JSON-serializable by converting dataclass instances."""
    if hasattr(obj, "__dataclass_fields__"):
        return asdict(obj)
    if isinstance(obj, (list, tuple)):
        return [_serialize(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    return obj


def generate_run_id() -> str:
    """Generate a unique run identifier."""
    return str(uuid.uuid4())


def _extract_overall_verdict(envelope: dict[str, Any]) -> str:
    """Best-effort extraction of an overall verdict from an evidence envelope."""
    payload = envelope.get("payload", {})
    if not isinstance(payload, dict):
        return ""
    if "overall_verdict" in payload:
        return str(payload["overall_verdict"])

    for section in ("drift", "benchmark"):
        nested = payload.get(section)
        if isinstance(nested, dict) and "overall_verdict" in nested:
            return str(nested["overall_verdict"])
    return ""


def _normalize_date_filter(raw: str | None, *, end_of_day: bool) -> str | None:
    """Normalize `YYYY-MM-DD` inputs into full-day ISO boundaries."""
    if raw is None:
        return None
    value = raw.strip()
    if not value:
        return None
    if len(value) != 10:
        return value
    try:
        day = datetime.fromisoformat(value)
    except ValueError:
        return value
    if end_of_day:
        day = day + timedelta(days=1) - timedelta(microseconds=1)
        return day.isoformat(timespec="microseconds")
    return day.isoformat(timespec="seconds")


def write_evidence(
    output_dir: str | Path,
    filename: str,
    payload: dict[str, Any],
    *,
    run_ts: str | None = None,
    dataset_id: str | None = None,
    contract_version: str | None = None,
    policy_version: str | None = None,
    run_id: str | None = None,
    run_kind: str | None = None,
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
        dataset_id: Dataset identifier for multi-dataset traceability.
        contract_version: Dataset contract version.
        policy_version: Policy version used for this run.
        run_id: Unique run identifier for evidence lookup.
        run_kind: Run type (intake, drift, benchmark, pipeline).

    Returns:
        The path to the written file.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    ts = run_ts or datetime.now(timezone.utc).isoformat()

    meta: dict[str, Any] = {
        "generated_at": ts,
        "version": "0.2.0",
    }
    if dataset_id is not None:
        meta["dataset_id"] = dataset_id
    if contract_version is not None:
        meta["contract_version"] = contract_version
    if policy_version is not None:
        meta["policy_version"] = policy_version
    if run_id is not None:
        meta["run_id"] = run_id
    if run_kind is not None:
        meta["run_kind"] = run_kind

    envelope: dict[str, Any] = {
        "meta": meta,
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
    dataset_id: str | None = None,
    contract_version: str | None = None,
    policy_version: str | None = None,
    run_id: str | None = None,
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
    return write_evidence(
        output_dir,
        filename,
        payload,
        run_ts=ts,
        dataset_id=dataset_id,
        contract_version=contract_version,
        policy_version=policy_version,
        run_id=run_id,
        run_kind="benchmark",
    )


# ---------------------------------------------------------------------------
# Phase 3: Evidence Lookup Helpers
# ---------------------------------------------------------------------------


def _parse_evidence_file(p: Path) -> dict[str, Any] | None:
    """Parse a single evidence file and return its summary dict, or None if malformed."""
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None

    if not isinstance(data, dict) or "meta" not in data:
        return None

    meta = data["meta"]
    return {
        "file": str(p),
        "generated_at": meta.get("generated_at", ""),
        "dataset_id": meta.get("dataset_id"),
        "contract_version": meta.get("contract_version"),
        "overall_verdict": _extract_overall_verdict(data).strip().upper(),
        "policy_version": meta.get("policy_version"),
        "run_id": meta.get("run_id"),
        "run_kind": meta.get("run_kind"),
    }


def invalidate_evidence_cache(evidence_dir: str | Path | None = None) -> None:
    """Clear the in-memory metadata cache.

    Args:
        evidence_dir: If provided, only clear entries for this directory.
            If None, clear the entire cache.
    """
    with _cache_lock:
        if evidence_dir is None:
            _metadata_cache.clear()
        else:
            prefix = str(Path(evidence_dir))
            keys_to_remove = [k for k in _metadata_cache if k.startswith(prefix)]
            for k in keys_to_remove:
                del _metadata_cache[k]


def list_evidence(
    evidence_dir: str | Path,
    *,
    dataset_id: str | None = None,
    run_kind: str | None = None,
    run_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict[str, Any]]:
    """List evidence artifacts with optional filtering.

    Uses an in-memory metadata cache to avoid re-parsing files on repeated
    queries.  Evidence is append-only, so cached entries never become stale.
    Only new files (not yet in cache) are parsed on each call.

    Args:
        evidence_dir: Directory containing evidence JSON artifacts.
        dataset_id: Filter to artifacts for this dataset.
        run_kind: Filter to artifacts of this run kind.
        run_id: Filter to artifacts with this run ID.
        date_from: ISO date string; include artifacts generated at or after.
        date_to: ISO date string; include artifacts generated at or before.

    Returns:
        A list of summary dicts sorted by generated_at descending.
    """
    d = Path(evidence_dir)
    if not d.is_dir():
        return []

    date_from_filter = _normalize_date_filter(date_from, end_of_day=False)
    date_to_filter = _normalize_date_filter(date_to, end_of_day=True)
    has_filters = any(v is not None for v in (dataset_id, run_kind, run_id, date_from, date_to))

    # Glob directory and parse only uncached files (append-only, so cache is stable)
    all_paths = sorted(d.glob("*.json"))

    with _cache_lock:
        for p in all_paths:
            key = str(p)
            if key not in _metadata_cache:
                _metadata_cache[key] = _parse_evidence_file(p)

    # Build results from cache — filter in-memory without touching disk
    results: list[dict[str, Any]] = []
    with _cache_lock:
        for p in all_paths:
            entry = _metadata_cache.get(str(p))

            if entry is None:
                if not has_filters:
                    results.append({
                        "file": str(p),
                        "parse_error": True,
                    })
                continue

            if dataset_id is not None and entry.get("dataset_id") != dataset_id:
                continue
            if run_kind is not None and entry.get("run_kind") != run_kind:
                continue
            if run_id is not None and not (entry.get("run_id") or "").startswith(run_id):
                continue

            generated_at = entry.get("generated_at", "")
            if date_from_filter is not None and generated_at < date_from_filter:
                continue
            if date_to_filter is not None and generated_at > date_to_filter:
                continue

            results.append(dict(entry))

    results.sort(key=lambda r: r.get("generated_at", ""), reverse=True)
    return results


def load_evidence(path: str | Path) -> dict[str, Any]:
    """Load a single evidence artifact from disk.

    Raises FileNotFoundError if the file does not exist.
    Raises ValueError if the file is not valid JSON.
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Evidence file not found: {p}")
    try:
        with open(p, encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)
        return data
    except json.JSONDecodeError as exc:
        raise ValueError(f"Malformed evidence file: {p}") from exc
