"""Tests for the DriftSentinel CLI entry point and databricks subpackage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest import mock

import pytest

from driftsentinel.cli import build_parser, main
from driftsentinel.databricks.bundle import BundleError
from driftsentinel.databricks.client import WorkspaceIdentity
from driftsentinel.databricks.files import VOLUME_SUBDIRS
from driftsentinel.databricks.jobs import RunResult

# ---------------------------------------------------------------------------
# CLI parser tests
# ---------------------------------------------------------------------------


class TestCLIParser:
    """Verify argparse structure and argument parsing."""

    def test_version_flag(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit) as exc_info:
            main(["--version"])
        assert exc_info.value.code == 0
        out = capsys.readouterr().out
        assert "driftsentinel" in out

    def test_no_args_shows_help(self) -> None:
        assert main([]) == 2

    def test_databricks_no_command_shows_help(self) -> None:
        assert main(["databricks"]) == 2

    def test_connect_requires_catalog_and_dataset(self) -> None:
        with pytest.raises(SystemExit):
            main(["databricks", "connect"])

    def test_connect_parses_all_args(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "databricks",
                "connect",
                "--catalog",
                "adb_dev",
                "--schema",
                "governed",
                "--volume-name",
                "my_vol",
                "--dataset-id",
                "test_ds",
                "--registry",
                "./registry.json",
                "--drift-policy",
                "./drift.yml",
                "--benchmark-policy",
                "./bench.yml",
                "--landing-path",
                "./data/current",
                "--baseline-path",
                "./data/baseline",
                "--profile",
                "dev",
                "--target",
                "prod",
                "--wait",
                "--timeout",
                "600",
            ]
        )
        assert args.catalog == "adb_dev"
        assert args.schema == "governed"
        assert args.volume_name == "my_vol"
        assert args.dataset_id == "test_ds"
        assert args.registry == "./registry.json"
        assert args.drift_policy == "./drift.yml"
        assert args.benchmark_policy == "./bench.yml"
        assert args.landing_path == "./data/current"
        assert args.baseline_path == "./data/baseline"
        assert args.profile == "dev"
        assert args.target == "prod"
        assert args.wait is True
        assert args.timeout == 600

    def test_run_parses_required_args(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "databricks",
                "run",
                "--catalog",
                "adb_dev",
                "--dataset-id",
                "test_ds",
                "--wait",
            ]
        )
        assert args.catalog == "adb_dev"
        assert args.dataset_id == "test_ds"
        assert args.wait is True

    def test_status_parses_required_args(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "databricks",
                "status",
                "--catalog",
                "adb_dev",
            ]
        )
        assert args.catalog == "adb_dev"
        assert args.schema == "default"

    def test_sync_parses_file_args(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "databricks",
                "sync",
                "--catalog",
                "adb_dev",
                "--dataset-id",
                "test_ds",
                "--registry",
                "./r.json",
            ]
        )
        assert args.catalog == "adb_dev"
        assert args.dataset_id == "test_ds"
        assert args.registry == "./r.json"

    def test_doctor_parses_required_args(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "databricks",
                "doctor",
                "--catalog",
                "adb_dev",
            ]
        )
        assert args.catalog == "adb_dev"

    def test_all_subcommands_have_func(self) -> None:
        parser = build_parser()
        for cmd in ("connect", "run", "status", "sync", "doctor"):
            # Each subcommand requires --catalog at minimum (plus --dataset-id
            # for connect/run/sync).
            base = ["databricks", cmd, "--catalog", "x"]
            if cmd in ("connect", "run", "sync"):
                base.extend(["--dataset-id", "ds"])
            args = parser.parse_args(base)
            assert hasattr(args, "func"), f"{cmd} missing func default"

    def test_registry_no_command_shows_help(self) -> None:
        assert main(["registry"]) == 2

    def test_registry_add_requires_contract(self) -> None:
        with pytest.raises(SystemExit):
            main(["registry", "add"])

    def test_registry_remove_requires_dataset_and_version(self) -> None:
        with pytest.raises(SystemExit):
            main(["registry", "remove"])

    def test_registry_add_parses_all_args(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "registry",
                "add",
                "--contract",
                "./contract.yml",
                "--registry",
                "./reg.json",
                "--catalog",
                "adb_dev",
                "--schema",
                "governed",
                "--volume-name",
                "rt",
                "--force",
            ]
        )
        assert args.contract == "./contract.yml"
        assert args.registry == "./reg.json"
        assert args.catalog == "adb_dev"
        assert args.schema == "governed"
        assert args.volume_name == "rt"
        assert args.force is True

    def test_registry_list_uses_default_registry(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["registry", "list"])
        assert args.registry == "data/registry.json"

    def test_registry_remove_parses_required_args(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "registry",
                "remove",
                "--dataset-id",
                "ds",
                "--contract-version",
                "1.0.0",
            ]
        )
        assert args.dataset_id == "ds"
        assert args.contract_version == "1.0.0"


# ---------------------------------------------------------------------------
# WorkspaceIdentity tests
# ---------------------------------------------------------------------------


class TestWorkspaceIdentity:
    def test_identity_is_frozen(self) -> None:
        identity = WorkspaceIdentity(host="https://example.com", user="user@example.com")
        assert identity.host == "https://example.com"
        assert identity.user == "user@example.com"
        with pytest.raises(AttributeError):
            identity.host = "other"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# RunResult tests
# ---------------------------------------------------------------------------


class TestRunResult:
    def test_succeeded_property(self) -> None:
        r = RunResult(
            run_id=1,
            state="TERMINATED",
            result_state="SUCCESS",
            run_page_url="https://example.com/run/1",
        )
        assert r.succeeded is True

    def test_failed_property(self) -> None:
        r = RunResult(
            run_id=2,
            state="TERMINATED",
            result_state="FAILED",
            run_page_url="https://example.com/run/2",
            message="Task failed",
        )
        assert r.succeeded is False
        assert r.message == "Task failed"


# ---------------------------------------------------------------------------
# Bundle module tests
# ---------------------------------------------------------------------------


class TestBundleModule:
    @pytest.fixture(autouse=True)
    def _set_tf_exec_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DATABRICKS_TF_EXEC_PATH", "/tmp/fake-terraform")

    def test_bundle_error_is_runtime_error(self) -> None:
        assert issubclass(BundleError, RuntimeError)

    @mock.patch("driftsentinel.databricks.bundle.subprocess.run")
    def test_validate_raises_on_nonzero(self, mock_run: mock.MagicMock) -> None:
        mock_run.return_value = mock.MagicMock(returncode=1, stdout="", stderr="validation error")
        with pytest.raises(BundleError, match="validation error"):
            from driftsentinel.databricks.bundle import validate

            validate(catalog="test_cat")

    @mock.patch("driftsentinel.databricks.bundle.subprocess.run")
    def test_validate_returns_stdout_on_success(self, mock_run: mock.MagicMock) -> None:
        mock_run.return_value = mock.MagicMock(returncode=0, stdout="Validation OK!", stderr="")
        from driftsentinel.databricks.bundle import validate

        result = validate(catalog="test_cat")
        assert "Validation OK!" in result

    @mock.patch("driftsentinel.databricks.bundle.subprocess.run")
    def test_summary_returns_parsed_json(self, mock_run: mock.MagicMock) -> None:
        mock_run.return_value = mock.MagicMock(
            returncode=0,
            stdout=json.dumps({"resources": {"jobs": {"dataset_pipeline_job": {"id": "123"}}}}),
            stderr="",
        )
        from driftsentinel.databricks.bundle import summary

        result = summary(catalog="test_cat")
        assert result["resources"]["jobs"]["dataset_pipeline_job"]["id"] == "123"

    @mock.patch("driftsentinel.databricks.bundle.subprocess.run")
    def test_deploy_forwards_schema_and_volume_name(self, mock_run: mock.MagicMock) -> None:
        mock_run.return_value = mock.MagicMock(returncode=0, stdout="ok", stderr="")
        from driftsentinel.databricks.bundle import deploy

        deploy(catalog="cat", schema="governed", volume_name="custom_vol")
        cmd = mock_run.call_args[0][0]
        assert "--var=schema=governed" in cmd
        assert "--var=runtime_volume_name=custom_vol" in cmd

    @mock.patch("driftsentinel.databricks.bundle.subprocess.run")
    def test_deploy_omits_default_schema_and_volume(self, mock_run: mock.MagicMock) -> None:
        mock_run.return_value = mock.MagicMock(returncode=0, stdout="ok", stderr="")
        from driftsentinel.databricks.bundle import deploy

        deploy(catalog="cat", schema="default", volume_name="driftsentinel_runtime")
        cmd = mock_run.call_args[0][0]
        assert "--var=schema=default" not in cmd
        assert "--var=runtime_volume_name=driftsentinel_runtime" not in cmd


# ---------------------------------------------------------------------------
# Files module tests
# ---------------------------------------------------------------------------


class TestFilesModule:
    def test_volume_subdirs_are_defined(self) -> None:
        assert "state" in VOLUME_SUBDIRS
        assert "policies" in VOLUME_SUBDIRS
        assert "evidence" in VOLUME_SUBDIRS

    def test_ensure_volume_layout_builds_expected_paths(self) -> None:
        mock_client = mock.MagicMock()
        mock_client.files.get_status.side_effect = Exception("not found")
        mock_client.files.upload.return_value = None

        from driftsentinel.databricks.files import ensure_volume_layout

        paths = ensure_volume_layout(
            mock_client,
            catalog="adb_dev",
            schema="default",
            dataset_id="my_ds",
        )
        assert paths["root"] == "/Volumes/adb_dev/default/driftsentinel_runtime"
        assert paths["state"] == "/Volumes/adb_dev/default/driftsentinel_runtime/state"
        assert paths["policies"] == "/Volumes/adb_dev/default/driftsentinel_runtime/policies"
        assert paths["evidence"] == "/Volumes/adb_dev/default/driftsentinel_runtime/evidence"
        assert paths["registry"] == "/Volumes/adb_dev/default/driftsentinel_runtime/state/registry.json"
        assert paths["landing"] == "/Volumes/adb_dev/default/driftsentinel_runtime/landing/my_ds"
        assert paths["baseline"] == "/Volumes/adb_dev/default/driftsentinel_runtime/baseline/my_ds"

    def test_upload_file_raises_for_missing_file(self) -> None:
        mock_client = mock.MagicMock()
        from driftsentinel.databricks.files import upload_file

        with pytest.raises(FileNotFoundError):
            upload_file(mock_client, "/nonexistent/file.json", "/remote/file.json")

    def test_upload_file_calls_sdk(self, tmp_path: Path) -> None:
        local = tmp_path / "test.json"
        local.write_text('{"hello": "world"}')
        mock_client = mock.MagicMock()

        from driftsentinel.databricks.files import upload_file

        result = upload_file(mock_client, local, "/remote/test.json")
        assert result == "/remote/test.json"
        mock_client.files.upload.assert_called_once()

    def test_upload_directory_uploads_files(self, tmp_path: Path) -> None:
        (tmp_path / "a.csv").write_text("col1\n1")
        (tmp_path / "b.csv").write_text("col1\n2")
        (tmp_path / ".hidden").write_text("skip")
        mock_client = mock.MagicMock()

        from driftsentinel.databricks.files import upload_directory

        result = upload_directory(mock_client, tmp_path, "/remote/data")
        assert len(result) == 2
        assert "/remote/data/a.csv" in result
        assert "/remote/data/b.csv" in result


# ---------------------------------------------------------------------------
# Jobs module tests
# ---------------------------------------------------------------------------


class TestJobsModule:
    def test_resolve_job_id_from_summary(self) -> None:
        from driftsentinel.databricks.jobs import _resolve_job_id

        bsummary: dict[str, Any] = {"resources": {"jobs": {"dataset_pipeline_job": {"id": "42"}}}}
        assert _resolve_job_id(None, bundle_summary=bsummary) == 42

    def test_resolve_job_id_explicit_override(self) -> None:
        from driftsentinel.databricks.jobs import _resolve_job_id

        assert _resolve_job_id(None, job_id=99) == 99

    def test_resolve_job_id_raises_without_info(self) -> None:
        from driftsentinel.databricks.jobs import _resolve_job_id

        with pytest.raises(ValueError, match="Cannot resolve"):
            _resolve_job_id(None)


# ---------------------------------------------------------------------------
# Connect module — build_job_parameters helper
# ---------------------------------------------------------------------------


class TestConnectHelpers:
    def test_build_job_parameters_with_policies(self) -> None:
        from driftsentinel.databricks.connect import _build_job_parameters

        params = _build_job_parameters(
            catalog="adb_dev",
            schema="default",
            volume_name="driftsentinel_runtime",
            dataset_id="my_ds",
            remote_paths={
                "registry": "/Volumes/adb_dev/default/driftsentinel_runtime/state/registry.json",
                "evidence": "/Volumes/adb_dev/default/driftsentinel_runtime/evidence",
                "drift_policy": "/Volumes/adb_dev/default/driftsentinel_runtime/policies/drift.yml",
                "benchmark_policy": "/Volumes/adb_dev/default/driftsentinel_runtime/policies/bench.yml",
            },
        )
        assert params["dataset_id"] == "my_ds"
        assert params["drift_policy_path"] == "/Volumes/adb_dev/default/driftsentinel_runtime/policies/drift.yml"
        assert params["benchmark_policy_path"] == "/Volumes/adb_dev/default/driftsentinel_runtime/policies/bench.yml"
        assert "registry_path" in params
        assert "evidence_dir" in params

    def test_build_job_parameters_without_policies(self) -> None:
        from driftsentinel.databricks.connect import _build_job_parameters

        params = _build_job_parameters(
            catalog="adb_dev",
            schema="default",
            volume_name="driftsentinel_runtime",
            dataset_id="my_ds",
            remote_paths={},
        )
        assert params["dataset_id"] == "my_ds"
        assert "drift_policy_path" not in params
        assert "benchmark_policy_path" not in params


# ---------------------------------------------------------------------------
# Registry CLI behavior tests
# ---------------------------------------------------------------------------


def _write_contract(
    path: Path,
    *,
    name: str = "demo_dataset",
    version: str = "1.0.0",
) -> Path:
    path.write_text(
        f"""
