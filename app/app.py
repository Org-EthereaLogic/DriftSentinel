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

try:
    import gradio as gr
except ImportError:  # allow test imports without gradio installed
    gr = None  # type: ignore[assignment]

from driftsentinel.config.loader import DatasetRegistry, RegistryError
from driftsentinel.evidence.writer import list_evidence, load_evidence
from driftsentinel.paths import PathSecurityError, resolve_trusted_child, trusted_roots

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
_VERDICT_CIRCLES = {"PASS": "🟢 PASS", "FAIL": "🔴 FAIL", "WARN": "🟡 WARN"}
_MODE_LABELS = {
    "dataset_backed": "Dataset-Backed",
    "demo": "Demo",
    "legacy_or_unknown": "Legacy/Unknown",
    "reference_data": "Reference Sample",
    "synthetic": "Synthetic",
}

_ASSETS = Path(__file__).parent.parent / "assets" / "driftsentinel-brand-system"
_LOGO_PATH = _ASSETS / "variants" / "logo-dark.png"
_FAVICON_PATH = str(_ASSETS / "favicons" / "favicon-32x32.png")

def _get_logo_uris() -> tuple[str | None, str | None]:
    """Encode the light and dark brand logos as base64 data URIs."""
    import base64

    def _b64(path: Path) -> str | None:
        if not path.is_file():
            return None
        return f"data:image/png;base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"

    return (
        _b64(_ASSETS / "variants" / "logo-light.png"),
        _b64(_ASSETS / "variants" / "logo-dark.png"),
    )

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
    legacy_unknown = 0
    other = 0
    for row in rows:
        raw = (row[5].strip() if len(row) > 5 else "")
        # Strip colored-circle prefix if present (e.g. "🟢 PASS" -> "PASS")
        v = raw.split()[-1].upper() if raw else ""
        if v in counts:
            counts[v] += 1
        else:
            other += 1
        if len(row) > 2 and row[2].strip() == _MODE_LABELS["legacy_or_unknown"]:
            legacy_unknown += 1
    parts = [f"**{total} artifact{'s' if total != 1 else ''}**"]
    if counts["PASS"]:
        parts.append(f"🟢 PASS: {counts['PASS']}")
    if counts["WARN"]:
        parts.append(f"🟡 WARN: {counts['WARN']}")
    if counts["FAIL"]:
        parts.append(f"🔴 FAIL: {counts['FAIL']}")
    if legacy_unknown:
        parts.append(f"legacy/unknown mode: {legacy_unknown}")
    if other:
        parts.append(f"other: {other}")
    return "  |  ".join(parts)


def _trim_result_rows(rows: list[list[str]], max_results: int | None) -> list[list[str]]:
    """Return the latest ``max_results`` rows without truncating empty/error states."""
    if max_results is None or max_results <= 0:
        return rows
    if not rows:
        return rows
    first = rows[0][0]
    if first.startswith("(error:") or "no artifacts" in first:
        return rows
    return rows[:max_results]


def _parse_max_results(value: str) -> int | None:
    """Convert a UI dropdown value into an optional integer result cap."""
    raw = value.strip()
    if not raw or raw.lower() == "all":
        return None
    try:
        parsed = int(raw)
    except ValueError:
        return None
    return parsed if parsed > 0 else None


def _visible_artifact_choices(rows: list[list[str]]) -> tuple[list[str], str | None]:
    """Extract visible artifact filenames for the Run Status handoff control."""
    if not rows:
        return [], None
    first = rows[0][0]
    if first.startswith("(error:") or "no artifacts" in first:
        return [], None
    files = [row[0] for row in rows if row and row[0]]
    return files, None

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
    execution_mode = (
        meta.get("execution_mode", "")
        or payload.get("execution_mode", "")
        or (payload.get("benchmark", {}) or {}).get("execution_mode", "")
        or "legacy_or_unknown"
    )
    return {
        "dataset_id": meta.get("dataset_id", "") or data.get("dataset_id", "") or "",
        "execution_mode": str(execution_mode),
        "run_kind": meta.get("run_kind", "") or data.get("run_kind", "") or "",
        "run_id": run_id[:8] if len(run_id) > 8 else run_id,
        "generated_at": _fmt_timestamp(meta.get("generated_at", "") or data.get("generated_at", "") or ""),
        "verdict": verdict,
    }

