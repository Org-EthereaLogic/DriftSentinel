"""Tests for the Phase 4 Databricks App UI.

Verifies app structure, read-only behavior, import hygiene,
and that the Gradio interface builds without errors.
"""

from __future__ import annotations

import ast
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP_DIR = ROOT / "app"
APP_PY = APP_DIR / "app.py"
APP_YAML = APP_DIR / "app.yaml"
APP_REQS = APP_DIR / "requirements.txt"


# --- File structure ---


class TestAppFileStructure:
    def test_app_directory_exists(self) -> None:
        assert APP_DIR.is_dir()

    def test_app_py_exists(self) -> None:
        assert APP_PY.is_file()

    def test_app_yaml_exists(self) -> None:
        assert APP_YAML.is_file()

    def test_requirements_txt_exists(self) -> None:
        assert APP_REQS.is_file()

    def test_app_yaml_uses_gradio_command(self) -> None:
        import yaml

        with open(APP_YAML) as f:
            data = yaml.safe_load(f)
        assert data["command"][0] == "gradio"
        assert data["command"][1] == "app.py"

    def test_app_yaml_env_uses_supported_value_fields(self) -> None:
        import yaml

        with open(APP_YAML) as f:
            data = yaml.safe_load(f)
        for entry in data["env"]:
            assert "value" in entry
            assert "valueFrom" not in entry

    def test_requirements_install_parent_project_and_gradio(self) -> None:
        text = APP_REQS.read_text()
        assert "-e .." in text
        assert "gradio>=6.10.0,<7" in text


# --- Read-only assertions ---


class TestAppReadOnly:
    def test_app_does_not_call_write_evidence(self) -> None:
        text = APP_PY.read_text()
        assert "write_evidence(" not in text
        assert "write_benchmark_bundle(" not in text

    def test_app_does_not_call_registry_register(self) -> None:
        text = APP_PY.read_text()
        assert ".register(" not in text

    def test_app_does_not_call_registry_remove(self) -> None:
        text = APP_PY.read_text()
        assert ".remove(" not in text

    def test_app_does_not_call_registry_save(self) -> None:
        text = APP_PY.read_text()
        assert ".save(" not in text

    def test_app_does_not_import_run_functions(self) -> None:
        text = APP_PY.read_text()
        assert "run_intake_demo" not in text
        assert "run_drift_demo" not in text
        assert "run_local_pipeline" not in text
        assert "run_dataset_pipeline" not in text
        assert "run_benchmark" not in text


# --- Import hygiene ---


class TestAppImportHygiene:
    def test_no_sibling_repo_imports(self) -> None:
        tree = ast.parse(APP_PY.read_text())
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                module = getattr(node, "module", "") or ""
                for alias in getattr(node, "names", []):
                    name = alias.name
                    for banned in [
                        "trusted_source_intake",
                        "silent_failure_prevention",
                        "measurable_control_effectiveness",
                    ]:
                        assert banned not in module, f"Sibling import: {module}"
                        assert banned not in name, f"Sibling import: {name}"

    def test_only_imports_read_functions_from_driftsentinel(self) -> None:
        tree = ast.parse(APP_PY.read_text())
        ds_imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and "driftsentinel" in node.module:
                for alias in node.names:
                    ds_imports.append(alias.name)
        allowed = {
            "DatasetRegistry",
            "RegistryError",
            "PathSecurityError",
            "list_evidence",
            "load_evidence",
            "resolve_trusted_child",
            "resolve_trusted_file",
            "trusted_roots",
        }
        for imp in ds_imports:
            assert imp in allowed, f"Unexpected driftsentinel import: {imp}"


# --- Functional helpers ---


