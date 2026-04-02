"""DriftSentinel Databricks App — read-only operator dashboard.

Provides four views over existing DriftSentinel package surfaces:
1. Registry View — browse registered datasets and policy compatibility
2. Run Status — filter and summarize recent control runs
3. Evidence Explorer — inspect full evidence artifact detail
4. Analytics — verdict distribution, run-kind breakdown, and run timeline

This app never writes evidence, modifies the registry, or executes controls.
"""

from __future__ import annotations

import json
import os
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from driftsentinel.config.loader import DatasetRegistry, RegistryError
from driftsentinel.evidence.writer import list_evidence, load_evidence

REGISTRY_PATH = os.environ.get("REGISTRY_PATH", "/tmp/driftsentinel_registry.json")
EVIDENCE_DIR = os.environ.get("EVIDENCE_DIR", "/tmp/driftsentinel_evidence")

_MIDNIGHT = "#071824"
_DEEP_SLATE = "#0B2233"
_CLOUD = "#E6F1F6"
_SENTINEL_CYAN = "#20CFE0"
_TRUST_TEAL = "#22C7A0"
_DRIFT_AMBER = "#F59E0B"
_ALERT_CORAL = "#F97316"
_GATE_SLATE = "#8AA3B6"

_ASSETS = Path(__file__).parent.parent / "assets" / "driftsentinel-brand-system"
_LOGO_PATH = _ASSETS / "variants" / "logo-dark.png"
_FAVICON_PATH = str(_ASSETS / "favicons" / "favicon-32x32.png")

def _logo_data_uri() -> str | None:
    """Encode the brand logo as a base64 data URI for inline HTML display."""
    import base64

    if not _LOGO_PATH.is_file():
        return None
    data = _LOGO_PATH.read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:image/png;base64,{b64}"

def _fmt_timestamp(raw: str) -> str:
    """Convert ISO 8601 to compact human-readable form: 'Apr 02, 14:40 UTC'."""
    if not raw:
        return ""
    try:
        dt = datetime.fromisoformat(raw).astimezone(timezone.utc)
        return dt.strftime("%b %d, %H:%M UTC")
    except (ValueError, TypeError):
        return raw

def _fmt_run_id(run_id: str) -> str:
    """Truncate run ID to first 8 characters."""
    return run_id[:8] if len(run_id) > 8 else run_id

def _build_summary_line(rows: list[list[str]]) -> str:
    """Build a Markdown summary with total count and verdict breakdown."""
    if not rows or (len(rows) == 1 and "no artifacts" in rows[0][0]):
        return ""
    total = len(rows)
    counts: dict[str, int] = {"PASS": 0, "FAIL": 0, "WARN": 0}
    other = 0
    for row in rows:
        raw = (row[4].strip() if len(row) > 4 else "")
        # Strip colored-circle prefix if present (e.g. "🟢 PASS" -> "PASS")
        v = raw.split()[-1].upper() if raw else ""
        if v in counts:
            counts[v] += 1
        else:
            other += 1
    parts = [f"**{total} artifact{'s' if total != 1 else ''}**"]
    if counts["PASS"]:
        parts.append(f"🟢 PASS: {counts['PASS']}")
    if counts["WARN"]:
        parts.append(f"🟡 WARN: {counts['WARN']}")
    if counts["FAIL"]:
        parts.append(f"🔴 FAIL: {counts['FAIL']}")
    if other:
        parts.append(f"other: {other}")
    return "  |  ".join(parts)

def _extract_artifact_meta(data: dict[str, Any]) -> dict[str, str]:
    """Extract key metadata fields from an evidence artifact for the preview line."""
    meta = data.get("meta", {}) or {}
    payload = data.get("payload", {})
    verdict = (
        str(payload.get("overall_verdict", ""))
        or (payload.get("drift", {}) or {}).get("overall_verdict", "")
        or (payload.get("benchmark", {}) or {}).get("overall_verdict", "")
    )
    run_id = meta.get("run_id", "") or data.get("run_id", "") or ""
    return {
        "dataset_id": meta.get("dataset_id", "") or data.get("dataset_id", "") or "",
        "run_kind": meta.get("run_kind", "") or data.get("run_kind", "") or "",
        "run_id": run_id[:8] if len(run_id) > 8 else run_id,
        "generated_at": _fmt_timestamp(meta.get("generated_at", "") or data.get("generated_at", "") or ""),
        "verdict": verdict,
    }