dataset:
  name: {name}
  description: Demo
  catalog: adb_dev
  schema: default
  table: t
  contract_version: "{version}"
source:
  system: demo
  format: csv
  landing_path: /tmp/landing
  baseline_path: /tmp/baseline
contract:
  required_columns:
    - column_name: id
      type: long
      nullable: false
  business_key: [id]
  batch_identifier: batch_id
""".lstrip(),
        encoding="utf-8",
    )
    return path


class TestRegistryAddCommand:
    def test_creates_new_registry_when_missing(self, tmp_path: Path) -> None:
        contract = _write_contract(tmp_path / "contract.yml")
        registry = tmp_path / "registry.json"

        rc = main(
            [
                "registry",
                "add",
                "--contract",
                str(contract),
                "--registry",
                str(registry),
            ]
        )

        assert rc == 0
        assert registry.is_file()
        data = json.loads(registry.read_text())
        assert data["registry"][0]["dataset_id"] == "demo_dataset"
        assert data["registry"][0]["contract_version"] == "1.0.0"

    def test_appends_to_existing_registry(self, tmp_path: Path) -> None:
        contract_a = _write_contract(tmp_path / "a.yml", name="alpha")
        contract_b = _write_contract(tmp_path / "b.yml", name="beta")
        registry = tmp_path / "registry.json"

        assert main(["registry", "add", "--contract", str(contract_a), "--registry", str(registry)]) == 0
        assert main(["registry", "add", "--contract", str(contract_b), "--registry", str(registry)]) == 0

        data = json.loads(registry.read_text())
        ids = sorted(e["dataset_id"] for e in data["registry"])
        assert ids == ["alpha", "beta"]

    def test_collision_without_force_returns_error(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        contract = _write_contract(tmp_path / "contract.yml")
        registry = tmp_path / "registry.json"

        assert main(["registry", "add", "--contract", str(contract), "--registry", str(registry)]) == 0
        rc = main(["registry", "add", "--contract", str(contract), "--registry", str(registry)])

        assert rc == 1
        err = capsys.readouterr().err
        assert "already registered" in err
        assert "--force" in err

    def test_collision_with_force_replaces_entry(self, tmp_path: Path) -> None:
        contract = _write_contract(tmp_path / "contract.yml")
        registry = tmp_path / "registry.json"

        assert main(["registry", "add", "--contract", str(contract), "--registry", str(registry)]) == 0
        # Same identity, different description (forces replacement).
        contract.write_text(contract.read_text().replace("Demo", "Updated"), encoding="utf-8")

        rc = main(
            [
                "registry",
                "add",
                "--contract",
                str(contract),
                "--registry",
                str(registry),
                "--force",
            ]
        )

        assert rc == 0
        data = json.loads(registry.read_text())
        assert data["registry"][0]["contract"]["dataset"]["description"] == "Updated"

    def test_substitutes_placeholders_when_supplied(self, tmp_path: Path) -> None:
        path = tmp_path / "contract.yml"
        path.write_text(
            """