class TestAppHelpers:
    def test_visible_artifact_choices_ignore_empty_state(self) -> None:
        from app.app import _visible_artifact_choices

        choices, default = _visible_artifact_choices([["(no artifacts found)", "", "", "", "", ""]])
        assert choices == []
        assert default is None

    def test_visible_artifact_choices_return_first_filename(self) -> None:
        from app.app import _visible_artifact_choices

        rows = [
            ["newest.json", "ds_a", "benchmark", "Apr 03, 00:00 UTC", "🟢 PASS", "newest"],
            ["older.json", "ds_a", "benchmark", "Apr 02, 00:00 UTC", "🔴 FAIL", "older"],
        ]
        choices, default = _visible_artifact_choices(rows)
        assert choices == ["newest.json", "older.json"]
        assert default is None

    def test_only_registry_tab_preloads_on_app_load(self) -> None:
        from app.app import build_app

        app = build_app()
        load_dependencies = [
            dep for dep in app.config.get("dependencies", [])
            if any(event == "load" for _, event in dep.get("targets", []))
        ]

        assert len(load_dependencies) == 1

    def test_load_registry_table_missing_file(self, tmp_path: Path) -> None:
        from app.app import load_registry_table

        rows = load_registry_table(str(tmp_path / "missing.json"))
        assert len(rows) == 1
        assert "no registry" in rows[0][0]

    def test_load_registry_table_with_data(self, tmp_path: Path) -> None:
        from app.app import load_registry_table
        from driftsentinel.config.loader import DatasetRegistry

        reg = DatasetRegistry()
        reg.register({
            "dataset": {
                "name": "test_ds",
                "contract_version": "1.0.0",
                "catalog": "cat",
                "schema": "sch",
                "table": "tbl",
            },
            "contract": {
                "required_columns": [{"column_name": "id", "type": "long", "nullable": False}],
                "business_key": ["id"],
                "batch_identifier": "batch_id",
            },
        })
        reg_path = tmp_path / "reg.json"
        reg.save(reg_path)
        rows = load_registry_table(str(reg_path))
        assert len(rows) == 1
        assert rows[0][0] == "test_ds"
        assert rows[0][1] == "1.0.0"
        assert rows[0][2] == "cat"

    def test_load_registry_table_rejects_untrusted_path(self) -> None:
        from app.app import load_registry_table

        with tempfile.TemporaryDirectory(dir=ROOT.parent) as temp_dir:
            reg_path = Path(temp_dir) / "registry.json"
            reg_path.write_text('{"registry": []}', encoding="utf-8")
            rows = load_registry_table(str(reg_path))

        assert rows[0][0].startswith("(error:")
        assert "trusted roots" in rows[0][0]

    def test_query_evidence_empty_dir(self, tmp_path: Path) -> None:
        from app.app import query_evidence

        rows = query_evidence(str(tmp_path), "", "", "", "", "")
        assert len(rows) == 1
        assert "no artifacts" in rows[0][0]

    def test_query_evidence_rejects_untrusted_dir(self) -> None:
        from app.app import query_evidence

        with tempfile.TemporaryDirectory(dir=ROOT.parent) as temp_dir:
            rows = query_evidence(temp_dir, "", "", "", "", "")

        assert rows[0][0].startswith("(error:")
        assert "trusted roots" in rows[0][0]

    def test_query_evidence_with_data(self, tmp_path: Path) -> None:
        from app.app import query_evidence
        from driftsentinel.evidence.writer import write_evidence

        write_evidence(
            tmp_path,
            "test.json",
            {"overall_verdict": "PASS"},
            run_ts="2026-04-02T00:00:00+00:00",
            dataset_id="ds_a",
            run_kind="benchmark",
            run_id="r1",
        )
        rows = query_evidence(str(tmp_path), "", "", "", "", "")
        assert len(rows) == 1
        assert rows[0][1] == "ds_a"
        assert rows[0][2] == "benchmark"
        assert rows[0][4] == "🟢 PASS"

    def test_query_evidence_honors_max_results(self, tmp_path: Path) -> None:
        from app.app import query_evidence
        from driftsentinel.evidence.writer import write_evidence

        write_evidence(
            tmp_path,
            "older.json",
            {"overall_verdict": "PASS"},
            run_ts="2026-04-02T00:00:00+00:00",
            dataset_id="ds_a",
            run_kind="benchmark",
            run_id="older",
        )
        write_evidence(
            tmp_path,
            "newer.json",
            {"overall_verdict": "FAIL"},
            run_ts="2026-04-03T00:00:00+00:00",
            dataset_id="ds_a",
            run_kind="benchmark",
            run_id="newer",
        )

        rows = query_evidence(str(tmp_path), "", "", "", "", "", max_results=1)
        assert len(rows) == 1
        assert rows[0][0] == "newer.json"
        assert rows[0][4] == "🔴 FAIL"

    def test_query_evidence_with_malformed_file(self, tmp_path: Path) -> None:
        from app.app import query_evidence

        (tmp_path / "bad.json").write_text("not json", encoding="utf-8")
        rows = query_evidence(str(tmp_path), "", "", "", "", "")
        assert rows == [["bad.json", "", "parse_error", "", "(malformed)", ""]]

    def test_load_artifact_detail_missing(self) -> None:
        from app.app import load_artifact_detail

        result = load_artifact_detail("/tmp", "nonexistent.json")
        assert "not found" in result

    def test_load_artifact_detail_none_filename(self) -> None:
        from app.app import load_artifact_detail

        result = load_artifact_detail("/tmp", None)
        assert "select an artifact filename" in result

    def test_load_artifact_detail_valid(self, tmp_path: Path) -> None:
        from app.app import load_artifact_detail
        from driftsentinel.evidence.writer import write_evidence

        write_evidence(
            tmp_path,
            "detail.json",
            {"score": 0.95},
            run_ts="2026-04-02T00:00:00+00:00",
        )
        result = load_artifact_detail(str(tmp_path), "detail.json")
        data = json.loads(result)
        assert data["payload"]["score"] == 0.95

    def test_load_artifact_detail_rejects_absolute_filename(self, tmp_path: Path) -> None:
        from app.app import load_artifact_detail
        from driftsentinel.evidence.writer import write_evidence

        artifact = write_evidence(
            tmp_path,
            "detail.json",
            {"score": 0.95},
            run_ts="2026-04-02T00:00:00+00:00",
        )
        result = load_artifact_detail(str(tmp_path), str(artifact))
        assert "bare filename" in result

    def test_load_artifact_meta_none_filename(self) -> None:
        from app.app import load_artifact_meta

        result = load_artifact_meta("/tmp", None)
        assert "Enter an artifact filename" in result