def load_registry_table(registry_path: str) -> list[list[str]]:
    """Load the registry and return rows for the Gradio table."""
    path = registry_path.strip() or REGISTRY_PATH
    if not Path(path).is_file():
        return [["(no registry file found)", "", "", "", ""]]
    try:
        reg = DatasetRegistry.load(path)
    except RegistryError as exc:
        return [[f"(error: {exc})", "", "", "", ""]]
    datasets = reg.list_datasets()
    if not datasets:
        return [["(no datasets registered)", "", "", "", ""]]
    rows: list[list[str]] = []
    for entry in datasets:
        did = entry["dataset_id"]
        ver = entry["contract_version"]
        contract = reg.get(did, ver)
        ds = contract.get("dataset", {})
        rows.append([did, ver, ds.get("catalog", ""), ds.get("schema", ""), ds.get("table", "")])
    return rows

def _registry_status_text(rows: list[list[str]]) -> str:
    """Return a Markdown status line for the registry result."""
    if not rows:
        return ""
    first = rows[0][0]
    if "no registry" in first:
        return (
            "No registry file found at the path above. "
            "Run `DatasetRegistry` in your intake notebook to create one, then reload."
        )
    if "no datasets" in first:
        return "Registry loaded but contains no datasets. Register a dataset contract and reload."
    if first.startswith("(error"):
        return f"Registry could not be parsed. Check file contents. Detail: `{first}`"
    count = len(rows)
    return f"**{count} dataset{'s' if count != 1 else ''} registered**"

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

def query_evidence(
    evidence_dir: str,
    dataset_id: str,
    run_kind: str,
    run_id: str,
    date_from: str,
    date_to: str,
) -> list[list[str]]:
    """Query evidence and return rows for the summary table."""
    edir = evidence_dir.strip() or EVIDENCE_DIR
    results = list_evidence(
        edir,
        dataset_id=dataset_id.strip() or None,
        run_kind=run_kind.strip() or None,
        run_id=run_id.strip() or None,
        date_from=date_from.strip() or None,
        date_to=date_to.strip() or None,
    )
    if not results:
        return [["(no artifacts found)", "", "", "", "", ""]]
    rows: list[list[str]] = []
    for r in results:
        if r.get("parse_error"):
            rows.append([Path(r["file"]).name, "(malformed)", "", "", "", r["file"]])
            continue
        verdict = ""
        try:
            data = load_evidence(r["file"])
            verdict = _extract_verdict(data)
        except (FileNotFoundError, ValueError):
            pass
        _VERDICT_CIRCLES = {"PASS": "🟢 PASS", "FAIL": "🔴 FAIL", "WARN": "🟡 WARN"}
        verdict = _VERDICT_CIRCLES.get(verdict.strip().upper(), verdict)
        rows.append([
            Path(r["file"]).name,
            r.get("dataset_id", "") or "",
            r.get("run_kind", "") or "",
            _fmt_timestamp(r.get("generated_at", "") or ""),
            verdict,
            _fmt_run_id(r.get("run_id", "") or ""),
        ])
    return rows

def load_artifact_detail(evidence_dir: str, filename: str) -> str:
    """Load and return the full JSON of an evidence artifact."""
    edir = evidence_dir.strip() or EVIDENCE_DIR
    if not filename.strip():
        return "(select an artifact filename)"
    path = Path(edir) / filename.strip()
    if not path.is_file():
        path = Path(filename.strip())
    if not path.is_file():
        return f"(file not found: {filename})"
    try:
        data = load_evidence(path)
        return json.dumps(data, indent=2, default=str)
    except (FileNotFoundError, ValueError) as exc:
        return f"(error: {exc})"

