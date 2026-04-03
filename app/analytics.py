"""Analytics helpers for the DriftSentinel dashboard.

Builds summary records and Plotly figures from evidence artifacts.
All functions are read-only — they never write evidence or modify
state.
"""

from __future__ import annotations

from typing import Any

from driftsentinel.evidence.writer import list_evidence

COLOR_SCHEMES = {
    "Brand": {
        "verdict": {"PASS": "#22C7A0", "FAIL": "#F97316", "WARN": "#F59E0B", "UNKNOWN": "#8AA3B6"},
        "kind": {
            "intake": "#20CFE0", "drift": "#F59E0B", "benchmark": "#22C7A0",
            "pipeline": "#8AA3B6", "unknown": "#4A6C80"
        },
        "threshold": "#F97316",
        "trend": "#20CFE0"
    },
    "Traffic Light": {
        "verdict": {"PASS": "#22C55E", "FAIL": "#EF4444", "WARN": "#EAB308", "UNKNOWN": "#9CA3AF"},
        "kind": {
            "intake": "#3B82F6", "drift": "#A855F7", "benchmark": "#10B981",
            "pipeline": "#F59E0B", "unknown": "#6B7280"
        },
        "threshold": "#EF4444",
        "trend": "#3B82F6"
    },
    "Colorblind Safe": {
        "verdict": {"PASS": "#009E73", "FAIL": "#D55E00", "WARN": "#F0E442", "UNKNOWN": "#999999"},
        "kind": {
            "intake": "#56B4E9", "drift": "#E69F00", "benchmark": "#009E73",
            "pipeline": "#CC79A7", "unknown": "#999999"
        },
        "threshold": "#D55E00",
        "trend": "#56B4E9"
    },
    "Cyberpunk": {
        "verdict": {"PASS": "#00FF00", "FAIL": "#FF003C", "WARN": "#FFE600", "UNKNOWN": "#00E5FF"},
        "kind": {
            "intake": "#00E5FF", "drift": "#FF003C", "benchmark": "#00FF00",
            "pipeline": "#FFE600", "unknown": "#9D00FF"
        },
        "threshold": "#FF003C",
        "trend": "#00E5FF"
    },
    "Pastel": {
        "verdict": {"PASS": "#86EFAC", "FAIL": "#FCA5A5", "WARN": "#FDE047", "UNKNOWN": "#D1D5DB"},
        "kind": {
            "intake": "#93C5FD", "drift": "#D8B4FE", "benchmark": "#86EFAC",
            "pipeline": "#FDE047", "unknown": "#D1D5DB"
        },
        "threshold": "#FCA5A5",
        "trend": "#93C5FD"
    }
}


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


def build_plotly_bar(verdict_rows: list[list[Any]], theme_name: str = "Brand") -> Any:
    """Build a Plotly bar chart from verdict distribution data."""
    if not verdict_rows:
        return None
    try:
        import plotly.graph_objects as go
    except ImportError:
        return None

    labels = [row[0] for row in verdict_rows]
    values = [row[1] for row in verdict_rows]
    colors = COLOR_SCHEMES.get(theme_name, COLOR_SCHEMES["Brand"])["verdict"]

    fig = go.Figure(
        data=[
            go.Bar(
                x=labels,
                y=values,
                marker_color=[colors.get(label, "#8AA3B6") for label in labels],
                text=values,
                textposition="outside",
                cliponaxis=False,
                hovertemplate="%{x}: %{y}<extra></extra>",
            )
        ]
    )
    fig.update_layout(
        title="Verdict Distribution",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=40, r=20, t=60, b=30),
        showlegend=False,
        height=320,
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(rangemode="tozero", automargin=True)
    return fig


def build_plotly_pie(kind_rows: list[list[Any]], theme_name: str = "Brand") -> Any:
    """Build a Plotly pie/donut figure from kind data. Returns None if plotly unavailable."""
    if not kind_rows:
        return None
    try:
        import plotly.graph_objects as go
    except ImportError:
        return None

    labels = [r[0] for r in kind_rows]
    values = [r[1] for r in kind_rows]
    colors = COLOR_SCHEMES.get(theme_name, COLOR_SCHEMES["Brand"])["kind"]
    marker_colors = [colors.get(lbl, "#4A6C80") for lbl in labels]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        marker=dict(colors=marker_colors),
        textinfo="label+percent",
    )])
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=30, b=20),
        height=320,
    )
    return fig