def load_registry_table(registry_path: str) -> list[list[str]]:
    """Load the registry and return rows for the Gradio table."""
    path = registry_path.strip() or REGISTRY_PATH
    try:
        normalized = os.path.abspath(os.path.normpath(os.path.expanduser(path)))
        roots = trusted_roots()
        if not any(normalized == root or normalized.startswith(f"{root}{os.sep}") for root in roots):
            raise PathSecurityError(f"Registry file escapes trusted roots: {path}")
        registry_file = Path(normalized)
        if not registry_file.is_file():
            return [["(no registry file found)", "", "", "", ""]]
        reg = DatasetRegistry.load(registry_file)
    except (PathSecurityError, RegistryError) as exc:
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

def _query_evidence_rows(
    evidence_dir: str,
    dataset_id: str,
    execution_mode: str,
    run_kind: str,
    run_id: str,
    date_from: str,
    date_to: str,
) -> list[list[str]]:
    """Query evidence and return rows for the summary table."""
    edir = evidence_dir.strip() or EVIDENCE_DIR
    try:
        results = list_evidence(
            edir,
            dataset_id=dataset_id.strip() or None,
            execution_mode=execution_mode.strip() or None,
            run_kind=run_kind.strip() or None,
            run_id=run_id.strip() or None,
            date_from=date_from.strip() or None,
            date_to=date_to.strip() or None,
        )
    except PathSecurityError as exc:
        return [[f"(error: {exc})", "", "", "", "", "", ""]]
    if not results:
        return [["(no artifacts found)", "", "", "", "", "", ""]]
    rows: list[list[str]] = []
    for r in results:
        if r.get("parse_error"):
            rows.append([Path(r["file"]).name, "", "Legacy/Unknown", "parse_error", "", "(malformed)", ""])
            continue
        raw_verdict = str(r.get("overall_verdict", "") or "").strip().upper()
        verdict = _VERDICT_CIRCLES.get(raw_verdict, raw_verdict)
        rows.append([
            Path(r["file"]).name,
            r.get("dataset_id", "") or "",
            _MODE_LABELS.get(str(r.get("execution_mode") or ""), str(r.get("execution_mode") or "")),
            r.get("run_kind", "") or "",
            _fmt_timestamp(r.get("generated_at", "") or ""),
            verdict,
            _fmt_run_id(r.get("run_id", "") or ""),
        ])
    return rows


def query_evidence(
    evidence_dir: str,
    dataset_id: str,
    execution_mode: str,
    run_kind: str,
    run_id: str,
    date_from: str,
    date_to: str,
    *,
    max_results: int | None = None,
) -> list[list[str]]:
    """Query evidence and optionally return only the latest ``max_results`` rows."""
    rows = _query_evidence_rows(
        evidence_dir,
        dataset_id,
        execution_mode,
        run_kind,
        run_id,
        date_from,
        date_to,
    )
    return _trim_result_rows(rows, max_results)

def _resolve_artifact_path(evidence_dir: str, filename: str) -> Path | None:
    """Resolve an artifact filename to a concrete path, or None if not found."""
    fname = filename.strip()
    if not fname:
        return None
    return resolve_trusted_child(
        evidence_dir.strip() or EVIDENCE_DIR,
        fname,
        context="Evidence artifact",
        allowed_suffixes=(".json",),
    )


def load_artifact_detail(evidence_dir: str, filename: str | None) -> str:
    """Load and return the full JSON of an evidence artifact."""
    raw_name = filename.strip() if isinstance(filename, str) else ""
    if not raw_name:
        return "(select an artifact filename)"
    try:
        path = _resolve_artifact_path(evidence_dir, raw_name)
    except ValueError as exc:
        return f"(error: {exc})"
    if path is None:
        return f"(file not found: {raw_name})"
    try:
        data = load_evidence(path)
        return json.dumps(data, indent=2, default=str)
    except FileNotFoundError:
        return f"(file not found: {raw_name})"
    except ValueError as exc:
        return f"(error: {exc})"