def load_artifact_meta(evidence_dir: str, filename: str) -> str:
    """Return a Markdown one-line metadata summary for an evidence artifact."""
    edir = evidence_dir.strip() or EVIDENCE_DIR
    if not filename.strip():
        return "_Enter an artifact filename above and click Load Artifact._"
    path = Path(edir) / filename.strip()
    if not path.is_file():
        path = Path(filename.strip())
    if not path.is_file():
        return f"_File not found: `{filename}`_"
    try:
        meta = _extract_artifact_meta(load_evidence(path))
        _VERDICT_CIRCLES = {"PASS": "🟢 PASS", "FAIL": "🔴 FAIL", "WARN": "🟡 WARN"}
        raw_verdict = meta["verdict"] or ""
        verdict = _VERDICT_CIRCLES.get(raw_verdict.strip().upper(), raw_verdict) or "—"
        return (
            f"**Dataset:** `{meta['dataset_id'] or '—'}`  "
            f"**Kind:** `{meta['run_kind'] or '—'}`  "
            f"**Run ID:** `{meta['run_id'] or '—'}`  "
            f"**Generated:** {meta['generated_at'] or '—'}  "
            f"**Verdict:** {verdict}"
        )
    except (FileNotFoundError, ValueError) as exc:
        return f"_Error reading artifact: {exc}_"

def _build_theme():  # type: ignore[no-untyped-def]
    """Return a DriftSentinel-branded gr.themes.Base theme."""
    import gradio as gr

    cyan_hue = gr.themes.Color(
        c50="#E6F1F6", c100="#C0DDE8", c200="#8ABCCE", c300="#4F9AB8", c400="#2080A3",
        c500=_SENTINEL_CYAN, c600="#1AB8C7", c700="#14A0AD", c800="#0F8A96",
        c900="#0B7480", c950=_MIDNIGHT,
    )
    slate_hue = gr.themes.Color(
        c50="#F4F8FA", c100="#E6F1F6", c200="#C8D9E4", c300=_GATE_SLATE, c400="#6B8A9F",
        c500="#4A6C80", c600="#2E4F62", c700="#1A3A4A", c800=_DEEP_SLATE,
        c900=_MIDNIGHT, c950="#030E13",
    )
    # Build theme with both light and dark variants set to the same dark values.
    pairs = {
        "body_background_fill": _MIDNIGHT, "body_text_color": _CLOUD,
        "block_background_fill": _DEEP_SLATE, "block_border_color": "#1A3A4A",
        "block_label_text_color": _GATE_SLATE,
        "input_background_fill": "#0F2D3D", "input_border_color": "#1A3A4A",
        "button_primary_background_fill": _SENTINEL_CYAN,
        "button_primary_text_color": _MIDNIGHT,
        "button_primary_background_fill_hover": "#1AB8C7",
        "table_even_background_fill": _DEEP_SLATE,
        "table_odd_background_fill": "#0F2D3D", "table_border_color": "#1A3A4A",
        "border_color_primary": _SENTINEL_CYAN, "link_text_color": _SENTINEL_CYAN,
        "code_background_fill": "#030E13",
    }
    theme_args: dict[str, str] = {}
    for k, v in pairs.items():
        theme_args[k] = v
        theme_args[f"{k}_dark"] = v
    return gr.themes.Base(
        primary_hue=cyan_hue, neutral_hue=slate_hue,
        font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui", "sans-serif"],
        font_mono=[gr.themes.GoogleFont("JetBrains Mono"), "ui-monospace", "monospace"],
    ).set(**theme_args)

_DS_CSS = """
    .ds-summary { color: #8AA3B6; font-size: 0.88em; margin-top: 4px; }
    .ds-tab-desc { color: #8AA3B6; font-size: 0.9em; margin-bottom: 12px; }
    .ds-empty-state { text-align: center; padding: 24px 16px; font-size: 0.95em; color: #8AA3B6; }
"""