def build_plotly_daily_volume(timeline_rows: list[list[Any]], theme_name: str = "Brand") -> Any:
    """Build a Plotly Stacked Bar chart for daily artifact volume by verdict."""
    if not timeline_rows:
        return None
    try:
        import plotly.graph_objects as go
    except ImportError:
        return None

    # Aggregate by date and verdict
    from collections import defaultdict
    from datetime import datetime

    daily_counts: dict[str, dict[str, int]] = defaultdict(
        lambda: {"PASS": 0, "FAIL": 0, "WARN": 0, "UNKNOWN": 0}
    )

    for row in timeline_rows:
        ts_str = str(row[0])
        verdict = str(row[3])
        try:
            # Parse ISO 8601 to YYYY-MM-DD
            dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            date_key = dt.strftime("%Y-%m-%d")
        except ValueError:
            date_key = ts_str[:10]  # Fallback formatting

        if verdict in daily_counts[date_key]:
            daily_counts[date_key][verdict] += 1
        else:
            daily_counts[date_key]["UNKNOWN"] += 1

    dates = sorted(list(daily_counts.keys()))

    colors = COLOR_SCHEMES.get(theme_name, COLOR_SCHEMES["Brand"])["verdict"]

    traces = []
    # Sort verdicts to have FAIL/WARN stacked above PASS
    for verdict in ["PASS", "WARN", "FAIL", "UNKNOWN"]:
        y_vals = [daily_counts[d][verdict] for d in dates]
        if sum(y_vals) == 0:
            continue
        traces.append(
            go.Bar(
                name=verdict,
                x=dates,
                y=y_vals,
                marker_color=colors[verdict],
                hovertemplate="%{x}<br>" + verdict + ": %{y}<extra></extra>"
            )
        )

    fig = go.Figure(data=traces)
    fig.update_layout(
        title="Daily Activity Volume",
        barmode="stack",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=40, r=20, t=60, b=30),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        height=320,
    )
    fig.update_xaxes(showgrid=False, type="category")
    fig.update_yaxes(rangemode="tozero", automargin=True)
    return fig


def build_plotly_health_trend(timeline_rows: list[list[Any]], theme_name: str = "Brand") -> Any:
    """Build a Plotly line chart showing daily PASS rate with a 90% threshold."""
    if not timeline_rows:
        return None
    try:
        import plotly.graph_objects as go
    except ImportError:
        return None

    # Aggregate by date
    from collections import defaultdict
    from datetime import datetime

    daily_pass: dict[str, int] = defaultdict(int)
    daily_total: dict[str, int] = defaultdict(int)

    for row in timeline_rows:
        ts_str = str(row[0])
        verdict = str(row[3])
        try:
            dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            date_key = dt.strftime("%Y-%m-%d")
        except ValueError:
            date_key = ts_str[:10]

        daily_total[date_key] += 1
        if verdict == "PASS":
            daily_pass[date_key] += 1

    dates = sorted(list(daily_total.keys()))
    rates = [(daily_pass[d] / daily_total[d] * 100) if daily_total[d] > 0 else 0 for d in dates]

    theme = COLOR_SCHEMES.get(theme_name, COLOR_SCHEMES["Brand"])
    fig = go.Figure()

    # 90% threshold line
    fig.add_trace(go.Scatter(
        x=[dates[0], dates[-1]] if dates else [],
        y=[90, 90],
        mode="lines",
        line=dict(color=theme["threshold"], width=2, dash="dash"),
        name="90% Threshold",
        hoverinfo="skip"
    ))

    # Pass rate line
    fig.add_trace(go.Scatter(
        x=dates,
        y=rates,
        mode="lines+markers",
        name="Pass Rate",
        line=dict(color=theme["trend"], width=2),
        marker=dict(size=8, color=theme["trend"], line=dict(color="#071824", width=1)),
        hovertemplate="%{x}<br>Pass Rate: %{y:.1f}%<extra></extra>"
    ))

    fig.update_layout(
        title="Daily Health Trend (% PASS)",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=40, r=20, t=60, b=30),
        showlegend=False,
        height=320,
    )
    fig.update_xaxes(showgrid=False, type="category")
    fig.update_yaxes(
        range=[0, 105], tickvals=[0, 50, 100],
        ticktext=["0%", "50%", "100%"]
    )
    return fig