class TestAnalyticsHelpers:
    def test_timeline_data_preserves_event_level_context(self) -> None:
        from app.analytics import timeline_data

        rows = timeline_data([
            {
                "dataset_id": "ds_a",
                "generated_at": "2026-04-02T22:00:00+00:00",
                "run_kind": "benchmark",
                "verdict": "PASS",
            }
        ])

        assert rows == [[
            "2026-04-02T22:00:00+00:00",
            "benchmark",
            "ds_a",
            "PASS",
        ]]

    def test_build_plotly_daily_volume(self) -> None:
        from app.analytics import build_plotly_daily_volume

        fig = build_plotly_daily_volume([
            ["2026-04-02T22:00:00+00:00", "benchmark", "ds_a", "PASS"]
        ])

        assert fig is not None
        assert fig.layout.title.text == "Daily Activity Volume"


    def test_build_plotly_health_trend(self) -> None:
        from app.analytics import build_plotly_health_trend

        fig = build_plotly_health_trend([
            ["2026-04-02T22:00:00+00:00", "benchmark", "ds_a", "PASS"]
        ])

        assert fig is not None
        assert fig.layout.title.text == "Daily Health Trend (% PASS)"


# --- DAB resource ---


class TestAppBundleResource:
    def test_driftsentinel_app_resource_exists(self) -> None:
        import yaml

        path = ROOT / "resources" / "driftsentinel_app.yml"
        assert path.is_file()
        with open(path) as f:
            data = yaml.safe_load(f)
        assert "resources" in data
        assert "apps" in data["resources"]
        assert "driftsentinel_app" in data["resources"]["apps"]
        app_def = data["resources"]["apps"]["driftsentinel_app"]
        assert app_def["name"] == "driftsentinel"
        assert app_def["source_code_path"] == ".."
        assert app_def["config"]["command"] == ["gradio", "app/app.py"]
        env = {item["name"]: item["value"] for item in app_def["config"]["env"]}
        assert env["REGISTRY_PATH"] == "/tmp/driftsentinel_registry.json"
        assert env["EVIDENCE_DIR"] == "/tmp/driftsentinel_evidence"
        assert env["DRIFTSENTINEL_ALLOWED_PATH_ROOTS"] == ""
