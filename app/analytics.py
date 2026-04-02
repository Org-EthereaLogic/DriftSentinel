"""Analytics helpers for the DriftSentinel dashboard.

Builds summary records and Plotly figures from evidence artifacts.
All functions are read-only — they never write evidence or modify
state.
"""

from __future__ import annotations

from typing import Any

from driftsentinel.evidence.writer import list_evidence


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
        records.append({
            "dataset_id": r.get("dataset_id") or "untagged",
            "run_kind": r.get("run_kind") or "unknown",
            "generated_at": r.get("generated_at", ""),
            "verdict": (r.get("overall_verdict") or "UNKNOWN").strip().upper(),
        })
    return records


def verdict_bar_data(records: list[dict[str, str]]) -> list[list[Any]]:
    """Return verdict/count rows."""
    counts: dict[str, int] = {"PASS": 0, "FAIL": 0, "WARN": 0}
    for rec in records:
        v = rec["verdict"]
        if v in counts:
            counts[v] += 1
    return [[v, c] for v, c in counts.items() if c > 0]


def kind_pie_data(records: list[dict[str, str]]) -> list[list[Any]]:
    """Return rows for a kind-distribution chart: [kind, count]."""
    counts: dict[str, int] = {}
    for rec in records:
        k = rec["run_kind"]
        counts[k] = counts.get(k, 0) + 1
    return [[k, c] for k, c in sorted(counts.items()) if c > 0]


def timeline_data(records: list[dict[str, str]]) -> list[list[Any]]:
    """Return rows for an event-level activity timeline.

    Each row contains: [timestamp, run_kind, dataset_id, verdict].
    This preserves the execution sequence instead of flattening
    everything into a single daily count.
    """
    rows: list[list[Any]] = []
    for rec in sorted(records, key=lambda item: item.get("generated_at", "")):
        ts = rec["generated_at"]
        if not ts:
            continue
        rows.append([
            ts,
            rec.get("run_kind") or "unknown",
            rec.get("dataset_id") or "untagged",
            rec.get("verdict") or "UNKNOWN",
        ])
    return rows


def build_plotly_bar(verdict_rows: list[list[Any]]) -> Any:
    """Build a Plotly bar chart from verdict distribution data."""
    if not verdict_rows:
        return None
    try:
        import plotly.graph_objects as go
    except ImportError:
        return None

    labels = [row[0] for row in verdict_rows]
    values = [row[1] for row in verdict_rows]
    colors = {"PASS": "#22C7A0", "FAIL": "#F97316", "WARN": "#F59E0B"}

    fig = go.Figure(
        data=[
            go.Bar(
                x=labels,
                y=values,
                marker_color=[colors.get(label, "#8AA3B6") for label in labels],
                text=values,
                textposition="outside",
                hovertemplate="%{x}: %{y}<extra></extra>",
            )
        ]
    )
    fig.update_layout(
        title="Verdict Distribution",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#E6F1F6"),
        margin=dict(l=40, r=20, t=50, b=30),
        showlegend=False,
        height=320,
    )
    fig.update_xaxes(color="#8AA3B6", gridcolor="rgba(0,0,0,0)")
    fig.update_yaxes(color="#8AA3B6", gridcolor="#1A3A4A", rangemode="tozero")
    return fig


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


def build_plotly_timeline(timeline_rows: list[list[Any]]) -> Any:
    """Build a Plotly activity timeline from event-level timeline data."""
    if not timeline_rows:
        return None
    try:
        import plotly.graph_objects as go
    except ImportError:
        return None

    timestamps = [row[0] for row in timeline_rows]
    run_kinds = [row[1] for row in timeline_rows]
    customdata = [[row[2], row[3]] for row in timeline_rows]
    verdict_colors = {
        "PASS": "#22C7A0",
        "FAIL": "#F97316",
        "WARN": "#F59E0B",
        "UNKNOWN": "#8AA3B6",
    }

    fig = go.Figure(
        data=[
            go.Scatter(
                x=timestamps,
                y=run_kinds,
                mode="markers",
                customdata=customdata,
                marker=dict(
                    color=[verdict_colors.get(row[3], "#8AA3B6") for row in timeline_rows],
                    size=11,
                    line=dict(color="#071824", width=1),
                ),
                hovertemplate=(
                    "Timestamp: %{x}<br>"
                    "Run Kind: %{y}<br>"
                    "Dataset: %{customdata[0]}<br>"
                    "Verdict: %{customdata[1]}<extra></extra>"
                ),
            )
        ]
    )
    fig.update_layout(
        title="Run Activity Timeline",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#E6F1F6"),
        margin=dict(l=40, r=20, t=50, b=30),
        showlegend=False,
        height=280,
    )
    fig.update_xaxes(
        title="Artifact Timestamp",
        color="#8AA3B6",
        gridcolor="#1A3A4A",
        tickformat="%b %d\n%H:%M:%S",
    )
    fig.update_yaxes(
        title="Run Kind",
        color="#8AA3B6",
        gridcolor="#1A3A4A",
        categoryorder="array",
        categoryarray=["intake", "drift", "benchmark", "pipeline", "unknown"],
    )
    return fig