dataset:
  name: ds
  description: x
  catalog: ${CATALOG}
  schema: ${SCHEMA}
  table: t
  contract_version: "1.0.0"
source:
  system: s
  format: csv
  landing_path: /Volumes/${CATALOG}/${SCHEMA}/landing/
  baseline_path: /Volumes/${CATALOG}/${SCHEMA}/baseline/
contract:
  required_columns:
    - column_name: id
      type: long
      nullable: false
  business_key: [id]
  batch_identifier: batch_id
""".lstrip(),
            encoding="utf-8",
        )
        registry = tmp_path / "registry.json"

        rc = main(
            [
                "registry",
                "add",
                "--contract",
                str(path),
                "--registry",
                str(registry),
                "--catalog",
                "adb_dev",
                "--schema",
                "governed",
            ]
        )

        assert rc == 0
        contract = json.loads(registry.read_text())["registry"][0]["contract"]
        assert contract["dataset"]["catalog"] == "adb_dev"
        assert contract["dataset"]["schema"] == "governed"
        assert "${CATALOG}" not in contract["source"]["landing_path"]


class TestRegistryListCommand:
    def test_missing_registry_returns_error(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        rc = main(["registry", "list", "--registry", str(tmp_path / "missing.json")])
        assert rc == 1
        assert "not found" in capsys.readouterr().err

    def test_lists_registered_datasets(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        contract_a = _write_contract(tmp_path / "a.yml", name="alpha")
        contract_b = _write_contract(tmp_path / "b.yml", name="beta", version="2.0.0")
        registry = tmp_path / "registry.json"
        main(["registry", "add", "--contract", str(contract_a), "--registry", str(registry)])
        main(["registry", "add", "--contract", str(contract_b), "--registry", str(registry)])
        capsys.readouterr()

        rc = main(["registry", "list", "--registry", str(registry)])

        assert rc == 0
        out = capsys.readouterr().out
        assert "DATASET_ID" in out
        assert "alpha" in out and "1.0.0" in out
        assert "beta" in out and "2.0.0" in out


class TestRegistryRemoveCommand:
    def test_removes_existing_entry(self, tmp_path: Path) -> None:
        contract = _write_contract(tmp_path / "contract.yml")
        registry = tmp_path / "registry.json"
        main(["registry", "add", "--contract", str(contract), "--registry", str(registry)])

        rc = main(
            [
                "registry",
                "remove",
                "--dataset-id",
                "demo_dataset",
                "--contract-version",
                "1.0.0",
                "--registry",
                str(registry),
            ]
        )

        assert rc == 0
        data = json.loads(registry.read_text())
        assert data["registry"] == []

    def test_unknown_entry_returns_error(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        contract = _write_contract(tmp_path / "contract.yml")
        registry = tmp_path / "registry.json"
        main(["registry", "add", "--contract", str(contract), "--registry", str(registry)])

        rc = main(
            [
                "registry",
                "remove",
                "--dataset-id",
                "demo_dataset",
                "--contract-version",
                "9.9.9",
                "--registry",
                str(registry),
            ]
        )

        assert rc == 1
        assert "not registered" in capsys.readouterr().err

    def test_missing_registry_returns_error(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        rc = main(
            [
                "registry",
                "remove",
                "--dataset-id",
                "x",
                "--contract-version",
                "1.0.0",
                "--registry",
                str(tmp_path / "missing.json"),
            ]
        )
        assert rc == 1
        assert "not found" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# pyproject.toml entry point
# ---------------------------------------------------------------------------


class TestEntryPoint:
    def test_scripts_entry_in_pyproject(self) -> None:
        import tomllib

        root = Path(__file__).resolve().parent.parent
        with open(root / "pyproject.toml", "rb") as f:
            data = tomllib.load(f)
        scripts = data["project"]["scripts"]
        assert scripts["driftsentinel"] == "driftsentinel.cli:main"