def build_app():  # type: ignore[no-untyped-def]
    """Construct the Gradio Blocks app with three tabs."""
    import gradio as gr

    blocks_kwargs: dict[str, Any] = {
        "title": "DriftSentinel",
        "theme": _build_theme(),
        "css": _DS_CSS,
    }

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        ctx = gr.Blocks(**blocks_kwargs)  # type: ignore[arg-type]

    with ctx as app:
        # ---- Header ----
        logo_uri = _logo_data_uri()
        if logo_uri:
            gr.HTML(
                f'<div style="display:flex;align-items:center;gap:16px;padding:12px 0 8px 0;">'
                f'<img src="{logo_uri}" alt="DriftSentinel" '
                f'style="height:64px;width:auto;" />'
                f'<span style="color:{_GATE_SLATE};font-size:0.85em;">'
                f'Read-only operator dashboard — intake, drift, benchmark</span>'
                f'</div>'
            )
        else:
            gr.Markdown(
                "## DriftSentinel\n"
                f"<span style='color:{_GATE_SLATE};font-size:0.85em;'>"
                "Read-only operator dashboard — intake, drift, benchmark</span>",
            )

        # ---- Registry View ----
        with gr.Tab("Registry"):
            gr.Markdown(
                "Browse all datasets registered in the contract registry. "
                "Each row shows the dataset ID, contract version, and Unity Catalog location.",
                elem_classes=["ds-tab-desc"],
            )
            with gr.Row():
                reg_path = gr.Textbox(label="Registry Path", value=REGISTRY_PATH, scale=4)
                reg_btn = gr.Button("Load Registry", variant="primary", scale=1)
            reg_status = gr.Markdown(
                "_Click Load Registry to fetch the current dataset registry._",
                elem_classes=["ds-summary", "ds-empty-state"],
            )
            reg_table = gr.Dataframe(
                headers=["Dataset ID", "Version", "Catalog", "Schema", "Table"],
                interactive=False, wrap=False,
            )

            def _load_registry_with_status(rp: str) -> tuple[list[list[str]], str]:
                rows = load_registry_table(rp)
                return rows, _registry_status_text(rows)

            reg_btn.click(fn=_load_registry_with_status, inputs=[reg_path],
                          outputs=[reg_table, reg_status])

        # ---- Run Status ----
        with gr.Tab("Run Status"):
            gr.Markdown(
                "Filter and inspect recent control run evidence. "
                "Each row is one artifact from an intake, drift, benchmark, or pipeline run.",
                elem_classes=["ds-tab-desc"],
            )
            with gr.Row():
                ev_dir = gr.Textbox(label="Evidence Directory", value=EVIDENCE_DIR, scale=4)
                query_btn = gr.Button("Query", variant="primary", scale=1)
            with gr.Accordion("Filters", open=True):
                with gr.Row():
                    ds_filter = gr.Textbox(label="Dataset ID", value="",
                                           placeholder="e.g. customer_profiles")
                    kind_filter = gr.Dropdown(
                        label="Run Kind",
                        choices=["", "intake", "drift", "benchmark", "pipeline"], value="",
                    )
                    rid_filter = gr.Textbox(label="Run ID prefix", value="",
                                            placeholder="first 8+ characters")
                with gr.Row():
                    from_filter = gr.Textbox(label="Date From", value="", placeholder="YYYY-MM-DD")
                    to_filter = gr.Textbox(label="Date To", value="", placeholder="YYYY-MM-DD")
            run_summary = gr.Markdown("_Click Query to load evidence artifacts._",
                                      elem_classes=["ds-summary", "ds-empty-state"])
            status_table = gr.Dataframe(
                headers=["File", "Dataset", "Kind", "Timestamp", "Verdict", "Run ID"],
                column_count=6,
                interactive=False, wrap=True,
            )

            def _query_with_summary(
                ed: str, ds: str, rk: str, ri: str, df: str, dt: str,
            ) -> tuple[list[list[str]], str]:
                rows = query_evidence(ed, ds, rk, ri, df, dt)
                is_empty = len(rows) == 1 and "no artifacts" in rows[0][0]
                if is_empty:
                    summary = (
                        "No artifacts found matching the current filters. "
                        "Confirm the evidence directory path is correct and that "
                        "at least one control run has completed."
                    )
                else:
                    summary = _build_summary_line(rows)
                return rows, summary

            query_btn.click(
                fn=_query_with_summary,
                inputs=[ev_dir, ds_filter, kind_filter, rid_filter, from_filter, to_filter],
                outputs=[status_table, run_summary],
            )

        # ---- Evidence Explorer ----
        with gr.Tab("Evidence Explorer"):
            gr.Markdown(
                "Inspect the full JSON payload of a single evidence artifact. "
                "Enter the filename from the Run Status table, then click Load Artifact.",
                elem_classes=["ds-tab-desc"],
            )
            with gr.Row():
                exp_dir = gr.Textbox(label="Evidence Directory", value=EVIDENCE_DIR, scale=3)
                exp_file = gr.Textbox(
                    label="Artifact Filename", value="",
                    placeholder="e.g. 2026-04-02T14-40-20Z_intake_ds_a.json", scale=3,
                )
                exp_btn = gr.Button("Load Artifact", variant="primary", scale=1)
            exp_meta = gr.Markdown(
                "_Enter an artifact filename above and click Load Artifact._",
                elem_classes=["ds-summary", "ds-empty-state"],
            )
            exp_json = gr.Code(label="Artifact JSON", language="json", interactive=False)

            def _load_with_meta(ed: str, fn: str) -> tuple[str, str]:
                return load_artifact_detail(ed, fn), load_artifact_meta(ed, fn)

            exp_btn.click(fn=_load_with_meta, inputs=[exp_dir, exp_file],
                          outputs=[exp_json, exp_meta])

        # ---- Analytics ----
        with gr.Tab("Analytics"):
            import pandas as pd

            try:
                from app.analytics import (
                    build_analytics_data,
                    build_plotly_pie,
                    kind_pie_data,
                    timeline_data,
                    verdict_bar_data,
                )
            except (ImportError, ModuleNotFoundError):
                from analytics import (  # type: ignore[no-redef]
                    build_analytics_data,
                    build_plotly_pie,
                    kind_pie_data,
                    timeline_data,
                    verdict_bar_data,
                )

            gr.Markdown(
                "Visual breakdown of control run evidence. Click Refresh to "
                "scan the evidence directory and update all charts.",
                elem_classes=["ds-tab-desc"],
            )
            with gr.Row():
                ana_dir = gr.Textbox(label="Evidence Directory", value=EVIDENCE_DIR, scale=4)
                ana_btn = gr.Button("Refresh", variant="primary", scale=1)
            ana_status = gr.Markdown(
                "_Click Refresh to load analytics._",
                elem_classes=["ds-summary", "ds-empty-state"],
            )

            with gr.Row():
                verdict_plot = gr.BarPlot(
                    x="Verdict", y="Count", title="Verdict Distribution",
                    color="Verdict",
                    color_map={"PASS": _TRUST_TEAL, "FAIL": _ALERT_CORAL, "WARN": _DRIFT_AMBER},
                    height=320,
                )
                kind_plot = gr.Plot(label="Runs by Kind")
            timeline_plot = gr.LinePlot(
                x="Date", y="Runs", title="Run Timeline",
                height=280,
            )

            def _refresh_analytics(edir: str):  # type: ignore[no-untyped-def]
                records = build_analytics_data(edir.strip() or EVIDENCE_DIR)
                if not records:
                    empty = pd.DataFrame({"Verdict": [], "Count": []})
                    empty_t = pd.DataFrame({"Date": [], "Runs": []})
                    return empty, None, empty_t, "No evidence artifacts found."
                vrows = verdict_bar_data(records)
                v_df = pd.DataFrame(vrows, columns=["Verdict", "Count"])
                krows = kind_pie_data(records)
                pie_fig = build_plotly_pie(krows)
                trows = timeline_data(records)
                t_df = pd.DataFrame(trows, columns=["Date", "Runs"])
                total = len(records)
                return v_df, pie_fig, t_df, f"**{total} artifacts** analyzed"

            ana_btn.click(
                fn=_refresh_analytics, inputs=[ana_dir],
                outputs=[verdict_plot, kind_plot, timeline_plot, ana_status],
            )

    return app

def _get_app():  # type: ignore[no-untyped-def]
    """Lazy app builder for module-level access."""
    return build_app()

# Databricks Apps runtime calls `gradio app.py` which expects a module-level `app`.
# Guarded so tests can import helpers without requiring gradio.
try:
    import gradio as _gr  # noqa: F401

    app = _get_app()
    demo = app
except ImportError:
    app = None  # type: ignore[assignment]
    demo = None  # type: ignore[assignment]

if __name__ == "__main__":
    _app = _get_app()
    _app.launch()
