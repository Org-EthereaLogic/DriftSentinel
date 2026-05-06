"""Tests for the Phase 4 Databricks App UI.

Verifies app structure, read-only behavior, import hygiene,
and that the Gradio interface builds without errors.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

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
    def test_configured_surface_paths_prefers_runtime_volume(self, monkeypatch) -> None:
        from app.app import _configured_surface_paths

        monkeypatch.delenv("REGISTRY_PATH", raising=False)
        monkeypatch.delenv("EVIDENCE_DIR", raising=False)
        monkeypatch.setenv("RUNTIME_VOLUME_PATH", "/Volumes/main/default/driftsentinel_runtime")

        registry_path, evidence_dir = _configured_surface_paths()

        assert registry_path == "/Volumes/main/default/driftsentinel_runtime/state/registry.json"
        assert evidence_dir == "/Volumes/main/default/driftsentinel_runtime/evidence"

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
            dep
            for dep in app.config.get("dependencies", [])
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
        reg.register(
            {
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
            }
        )
        reg_path = tmp_path / "reg.json"
        reg.save(reg_path)
        rows = load_registry_table(str(reg_path))
        assert len(rows) == 1
        assert rows[0][0] == "test_ds"
        assert rows[0][1] == "1.0.0"
        assert rows[0][2] == "cat"

    def test_load_registry_table_rejects_untrusted_path(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.app import load_registry_table

        monkeypatch.setattr(
            "app.app.trusted_roots",
            lambda extra_roots=(): (str(tmp_path / "_no_match_"),),
        )
        reg_path = tmp_path / "registry.json"
        reg_path.write_text('{"registry": []}', encoding="utf-8")
        rows = load_registry_table(str(reg_path))

        assert rows[0][0].startswith("(error:")
        assert "trusted roots" in rows[0][0]

    def test_query_evidence_empty_dir(self, tmp_path: Path) -> None:
        from app.app import query_evidence

        rows = query_evidence(str(tmp_path), "", "", "", "", "", "")
        assert len(rows) == 1
        assert "no artifacts" in rows[0][0]

    def test_query_evidence_rejects_untrusted_dir(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.app import query_evidence

        monkeypatch.setattr(
            "driftsentinel.paths.trusted_roots",
            lambda extra_roots=(): (str(tmp_path / "_no_match_"),),
        )
        rows = query_evidence(str(tmp_path), "", "", "", "", "", "")

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
            execution_mode="dataset_backed",
        )
        rows = query_evidence(str(tmp_path), "", "", "", "", "", "")
        assert len(rows) == 1
        assert rows[0][1] == "ds_a"
        assert rows[0][2] == "Dataset-Backed"
        assert rows[0][3] == "benchmark"
        assert rows[0][5] == "🟢 PASS"

    def test_query_evidence_derives_intake_pass_verdict(self, tmp_path: Path) -> None:
        from app.app import query_evidence
        from driftsentinel.evidence.writer import write_evidence

        write_evidence(
            tmp_path,
            "intake.json",
            {"ready": 10, "quarantined": 0, "schema_valid": True},
            run_ts="2026-04-02T00:00:00+00:00",
            dataset_id="ds_a",
            run_kind="intake",
            run_id="r1",
            execution_mode="dataset_backed",
        )
        rows = query_evidence(str(tmp_path), "", "", "", "", "", "")
        assert len(rows) == 1
        assert rows[0][3] == "intake"
        assert rows[0][5] == "🟢 PASS"

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
            execution_mode="dataset_backed",
        )
        write_evidence(
            tmp_path,
            "newer.json",
            {"overall_verdict": "FAIL"},
            run_ts="2026-04-03T00:00:00+00:00",
            dataset_id="ds_a",
            run_kind="benchmark",
            run_id="newer",
            execution_mode="dataset_backed",
        )

        rows = query_evidence(str(tmp_path), "", "", "", "", "", "", max_results=1)
        assert len(rows) == 1
        assert rows[0][0] == "newer.json"
        assert rows[0][5] == "🔴 FAIL"

    def test_query_evidence_with_malformed_file(self, tmp_path: Path) -> None:
        from app.app import query_evidence

        (tmp_path / "bad.json").write_text("not json", encoding="utf-8")
        rows = query_evidence(str(tmp_path), "", "", "", "", "", "")
        assert rows == [["bad.json", "", "Legacy/Unknown", "parse_error", "", "(malformed)", ""]]

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

    def test_load_artifact_meta_shows_execution_mode(self, tmp_path: Path) -> None:
        from app.app import load_artifact_meta
        from driftsentinel.evidence.writer import write_evidence

        write_evidence(
            tmp_path,
            "mode.json",
            {"overall_verdict": "PASS"},
            run_ts="2026-04-02T00:00:00+00:00",
            dataset_id="ds_a",
            run_kind="benchmark",
            run_id="run-1",
            execution_mode="reference_data",
        )
        result = load_artifact_meta(str(tmp_path), "mode.json")
        assert "Mode:" in result
        assert "Reference Sample" in result


class TestAnalyticsHelpers:
    def test_timeline_data_preserves_event_level_context(self) -> None:
        from app.analytics import timeline_data

        rows = timeline_data(
            [
                {
                    "dataset_id": "ds_a",
                    "execution_mode": "dataset_backed",
                    "generated_at": "2026-04-02T22:00:00+00:00",
                    "run_kind": "benchmark",
                    "verdict": "PASS",
                }
            ]
        )

        assert rows == [
            [
                "2026-04-02T22:00:00+00:00",
                "benchmark",
                "ds_a",
                "PASS",
            ]
        ]

    def test_build_plotly_verdict_by_kind(self) -> None:
        from app.analytics import build_plotly_verdict_by_kind

        rec = {"dataset_id": "ds_a", "execution_mode": "demo", "generated_at": ""}
        records = [
            {**rec, "run_kind": "benchmark", "verdict": "PASS"},
            {**rec, "run_kind": "drift", "verdict": "FAIL"},
        ]
        fig = build_plotly_verdict_by_kind(records)

        assert fig is not None
        assert fig.layout.title.text == "Verdict by Run Kind"

    def test_build_plotly_health_trend(self) -> None:
        from app.analytics import build_plotly_health_trend

        fig = build_plotly_health_trend([["2026-04-02T22:00:00+00:00", "benchmark", "ds_a", "PASS"]])

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
        volume_resource = app_def["resources"][0]["uc_securable"]
        assert volume_resource["securable_type"] == "VOLUME"
        assert volume_resource["securable_full_name"] == ("${var.catalog}.${var.schema}.${var.runtime_volume_name}")
        assert volume_resource["permission"] == "READ_VOLUME"
        job_resource = app_def["resources"][1]["job"]
        assert job_resource["id"] == "${resources.jobs.dataset_pipeline_job.id}"
        assert job_resource["permission"] == "CAN_MANAGE_RUN"
        assert app_def["config"]["command"] == ["gradio", "app/app.py"]
        env = {item["name"]: item for item in app_def["config"]["env"]}
        assert env["RUNTIME_VOLUME_PATH"]["value_from"] == "runtime_volume"
        assert env["DATASET_PIPELINE_JOB_ID"]["value_from"] == "dataset_pipeline_job"
        assert env["DRIFTSENTINEL_ALLOWED_PATH_ROOTS"]["value"] == ""


# --- Deploy script (DS-PATCH-038) ---


def _fixture_bundle_summary(
    *,
    catalog: str = "main",
    schema: str = "default",
    volume_name: str = "driftsentinel_runtime",
    job_id: str = "987654321",
    securable_full_name: str | None = None,
    embedded_job_id: str | None = None,
    command: list[str] | None = ["gradio", "app/app.py"],
    extra_env: list[dict] | None = None,
) -> dict:
    full_name = securable_full_name if securable_full_name is not None else f"{catalog}.{schema}.{volume_name}"
    embedded = embedded_job_id if embedded_job_id is not None else "${resources.jobs.dataset_pipeline_job.id}"
    env_entries: list[dict] = [
        {"name": "RUNTIME_VOLUME_PATH", "value_from": "runtime_volume"},
        {"name": "DATASET_PIPELINE_JOB_ID", "value_from": "dataset_pipeline_job"},
        {"name": "DRIFTSENTINEL_ALLOWED_PATH_ROOTS", "value": ""},
    ]
    if extra_env:
        env_entries.extend(extra_env)
    summary: dict = {
        "variables": {
            "catalog": {"value": catalog},
            "schema": {"value": schema},
            "runtime_volume_name": {"value": volume_name},
        },
        "resources": {
            "apps": {
                "driftsentinel_app": {
                    "name": "driftsentinel",
                    "source_code_path": ("/Workspace/Users/op@example.com/.bundle/driftsentinel/dev/files"),
                    "config": {
                        "env": env_entries,
                        "resources": [
                            {
                                "name": "runtime_volume",
                                "uc_securable": {
                                    "securable_type": "VOLUME",
                                    "securable_full_name": full_name,
                                    "permission": "READ_VOLUME",
                                },
                            },
                            {
                                "name": "dataset_pipeline_job",
                                "job": {
                                    "id": embedded,
                                    "permission": "CAN_MANAGE_RUN",
                                },
                            },
                        ],
                    },
                }
            },
            "jobs": {
                "dataset_pipeline_job": {"id": job_id},
            },
        },
    }
    if command is not None:
        summary["resources"]["apps"]["driftsentinel_app"]["config"]["command"] = list(command)
    return summary


class TestDeployScriptCommandShape:
    def test_apps_deploy_command_uses_source_code_path_and_no_bundle_flags(self) -> None:
        from scripts.deploy_databricks_app import _build_apps_deploy_cmd

        cmd = _build_apps_deploy_cmd(
            "driftsentinel",
            "/Workspace/Users/op/.bundle/driftsentinel/dev/files",
            ["-p", "demo"],
        )

        assert cmd[:6] == [
            "databricks",
            "apps",
            "deploy",
            "driftsentinel",
            "--source-code-path",
            "/Workspace/Users/op/.bundle/driftsentinel/dev/files",
        ]
        assert "--target" not in cmd
        assert not any(part.startswith("--var") for part in cmd)
        assert cmd[-2:] == ["-p", "demo"]

    def test_apps_deploy_command_omits_profile_when_unset(self) -> None:
        from scripts.deploy_databricks_app import _build_apps_deploy_cmd

        cmd = _build_apps_deploy_cmd("driftsentinel", "/Workspace/path/files", [])

        assert cmd == [
            "databricks",
            "apps",
            "deploy",
            "driftsentinel",
            "--source-code-path",
            "/Workspace/path/files",
        ]


class TestDeployScriptAppYamlGeneration:
    def test_returns_none_when_no_command(self) -> None:
        from scripts.deploy_databricks_app import _build_app_yaml_content

        summary = _fixture_bundle_summary(command=None)

        assert _build_app_yaml_content(summary, "driftsentinel_app") is None

    def test_resolves_volume_value_from_reference(self) -> None:
        import yaml as _yaml

        from scripts.deploy_databricks_app import _build_app_yaml_content

        summary = _fixture_bundle_summary(catalog="main", schema="default", volume_name="driftsentinel_runtime")

        content = _build_app_yaml_content(summary, "driftsentinel_app")
        assert content is not None
        data = _yaml.safe_load(content)
        env = {item["name"]: item for item in data["env"]}
        assert env["RUNTIME_VOLUME_PATH"] == {
            "name": "RUNTIME_VOLUME_PATH",
            "value": "/Volumes/main/default/driftsentinel_runtime",
        }
        assert "value_from" not in env["RUNTIME_VOLUME_PATH"]

    def test_resolves_volume_from_variables_when_full_name_unresolved(self) -> None:
        import yaml as _yaml

        from scripts.deploy_databricks_app import _build_app_yaml_content

        summary = _fixture_bundle_summary(
            catalog="ent",
            schema="prod",
            volume_name="ds_runtime",
            securable_full_name="${var.catalog}.${var.schema}.${var.runtime_volume_name}",
        )

        content = _build_app_yaml_content(summary, "driftsentinel_app")
        assert content is not None
        data = _yaml.safe_load(content)
        env = {item["name"]: item for item in data["env"]}
        assert env["RUNTIME_VOLUME_PATH"]["value"] == "/Volumes/ent/prod/ds_runtime"

    def test_resolves_job_value_from_reference(self) -> None:
        import yaml as _yaml

        from scripts.deploy_databricks_app import _build_app_yaml_content

        summary = _fixture_bundle_summary(job_id="42")

        content = _build_app_yaml_content(summary, "driftsentinel_app")
        assert content is not None
        data = _yaml.safe_load(content)
        env = {item["name"]: item for item in data["env"]}
        assert env["DATASET_PIPELINE_JOB_ID"]["value"] == "42"

    def test_resolves_job_id_when_embedded_id_already_concrete(self) -> None:
        import yaml as _yaml

        from scripts.deploy_databricks_app import _build_app_yaml_content

        summary = _fixture_bundle_summary(embedded_job_id="11111", job_id="22222")

        content = _build_app_yaml_content(summary, "driftsentinel_app")
        assert content is not None
        data = _yaml.safe_load(content)
        env = {item["name"]: item for item in data["env"]}
        # When the resource's own id is concrete, prefer it over the top-level
        # jobs block lookup.
        assert env["DATASET_PIPELINE_JOB_ID"]["value"] == "11111"

    def test_passes_through_literal_value_entries(self) -> None:
        import yaml as _yaml

        from scripts.deploy_databricks_app import _build_app_yaml_content

        summary = _fixture_bundle_summary()

        content = _build_app_yaml_content(summary, "driftsentinel_app")
        assert content is not None
        data = _yaml.safe_load(content)
        env = {item["name"]: item for item in data["env"]}
        assert env["DRIFTSENTINEL_ALLOWED_PATH_ROOTS"] == {
            "name": "DRIFTSENTINEL_ALLOWED_PATH_ROOTS",
            "value": "",
        }

    def test_unknown_value_from_resolves_to_empty_string(self) -> None:
        import yaml as _yaml

        from scripts.deploy_databricks_app import _build_app_yaml_content

        summary = _fixture_bundle_summary(extra_env=[{"name": "MYSTERY", "value_from": "ghost_resource"}])

        content = _build_app_yaml_content(summary, "driftsentinel_app")
        assert content is not None
        data = _yaml.safe_load(content)
        env = {item["name"]: item for item in data["env"]}
        # Fail-soft: env var is preserved with empty string per DS-PATCH-038 §4.2.1.
        assert env["MYSTERY"] == {"name": "MYSTERY", "value": ""}

    def test_command_is_preserved_in_order(self) -> None:
        import yaml as _yaml

        from scripts.deploy_databricks_app import _build_app_yaml_content

        summary = _fixture_bundle_summary(command=["gradio", "app/app.py"])

        content = _build_app_yaml_content(summary, "driftsentinel_app")
        assert content is not None
        data = _yaml.safe_load(content)
        assert data["command"] == ["gradio", "app/app.py"]


class TestDeployScriptResourceResolution:
    def test_volume_path_falls_back_when_full_name_blank(self) -> None:
        from scripts.deploy_databricks_app import _resolve_app_resource_values

        summary = _fixture_bundle_summary(securable_full_name="")

        resolved = _resolve_app_resource_values(summary, "driftsentinel_app")

        assert resolved["runtime_volume"] == "/Volumes/main/default/driftsentinel_runtime"

    def test_returns_empty_mapping_when_app_missing(self) -> None:
        from scripts.deploy_databricks_app import _resolve_app_resource_values

        assert _resolve_app_resource_values({}, "driftsentinel_app") == {}
