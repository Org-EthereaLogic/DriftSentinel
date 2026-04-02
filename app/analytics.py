"""Analytics helpers for the DriftSentinel dashboard.

Builds Pandas DataFrames and Plotly/Gradio-native chart data from
evidence artifacts. All functions are read-only — they never write
evidence or modify state.
"""

from __future__ import annotations

from typing import Any

from driftsentinel.evidence.writer import list_evidence, load_evidence


def _extract_verdict(artifact: dict[str, Any]) -> str:
    """Best-effort extraction of an overall verdict from an evidence payload."""
    payload = artifact.get("payload", {})
    if "overall_verdict" in payload:
        return str(payload["overall_verdict"])
    if "drift" in payload and isinstance(payload["drift"], dict):
        return payload["drift"].get("overall_verdict", "")
    if "benchmark" in payload and isinstance(payload["benchmark"], dict):
        return payload["benchmark"].get("overall_verdict", "")
    return ""


def build_analytics_data(evidence_dir: str) -> list[dict[str, str]]:
    """Scan evidence artifacts and return a list of summary records.

    Each record has: dataset_id, run_kind, generated_at, verdict.
    Malformed files are skipped.
    """
    results = list_evidence(evidence_dir)
    records: list[dict[str, str]] = []
    for r in results:
        if r.get("parse_error"):
            records.append({
                "dataset_id": r.get("dataset_id") or "untagged",
                "run_kind": r.get("run_kind") or "unknown",
                "generated_at": r.get("generated_at", ""),
                "verdict": "UNKNOWN",
            })
            continue
        verdict = ""
        try:
            data = load_evidence(r["file"])
            verdict = _extract_verdict(data)
        except (FileNotFoundError, ValueError):
            continue
        records.append({
            "dataset_id": r.get("dataset_id") or "untagged",
            "run_kind": r.get("run_kind") or "unknown",
            "generated_at": r.get("generated_at", ""),
            "verdict": verdict.strip().upper() if verdict else "UNKNOWN",
        })
    return records


def verdict_bar_data(records: list[dict[str, str]]) -> list[list[Any]]:
    """Return rows for a Gradio BarPlot: [verdict, count]."""
    counts: dict[str, int] = {"PASS": 0, "FAIL": 0, "WARN": 0}
    for rec in records:
        v = rec["verdict"]
        if v in counts:
            counts[v] += 1
    return [[v, c] for v, c in counts.items() if c > 0]


def kind_pie_data(records: list[dict[str, str]]) -> list[list[Any]]:
    """Return rows for a Plotly pie chart: [kind, count]."""
    counts: dict[str, int] = {}
    for rec in records:
        k = rec["run_kind"]
        counts[k] = counts.get(k, 0) + 1
    return [[k, c] for k, c in sorted(counts.items()) if c > 0]


def timeline_data(records: list[dict[str, str]]) -> list[list[Any]]:
    """Return rows for a Gradio LinePlot: [date, count].

    Groups artifacts by date (YYYY-MM-DD) from the generated_at timestamp.
    """
    day_counts: dict[str, int] = {}
    for rec in records:
        ts = rec["generated_at"]
        if not ts:
            continue
        day = ts[:10]  # YYYY-MM-DD prefix
        day_counts[day] = day_counts.get(day, 0) + 1
    return [[d, c] for d, c in sorted(day_counts.items())]


def build_plotly_pie(kind_rows: list[list[Any]]) -> Any:
    """Build a Plotly pie/donut figure from kind data. Returns None if plotly unavailable."""
    if not kind_rows:
        return None
    try:
        import plotly.graph_objects as go
    except ImportError:
        return None

    labels = [r[0] for r in kind_rows]
    values = [r[1] for r in kind_rows]
    colors = {
        "intake": "#20CFE0",
        "drift": "#F59E0B",
        "benchmark": "#22C7A0",
        "pipeline": "#8AA3B6",
        "unknown": "#4A6C80",
    }
    marker_colors = [colors.get(lbl, "#4A6C80") for lbl in labels]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        marker=dict(colors=marker_colors),
        textinfo="label+percent",
        textfont=dict(color="#E6F1F6"),
    )])
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#E6F1F6"),
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(font=dict(color="#8AA3B6")),
        height=320,
    )
    return fig
