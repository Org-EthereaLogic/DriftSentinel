"""DriftSentinel Databricks App — read-only operator dashboard.

Provides three views over existing DriftSentinel package surfaces:
1. Registry View — browse registered datasets and policy compatibility
2. Run Status — filter and summarize recent control runs
3. Evidence Explorer — inspect full evidence artifact detail

This app never writes evidence, modifies the registry, or executes controls.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from driftsentinel.config.loader import DatasetRegistry, RegistryError
from driftsentinel.evidence.writer import list_evidence, load_evidence

REGISTRY_PATH = os.environ.get("REGISTRY_PATH", "/tmp/driftsentinel_registry.json")
EVIDENCE_DIR = os.environ.get("EVIDENCE_DIR", "/tmp/driftsentinel_evidence")


# ---------------------------------------------------------------------------
# Registry View helpers
# ---------------------------------------------------------------------------


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
        rows.append([
            did,
            ver,
            ds.get("catalog", ""),
            ds.get("schema", ""),
            ds.get("table", ""),
        ])
    return rows


# ---------------------------------------------------------------------------
# Evidence helpers
# ---------------------------------------------------------------------------


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
        rows.append([
            Path(r["file"]).name,
            r.get("dataset_id", "") or "",
            r.get("run_kind", "") or "",
            r.get("generated_at", "") or "",
            verdict,
            r.get("run_id", "") or "",
        ])
    return rows


def load_artifact_detail(evidence_dir: str, filename: str) -> str:
    """Load and return the full JSON of an evidence artifact."""
    edir = evidence_dir.strip() or EVIDENCE_DIR
    if not filename.strip():
        return "(select an artifact filename)"
    path = Path(edir) / filename.strip()
    if not path.is_file():
        # filename might be a full path from the table
        path = Path(filename.strip())
    if not path.is_file():
        return f"(file not found: {filename})"
    try:
        data = load_evidence(path)
        return json.dumps(data, indent=2, default=str)
    except (FileNotFoundError, ValueError) as exc:
        return f"(error: {exc})"


# ---------------------------------------------------------------------------
# Gradio App
# ---------------------------------------------------------------------------


def build_app():  # type: ignore[no-untyped-def]
    """Construct the Gradio Blocks app with three tabs."""
    import gradio as gr

    with gr.Blocks(title="DriftSentinel") as app:
        gr.Markdown("# DriftSentinel Operator Dashboard")
        gr.Markdown(
            "Read-only view of registered datasets, recent control runs, "
            "and evidence artifacts."
        )

        # --- Registry View ---
        with gr.Tab("Registry"):
            reg_path = gr.Textbox(
                label="Registry Path",
                value=REGISTRY_PATH,
                interactive=True,
            )
            reg_btn = gr.Button("Load Registry")
            reg_table = gr.Dataframe(
                headers=["Dataset ID", "Version", "Catalog", "Schema", "Table"],
                interactive=False,
            )
            reg_btn.click(
                fn=load_registry_table,
                inputs=[reg_path],
                outputs=[reg_table],
            )

        # --- Run Status ---
        with gr.Tab("Run Status"):
            with gr.Row():
                ev_dir = gr.Textbox(label="Evidence Dir", value=EVIDENCE_DIR)
                ds_filter = gr.Textbox(label="Dataset ID", value="")
                kind_filter = gr.Dropdown(
                    label="Run Kind",
                    choices=["", "intake", "drift", "benchmark", "pipeline"],
                    value="",
                )
            with gr.Row():
                rid_filter = gr.Textbox(label="Run ID", value="")
                from_filter = gr.Textbox(label="Date From (ISO)", value="")
                to_filter = gr.Textbox(label="Date To (ISO)", value="")
            query_btn = gr.Button("Query")
            status_table = gr.Dataframe(
                headers=["File", "Dataset", "Kind", "Timestamp", "Verdict", "Run ID"],
                interactive=False,
            )
            query_btn.click(
                fn=query_evidence,
                inputs=[ev_dir, ds_filter, kind_filter, rid_filter, from_filter, to_filter],
                outputs=[status_table],
            )

        # --- Evidence Explorer ---
        with gr.Tab("Evidence Explorer"):
            with gr.Row():
                exp_dir = gr.Textbox(label="Evidence Dir", value=EVIDENCE_DIR)
                exp_file = gr.Textbox(label="Artifact Filename", value="")
            exp_btn = gr.Button("Load Artifact")
            exp_json = gr.Code(label="Artifact JSON", language="json", interactive=False)
            exp_btn.click(
                fn=load_artifact_detail,
                inputs=[exp_dir, exp_file],
                outputs=[exp_json],
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