def load_artifact_meta(evidence_dir: str, filename: str | None) -> str:
    """Return a Markdown one-line metadata summary for an evidence artifact."""
    raw_name = filename.strip() if isinstance(filename, str) else ""
    if not raw_name:
        return "_Enter an artifact filename above and click Load Artifact._"
    try:
        path = _resolve_artifact_path(evidence_dir, raw_name)
    except ValueError as exc:
        return f"_Error reading artifact: {exc}_"
    if path is None:
        return f"_File not found: `{raw_name}`_"
    try:
        meta = _extract_artifact_meta(load_evidence(path))
        raw_verdict = meta["verdict"] or ""
        verdict = _VERDICT_CIRCLES.get(raw_verdict.strip().upper(), raw_verdict) or "—"
        mode = _MODE_LABELS.get(meta["execution_mode"], meta["execution_mode"]) or "—"
        return (
            f"**Dataset:** `{meta['dataset_id'] or '—'}`  "
            f"**Mode:** `{mode}`  "
            f"**Kind:** `{meta['run_kind'] or '—'}`  "
            f"**Run ID:** `{meta['run_id'] or '—'}`  "
            f"**Generated:** {meta['generated_at'] or '—'}  "
            f"**Verdict:** {verdict}"
        )
    except FileNotFoundError:
        return f"_File not found: `{raw_name}`_"
    except ValueError as exc:
        return f"_Error reading artifact: {exc}_"

def _build_theme():  # type: ignore[no-untyped-def]
    """Return a DriftSentinel-branded gr.themes.Base theme."""

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
    # Apply explicit overrides only to the dark mode variant.
    # The light mode will inherit Gradio's Base defaults tinted by the hues above.
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
        theme_args[f"{k}_dark"] = v
    return gr.themes.Base(
        primary_hue=cyan_hue, neutral_hue=slate_hue,
        font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui", "sans-serif"],
        font_mono=[gr.themes.GoogleFont("JetBrains Mono"), "ui-monospace", "monospace"],
    ).set(**theme_args)

_DS_CSS = """
    .ds-summary { color: var(--body-text-color-subdued); font-size: 0.88em; margin-top: 4px; }
    .ds-tab-desc { color: var(--body-text-color-subdued); font-size: 0.9em; margin-bottom: 12px; }
    .ds-empty-state { text-align: center; padding: 24px 16px;
        font-size: 0.95em; color: var(--body-text-color-subdued); }
    .ds-readonly-dataframe [aria-label*="Drop CSV or TSV files here to import data into dataframe"] {
        pointer-events: none !important;
    }
    .ds-readonly-dataframe [aria-label*="Drop CSV or TSV files here to import data into dataframe"] * {
        pointer-events: auto !important;
    }
    #ds-logo-dark { display: none !important; }
    .dark #ds-logo-dark, :root.dark #ds-logo-dark, body.dark #ds-logo-dark { display: block !important; }
    .dark #ds-logo-light, :root.dark #ds-logo-light, body.dark #ds-logo-light { display: none !important; }
"""

def build_app():  # type: ignore[no-untyped-def]
    """Construct the Gradio Blocks app with four tabs."""
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
        logo_light_uri, logo_dark_uri = _get_logo_uris()
        if logo_light_uri and logo_dark_uri:
            gr.HTML(
                f'<div style="display:flex;align-items:center;gap:16px;padding:12px 0 8px 0;">'
                f'<img id="ds-logo-light" src="{logo_light_uri}" alt="DriftSentinel" style="height:64px;width:auto;" />'
                f'<img id="ds-logo-dark" src="{logo_dark_uri}" alt="DriftSentinel" style="height:64px;width:auto;" />'
                f'<span style="color:var(--body-text-color-subdued);font-size:0.85em;">'
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
        with gr.Tabs(elem_id="tabs") as tabs:
            with gr.Tab("Registry", id="registry"):
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
                    interactive=False,
                    wrap=False,
                    elem_classes=["ds-readonly-dataframe"],
                )

                def _load_registry_with_status(rp: str) -> tuple[list[list[str]], str]:
                    rows = load_registry_table(rp)
                    return rows, _registry_status_text(rows)

                reg_btn.click(fn=_load_registry_with_status, inputs=[reg_path],
                              outputs=[reg_table, reg_status])

            # ---- Run Status ----
            with gr.Tab("Run Status", id="run_status"):
                gr.Markdown(
                    "Filter and inspect recent control run evidence. "
                    "Each row is one artifact from an intake, drift, benchmark, or pipeline run, "
                    "with explicit execution mode labeling.",
                    elem_classes=["ds-tab-desc"],
                )
                with gr.Row():
                    ev_dir = gr.Textbox(label="Evidence Directory", value=EVIDENCE_DIR, scale=4)
                    max_results = gr.Dropdown(
                        label="Max Results",
                        choices=["100", "250", "500", "1000", "All"],
                        value="250",
                        scale=1,
                    )
                    query_btn = gr.Button("Query", variant="primary", scale=1)
                with gr.Accordion("Filters", open=False):
                    with gr.Row():
                        ds_filter = gr.Textbox(label="Dataset ID", value="",
                                               placeholder="e.g. customer_profiles")
                        mode_filter = gr.Dropdown(
                            label="Execution Mode",
                            choices=["", "dataset_backed", "reference_data", "synthetic", "demo", "legacy_or_unknown"],
                            value="",
                        )
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
                    headers=["File", "Dataset", "Mode", "Kind", "Timestamp", "Verdict", "Run ID"],
                    column_count=7,
                    interactive=False,
                    wrap=True,
                    elem_classes=["ds-readonly-dataframe"],
                )
                visible_artifacts = gr.Dropdown(
                    label="Visible Artifact Filename",
                    choices=[],
                    value=None,
                    allow_custom_value=False,
                    info="Use this picker to open a result in Evidence Explorer without retyping the filename.",
                )

                def _query_with_summary(
                    ed: str, mr: str, ds: str, mode: str, rk: str, ri: str, df: str, dt: str,
                ) -> tuple[list[list[str]], str, gr.Dropdown]:
                    all_rows = _query_evidence_rows(ed, ds, mode, rk, ri, df, dt)
                    rows = _trim_result_rows(all_rows, _parse_max_results(mr))
                    artifact_files, default_artifact = _visible_artifact_choices(rows)
                    artifact_update = gr.Dropdown(choices=artifact_files, value=default_artifact)
                    is_empty = len(all_rows) == 1 and "no artifacts" in all_rows[0][0]
                    is_error = len(all_rows) == 1 and all_rows[0][0].startswith("(error:")
                    if is_error:
                        summary = (
                            "Evidence query blocked. Confirm the path stays inside the trusted "
                            "roots or configure `DRIFTSENTINEL_ALLOWED_PATH_ROOTS`."
                        )
                    elif is_empty:
                        summary = (
                            "No artifacts found matching the current filters. "
                            "Confirm the evidence directory path is correct and that "
                            "at least one control run has completed."
                        )
                    else:
                        summary = _build_summary_line(all_rows)
                        if len(rows) < len(all_rows):
                            summary = (
                                f"{summary}  |  displaying latest {len(rows)} rows "
                                f"(adjust `Max Results` to load more)"
                            )
                    return rows, summary, artifact_update

                query_btn.click(
                    fn=_query_with_summary,
                    inputs=[
                        ev_dir,
                        max_results,
                        ds_filter,
                        mode_filter,
                        kind_filter,
                        rid_filter,
                        from_filter,
                        to_filter,
                    ],
                    outputs=[status_table, run_summary, visible_artifacts],
                )

            # ---- Evidence Explorer ----
            with gr.Tab("Evidence Explorer", id="evidence_explorer"):
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

                def _open_visible_artifact(current_dir: str, filename: str | None):
                    if not filename or not filename.strip():
                        return gr.skip(), gr.skip(), gr.skip(), gr.skip(), gr.skip()
                    detail, meta = _load_with_meta(current_dir, filename)
                    return current_dir, filename, detail, meta, gr.Tabs(selected="evidence_explorer")

                visible_artifacts.change(
                    fn=_open_visible_artifact,
                    inputs=[ev_dir, visible_artifacts],
                    outputs=[exp_dir, exp_file, exp_json, exp_meta, tabs],
                )

                def _sync_evidence_dir(current_dir: str) -> str:
                    return current_dir

                ev_dir.change(fn=_sync_evidence_dir, inputs=[ev_dir], outputs=[exp_dir])

                def _on_status_select(current_dir: str, evt: gr.SelectData):
                    filename = ""
                    if isinstance(evt.row_value, list) and evt.row_value:
                        filename = str(evt.row_value[0])
                    detail, meta = _load_with_meta(current_dir, filename)
                    return current_dir, filename, detail, meta, gr.Tabs(selected="evidence_explorer")

                status_table.select(
                    fn=_on_status_select,
                    inputs=[ev_dir],
                    outputs=[exp_dir, exp_file, exp_json, exp_meta, tabs]
                )

            # ---- Analytics ----
            with gr.Tab("Analytics", id="analytics"):
                try:
                    from app.analytics import (
                        _daily_verdict_summary,
                        build_analytics_data,
                        build_plotly_bar,
                        build_plotly_daily_volume,
                        build_plotly_health_trend,
                        build_plotly_pie,
                        kind_pie_data,
                        timeline_data,
                        verdict_bar_data,
                    )
                except (ImportError, ModuleNotFoundError):
                    from analytics import (  # type: ignore[no-redef]
                        _daily_verdict_summary,
                        build_analytics_data,
                        build_plotly_bar,
                        build_plotly_daily_volume,
                        build_plotly_health_trend,
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
                    ana_dir = gr.Textbox(label="Evidence Directory", value=EVIDENCE_DIR, scale=3)
                    color_theme = gr.Dropdown(
                        choices=["Brand", "Traffic Light", "Colorblind Safe", "Cyberpunk", "Pastel"],
                        value="Brand",
                        label="Color Theme",
                        scale=1
                    )
                    ana_btn = gr.Button("Refresh", variant="primary", scale=1)
                ana_status = gr.Markdown(
                    "_Click Refresh to load analytics._",
                    elem_classes=["ds-summary", "ds-empty-state"],
                )

                with gr.Row():
                    verdict_plot = gr.Plot(label="Verdict Distribution")
                    kind_plot = gr.Plot(label="Runs by Kind")
                with gr.Row():
                    volume_plot = gr.Plot(label="Daily Activity Volume")
                    health_plot = gr.Plot(label="Daily Health Trend")

                def _refresh_analytics(edir: str, theme: str):  # type: ignore[no-untyped-def]
                    try:
                        records = build_analytics_data(edir.strip() or EVIDENCE_DIR)
                    except PathSecurityError as exc:
                        return None, None, None, None, f"Analytics refresh blocked: {exc}"
                    if not records:
                        return None, None, None, None, "No evidence artifacts found."
                    vrows = verdict_bar_data(records)
                    verdict_fig = build_plotly_bar(vrows, theme)
                    krows = kind_pie_data(records)
                    pie_fig = build_plotly_pie(krows, theme)
                    trows = timeline_data(records)
                    # Compute daily summary once and pass to both chart builders
                    summary = _daily_verdict_summary(trows)
                    volume_fig = build_plotly_daily_volume(trows, theme, daily_summary=summary)
                    health_fig = build_plotly_health_trend(trows, theme, daily_summary=summary)
                    total = len(records)
                    legacy = sum(1 for record in records if record.get("execution_mode") == "legacy_or_unknown")
                    status = f"**{total} artifacts** analyzed"
                    if legacy:
                        status += (
                            f"  |  **{legacy} legacy/unknown artifacts** lack explicit execution mode "
                            "and should not be treated as proof of real-data execution"
                        )
                    return verdict_fig, pie_fig, volume_fig, health_fig, status

            ana_btn.click(
                fn=_refresh_analytics, inputs=[ana_dir, color_theme],
                outputs=[verdict_plot, kind_plot, volume_plot, health_plot, ana_status],
            )

        app.load(
            fn=_load_registry_with_status, inputs=[reg_path],
            outputs=[reg_table, reg_status],
        )

    return app

def _get_app():  # type: ignore[no-untyped-def]
    """Lazy app builder for module-level access."""
    return build_app()

# Databricks Apps runtime calls `gradio app.py` which expects a module-level `app`.
# Guarded so tests can import helpers without requiring gradio.
if gr is not None:
    app = _get_app()
    demo = app
else:
    app = None  # type: ignore[assignment]
    demo = None  # type: ignore[assignment]

if __name__ == "__main__":
    _app = _get_app()
    _app.launch()
