"""Tests for driftsentinel.databricks.connect — orchestration layer for Databricks CLI commands.

Covers: connect, run, status, sync, doctor entry points and helper functions.
"""

from __future__ import annotations

from typing import Any
from unittest import mock

import pytest

from driftsentinel.databricks import connect
from driftsentinel.databricks.bundle import BundleError
from driftsentinel.databricks.client import WorkspaceIdentity
from driftsentinel.databricks.jobs import RunResult
from driftsentinel.runtime_paths import DEFAULT_RUNTIME_VOLUME_NAME

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_ws() -> mock.MagicMock:
    """Mock Databricks workspace client."""
    ws = mock.MagicMock()
    ws.catalogs = mock.MagicMock()
    ws.files = mock.MagicMock()
    return ws


@pytest.fixture
def mock_identity() -> WorkspaceIdentity:
    """Mock workspace identity."""
    return WorkspaceIdentity(user="test_user@example.com", host="https://test.databricks.com")


@pytest.fixture
def mock_run_result() -> RunResult:
    """Mock job run result (successful)."""
    return RunResult(
        run_id=123,
        state="TERMINATED",
        result_state="SUCCESS",
        run_page_url="https://test.databricks.com/jobs/123/runs/456",
        message="Run succeeded",
    )


@pytest.fixture
def bundle_summary_fixture() -> dict[str, Any]:
    """Mock bundle summary output."""
    return {
        "resources": {
            "jobs": {
                "dataset_pipeline_job": {
                    "id": "999",
                    "name": "driftsentinel-pipeline",
                },
            },
        },
    }


# ---------------------------------------------------------------------------
# _build_job_parameters tests
# ---------------------------------------------------------------------------


class TestBuildJobParameters:
    """Verify _build_job_parameters constructs correct parameter dicts."""

    def test_minimal_params(self) -> None:
        """Build params with only required args."""
        params = connect._build_job_parameters(
            catalog="adb_dev",
            schema="governed",
            volume_name=DEFAULT_RUNTIME_VOLUME_NAME,
            dataset_id="test_dataset",
            remote_paths={},
        )
        assert params["dataset_id"] == "test_dataset"
        assert "registry_path" in params
        assert "evidence_dir" in params
        assert "drift_policy_path" not in params
        assert "benchmark_policy_path" not in params

    def test_with_policy_paths(self) -> None:
        """Build params including drift and benchmark policies."""
        params = connect._build_job_parameters(
            catalog="adb_dev",
            schema="governed",
            volume_name=DEFAULT_RUNTIME_VOLUME_NAME,
            dataset_id="test_dataset",
            remote_paths={
                "drift_policy": "/Volumes/adb_dev/governed/ws_vol/drift.yml",
                "benchmark_policy": "/Volumes/adb_dev/governed/ws_vol/benchmark.yml",
            },
        )
        assert params["drift_policy_path"] == "/Volumes/adb_dev/governed/ws_vol/drift.yml"
        assert params["benchmark_policy_path"] == "/Volumes/adb_dev/governed/ws_vol/benchmark.yml"

    def test_remote_paths_override_defaults(self) -> None:
        """remote_paths dict values override computed defaults."""
        registry_override = "/Volumes/custom/path/registry.json"
        params = connect._build_job_parameters(
            catalog="adb_dev",
            schema="governed",
            volume_name=DEFAULT_RUNTIME_VOLUME_NAME,
            dataset_id="test_dataset",
            remote_paths={
                "registry": registry_override,
            },
        )
        assert params["registry_path"] == registry_override


# ---------------------------------------------------------------------------
# connect() function tests
# ---------------------------------------------------------------------------


class TestConnect:
    """Verify the connect() orchestration function."""

    @mock.patch("driftsentinel.databricks.connect.files.sync_files")
    @mock.patch("driftsentinel.databricks.connect.jobs.submit_run")
    @mock.patch("driftsentinel.databricks.connect.bundle.app_get")
    @mock.patch("driftsentinel.databricks.connect.bundle.app_start")
    @mock.patch("driftsentinel.databricks.connect.bundle.summary")
    @mock.patch("driftsentinel.databricks.connect.bundle.deploy")
    @mock.patch("driftsentinel.databricks.connect.client.resolve_identity")
    @mock.patch("driftsentinel.databricks.connect.client.get_workspace_client")
    def test_connect_returns_dict_with_required_keys(
        self,
        mock_get_ws: mock.MagicMock,
        mock_resolve_id: mock.MagicMock,
        mock_deploy: mock.MagicMock,
        mock_summary: mock.MagicMock,
        mock_app_start: mock.MagicMock,
        mock_app_get: mock.MagicMock,
        mock_submit: mock.MagicMock,
        mock_sync: mock.MagicMock,
        mock_identity: WorkspaceIdentity,
        bundle_summary_fixture: dict[str, Any],
        mock_ws: mock.MagicMock,
    ) -> None:
        """Connect returns a dict with identity, bundle_summary, job_id, and run info."""
        mock_get_ws.return_value = mock_ws
        mock_resolve_id.return_value = mock_identity
        mock_summary.return_value = bundle_summary_fixture
        mock_app_get.return_value = {"url": ""}
        mock_sync.return_value = {
            "registry": "/Volumes/adb_dev/governed/ws_vol/registry.json",
            "evidence": "/Volumes/adb_dev/governed/ws_vol/evidence",
        }
        mock_submit.return_value = 456

        result = connect.connect(
            catalog="adb_dev",
            schema="governed",
            volume_name=DEFAULT_RUNTIME_VOLUME_NAME,
            dataset_id="test_dataset",
        )

        assert isinstance(result, dict)
        assert "identity" in result
        assert "bundle_summary" in result
        assert "job_id" in result
        assert "run" in result

    @mock.patch("driftsentinel.databricks.connect.files.sync_files")
    @mock.patch("driftsentinel.databricks.connect.jobs.run_and_wait")
    @mock.patch("driftsentinel.databricks.connect.bundle.app_get")
    @mock.patch("driftsentinel.databricks.connect.bundle.app_start")
    @mock.patch("driftsentinel.databricks.connect.bundle.summary")
    @mock.patch("driftsentinel.databricks.connect.bundle.deploy")
    @mock.patch("driftsentinel.databricks.connect.client.resolve_identity")
    @mock.patch("driftsentinel.databricks.connect.client.get_workspace_client")
    def test_connect_with_wait_polls_for_completion(
        self,
        mock_get_ws: mock.MagicMock,
        mock_resolve_id: mock.MagicMock,
        mock_deploy: mock.MagicMock,
        mock_summary: mock.MagicMock,
        mock_app_start: mock.MagicMock,
        mock_app_get: mock.MagicMock,
        mock_run_wait: mock.MagicMock,
        mock_sync: mock.MagicMock,
        mock_identity: WorkspaceIdentity,
        bundle_summary_fixture: dict[str, Any],
        mock_run_result: RunResult,
        mock_ws: mock.MagicMock,
    ) -> None:
        """Connect with wait=True calls run_and_wait and returns completion info."""
        mock_get_ws.return_value = mock_ws
        mock_resolve_id.return_value = mock_identity
        mock_summary.return_value = bundle_summary_fixture
        mock_app_get.return_value = {"url": ""}
        mock_sync.return_value = {
            "registry": "/Volumes/adb_dev/governed/ws_vol/registry.json",
            "evidence": "/Volumes/adb_dev/governed/ws_vol/evidence",
        }
        mock_run_wait.return_value = mock_run_result

        result = connect.connect(
            catalog="adb_dev",
            schema="governed",
            volume_name=DEFAULT_RUNTIME_VOLUME_NAME,
            dataset_id="test_dataset",
            wait=True,
            timeout_s=600,
        )

        assert result["run"]["run_id"] == 123
        assert result["run"]["result_state"] == "SUCCESS"
        mock_run_wait.assert_called_once()

    @mock.patch("driftsentinel.databricks.connect.files.sync_files")
    @mock.patch("driftsentinel.databricks.connect.bundle.app_get")
    @mock.patch("driftsentinel.databricks.connect.bundle.summary")
    @mock.patch("driftsentinel.databricks.connect.bundle.app_start")
    @mock.patch("driftsentinel.databricks.connect.bundle.deploy")
    @mock.patch("driftsentinel.databricks.connect.client.resolve_identity")
    @mock.patch("driftsentinel.databricks.connect.client.get_workspace_client")
    def test_connect_calls_app_start_even_on_error(
        self,
        mock_get_ws: mock.MagicMock,
        mock_resolve_id: mock.MagicMock,
        mock_deploy: mock.MagicMock,
        mock_app_start: mock.MagicMock,
        mock_summary: mock.MagicMock,
        mock_app_get: mock.MagicMock,
        mock_sync: mock.MagicMock,
        mock_identity: WorkspaceIdentity,
        bundle_summary_fixture: dict[str, Any],
        mock_ws: mock.MagicMock,
    ) -> None:
        """Connect calls app_start even if it raises an error (non-fatal)."""
        mock_get_ws.return_value = mock_ws
        mock_resolve_id.return_value = mock_identity
        mock_deploy.return_value = None
        mock_app_start.side_effect = BundleError("App already exists")
        mock_summary.return_value = bundle_summary_fixture
        mock_app_get.return_value = {"url": ""}
        mock_sync.return_value = {
            "registry": "/Volumes/adb_dev/governed/ws_vol/registry.json",
            "evidence": "/Volumes/adb_dev/governed/ws_vol/evidence",
        }

        # Error from app_start should not propagate; execution continues
        result = connect.connect(
            catalog="adb_dev",
            schema="governed",
            volume_name=DEFAULT_RUNTIME_VOLUME_NAME,
            dataset_id="test_dataset",
        )

        # Verify app_start was called
        mock_app_start.assert_called_once()
        # And we still got a result despite the app error
        assert "identity" in result


# ---------------------------------------------------------------------------
# run() function tests
# ---------------------------------------------------------------------------


class TestRun:
    """Verify the run() function for rerunning pipelines."""

    @mock.patch("driftsentinel.databricks.connect.jobs.submit_run")
    @mock.patch("driftsentinel.databricks.connect.bundle.summary")
    @mock.patch("driftsentinel.databricks.connect.client.get_workspace_client")
    def test_run_returns_dict_with_run_id(
        self,
        mock_get_ws: mock.MagicMock,
        mock_summary: mock.MagicMock,
        mock_submit: mock.MagicMock,
        bundle_summary_fixture: dict[str, Any],
        mock_ws: mock.MagicMock,
    ) -> None:
        """Rerun pipeline returns dict with run_id and state."""
        mock_get_ws.return_value = mock_ws
        mock_summary.return_value = bundle_summary_fixture
        mock_submit.return_value = 789

        result = connect.run(
            catalog="adb_dev",
            schema="governed",
            volume_name=DEFAULT_RUNTIME_VOLUME_NAME,
            dataset_id="test_dataset",
        )

        assert result["run_id"] == 789
        assert result["state"] == "SUBMITTED"
        mock_submit.assert_called_once()

    @mock.patch("driftsentinel.databricks.connect.jobs.run_and_wait")
    @mock.patch("driftsentinel.databricks.connect.bundle.summary")
    @mock.patch("driftsentinel.databricks.connect.client.get_workspace_client")
    def test_run_with_wait_returns_completion_info(
        self,
        mock_get_ws: mock.MagicMock,
        mock_summary: mock.MagicMock,
        mock_run_wait: mock.MagicMock,
        bundle_summary_fixture: dict[str, Any],
        mock_run_result: RunResult,
        mock_ws: mock.MagicMock,
    ) -> None:
        """Rerun with wait=True returns completion info including succeeded status."""
        mock_get_ws.return_value = mock_ws
        mock_summary.return_value = bundle_summary_fixture
        mock_run_wait.return_value = mock_run_result

        result = connect.run(
            catalog="adb_dev",
            schema="governed",
            volume_name=DEFAULT_RUNTIME_VOLUME_NAME,
            dataset_id="test_dataset",
            wait=True,
            timeout_s=300,
        )

        assert result["run_id"] == 123
        assert result["result_state"] == "SUCCESS"
        assert mock_run_result.succeeded is True

    @mock.patch("driftsentinel.databricks.connect.jobs.run_and_wait")
    @mock.patch("driftsentinel.databricks.connect.bundle.summary")
    @mock.patch("driftsentinel.databricks.connect.client.get_workspace_client")
    def test_run_includes_policy_paths_in_params(
        self,
        mock_get_ws: mock.MagicMock,
        mock_summary: mock.MagicMock,
        mock_run_wait: mock.MagicMock,
        bundle_summary_fixture: dict[str, Any],
        mock_run_result: RunResult,
        mock_ws: mock.MagicMock,
    ) -> None:
        """Rerun includes custom policy paths in job parameters."""
        mock_get_ws.return_value = mock_ws
        mock_summary.return_value = bundle_summary_fixture
        mock_run_wait.return_value = mock_run_result

        connect.run(
            catalog="adb_dev",
            schema="governed",
            volume_name=DEFAULT_RUNTIME_VOLUME_NAME,
            dataset_id="test_dataset",
            drift_policy="/path/to/drift.yml",
            benchmark_policy="/path/to/bench.yml",
            wait=True,
        )

        call_args = mock_run_wait.call_args
        params = call_args[1]["parameters"]
        assert "drift_policy_path" in params
        assert "benchmark_policy_path" in params


# ---------------------------------------------------------------------------
# status() function tests
# ---------------------------------------------------------------------------


class TestStatus:
    """Verify the status() function."""

    @mock.patch("builtins.print")
    @mock.patch("driftsentinel.databricks.connect.bundle.summary")
    @mock.patch("driftsentinel.databricks.connect.bundle.app_get")
    @mock.patch("driftsentinel.databricks.connect.client.get_workspace_client")
    def test_status_success(
        self,
        mock_get_ws: mock.MagicMock,
        mock_app_get: mock.MagicMock,
        mock_summary: mock.MagicMock,
        mock_print: mock.MagicMock,
        bundle_summary_fixture: dict[str, Any],
        mock_ws: mock.MagicMock,
    ) -> None:
        """Status returns runtime paths, app URL, and job IDs."""
        mock_get_ws.return_value = mock_ws
        mock_app_get.return_value = {
            "url": "https://test.databricks.com/apps/driftsentinel",
            "app_status": {"state": "RUNNING"},
        }
        mock_summary.return_value = bundle_summary_fixture

        result = connect.status(
            catalog="adb_dev",
            schema="governed",
            volume_name=DEFAULT_RUNTIME_VOLUME_NAME,
        )

        assert "runtime_volume" in result
        assert "evidence_dir" in result
        assert "registry" in result
        assert result["app_url"] == "https://test.databricks.com/apps/driftsentinel"
        assert result["app_status"] == "RUNNING"
        assert "jobs" in result
        assert result["jobs"]["dataset_pipeline_job"] == "999"

    @mock.patch("builtins.print")
    @mock.patch("driftsentinel.databricks.connect.bundle.summary")
    @mock.patch("driftsentinel.databricks.connect.bundle.app_get")
    @mock.patch("driftsentinel.databricks.connect.client.get_workspace_client")
    def test_status_app_error_is_caught(
        self,
        mock_get_ws: mock.MagicMock,
        mock_app_get: mock.MagicMock,
        mock_summary: mock.MagicMock,
        mock_print: mock.MagicMock,
        bundle_summary_fixture: dict[str, Any],
        mock_ws: mock.MagicMock,
    ) -> None:
        """Status gracefully handles app_get errors."""
        mock_get_ws.return_value = mock_ws
        mock_app_get.side_effect = BundleError("App not deployed")
        mock_summary.return_value = bundle_summary_fixture

        result = connect.status(
            catalog="adb_dev",
            schema="governed",
            volume_name=DEFAULT_RUNTIME_VOLUME_NAME,
        )

        assert result["app_error"] == "App not deployed"
        assert result["jobs"]["dataset_pipeline_job"] == "999"


# ---------------------------------------------------------------------------
# sync() function tests
# ---------------------------------------------------------------------------


class TestSync:
    """Verify the sync() function for file uploads."""

    @mock.patch("driftsentinel.databricks.connect.files.sync_files")
    @mock.patch("driftsentinel.databricks.connect.client.resolve_identity")
    @mock.patch("driftsentinel.databricks.connect.client.get_workspace_client")
    def test_sync_basic(
        self,
        mock_get_ws: mock.MagicMock,
        mock_resolve_id: mock.MagicMock,
        mock_sync_files: mock.MagicMock,
        mock_identity: WorkspaceIdentity,
        mock_ws: mock.MagicMock,
    ) -> None:
        """Sync uploads files and returns remote paths."""
        mock_get_ws.return_value = mock_ws
        mock_resolve_id.return_value = mock_identity
        expected_paths = {
            "registry": "/Volumes/adb_dev/governed/ws_vol/registry.json",
            "evidence": "/Volumes/adb_dev/governed/ws_vol/evidence",
        }
        mock_sync_files.return_value = expected_paths

        result = connect.sync(
            catalog="adb_dev",
            schema="governed",
            volume_name=DEFAULT_RUNTIME_VOLUME_NAME,
            dataset_id="test_dataset",
        )

        assert result == expected_paths
        mock_sync_files.assert_called_once()

    @mock.patch("driftsentinel.databricks.connect.files.sync_files")
    @mock.patch("driftsentinel.databricks.connect.client.resolve_identity")
    @mock.patch("driftsentinel.databricks.connect.client.get_workspace_client")
    def test_sync_with_custom_paths(
        self,
        mock_get_ws: mock.MagicMock,
        mock_resolve_id: mock.MagicMock,
        mock_sync_files: mock.MagicMock,
        mock_identity: WorkspaceIdentity,
        mock_ws: mock.MagicMock,
    ) -> None:
        """Sync with custom policy and data paths."""
        mock_get_ws.return_value = mock_ws
        mock_resolve_id.return_value = mock_identity
        mock_sync_files.return_value = {}

        connect.sync(
            catalog="adb_dev",
            schema="governed",
            volume_name=DEFAULT_RUNTIME_VOLUME_NAME,
            dataset_id="test_dataset",
            registry="/custom/registry.json",
            drift_policy="/custom/drift.yml",
            benchmark_policy="/custom/bench.yml",
            landing_path="/custom/landing",
            baseline_path="/custom/baseline",
        )

        # Verify sync_files was called with all arguments
        call_args = mock_sync_files.call_args
        assert call_args[1]["registry_path"] == "/custom/registry.json"
        assert call_args[1]["drift_policy_path"] == "/custom/drift.yml"
        assert call_args[1]["benchmark_policy_path"] == "/custom/bench.yml"


# ---------------------------------------------------------------------------
# doctor() function tests
# ---------------------------------------------------------------------------


class TestDoctor:
    """Verify the doctor() diagnostic function."""

    @mock.patch("builtins.print")
    @mock.patch("driftsentinel.databricks.connect.bundle.summary")
    @mock.patch("driftsentinel.databricks.connect.bundle.validate")
    @mock.patch("driftsentinel.databricks.connect.client.resolve_identity")
    @mock.patch("driftsentinel.databricks.connect.client.get_workspace_client")
    def test_doctor_all_checks_pass(
        self,
        mock_get_ws: mock.MagicMock,
        mock_resolve_id: mock.MagicMock,
        mock_validate: mock.MagicMock,
        mock_summary: mock.MagicMock,
        mock_print: mock.MagicMock,
        bundle_summary_fixture: dict[str, Any],
        mock_identity: WorkspaceIdentity,
        mock_ws: mock.MagicMock,
    ) -> None:
        """Doctor with all checks passing."""
        mock_get_ws.return_value = mock_ws
        mock_resolve_id.return_value = mock_identity
        mock_ws.catalogs.get.return_value = mock.MagicMock()
        mock_validate.return_value = None
        mock_ws.files.get_status.return_value = mock.MagicMock()
        mock_summary.return_value = bundle_summary_fixture

        result = connect.doctor(
            catalog="adb_dev",
            schema="governed",
            volume_name=DEFAULT_RUNTIME_VOLUME_NAME,
        )

        assert result["auth"]["status"] == "OK"
        assert result["catalog"]["status"] == "OK"
        assert result["bundle"]["status"] == "OK"
        assert result["volume"]["status"] == "OK"
        assert result["jobs"]["status"] == "OK"

    @mock.patch("builtins.print")
    @mock.patch("driftsentinel.databricks.connect.client.get_workspace_client")
    def test_doctor_auth_fails_early_exit(
        self,
        mock_get_ws: mock.MagicMock,
        mock_print: mock.MagicMock,
        mock_ws: mock.MagicMock,
    ) -> None:
        """Doctor returns early if auth fails."""
        auth_error = Exception("Invalid token")
        mock_get_ws.side_effect = auth_error

        result = connect.doctor(
            catalog="adb_dev",
            schema="governed",
            volume_name=DEFAULT_RUNTIME_VOLUME_NAME,
        )

        assert result["auth"]["status"] == "FAIL"
        assert "Invalid token" in result["auth"]["error"]

    @mock.patch("builtins.print")
    @mock.patch("driftsentinel.databricks.connect.bundle.summary")
    @mock.patch("driftsentinel.databricks.connect.bundle.validate")
    @mock.patch("driftsentinel.databricks.connect.client.resolve_identity")
    @mock.patch("driftsentinel.databricks.connect.client.get_workspace_client")
    def test_doctor_volume_missing_returns_warn_status(
        self,
        mock_get_ws: mock.MagicMock,
        mock_resolve_id: mock.MagicMock,
        mock_validate: mock.MagicMock,
        mock_summary: mock.MagicMock,
        mock_print: mock.MagicMock,
        bundle_summary_fixture: dict[str, Any],
        mock_identity: WorkspaceIdentity,
        mock_ws: mock.MagicMock,
    ) -> None:
        """Doctor warns if volume doesn't exist yet (normal for first deploy)."""
        mock_get_ws.return_value = mock_ws
        mock_resolve_id.return_value = mock_identity
        mock_ws.catalogs.get.return_value = mock.MagicMock()
        mock_validate.return_value = None
        mock_ws.files.get_status.side_effect = Exception("Path does not exist")
        mock_summary.return_value = bundle_summary_fixture

        result = connect.doctor(
            catalog="adb_dev",
            schema="governed",
            volume_name=DEFAULT_RUNTIME_VOLUME_NAME,
        )

        assert result["volume"]["status"] == "WARN"
        assert "Path does not exist" in result["volume"]["note"]


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------


class TestHelperFunctions:
    """Verify helper functions for output and formatting."""

    def test_print_run_summary_success(self, capsys: pytest.CaptureFixture[str], mock_run_result: RunResult) -> None:
        """_print_run_summary formats success verdict."""
        connect._print_run_summary({}, mock_run_result)
        captured = capsys.readouterr()
        assert "PASS" in captured.err
        assert mock_run_result.run_page_url in captured.err

    def test_print_run_summary_failure(self, capsys: pytest.CaptureFixture[str]) -> None:
        """_print_run_summary formats failure verdict."""
        failed_result = RunResult(
            run_id=999,
            state="TERMINATED",
            result_state="FAILED",
            run_page_url="https://test.databricks.com/jobs/999",
            message="Task failed",
        )
        connect._print_run_summary({}, failed_result)
        captured = capsys.readouterr()
        assert "FAIL" in captured.err

    @mock.patch("driftsentinel.databricks.connect.bundle.app_get")
    def test_print_connect_summary(self, mock_app_get: mock.MagicMock, capsys: pytest.CaptureFixture[str]) -> None:
        """_print_connect_summary displays runtime info."""
        mock_app_get.return_value = {
            "url": "https://test.databricks.com/apps/driftsentinel",
        }
        result = {
            "run": {"run_page_url": "https://test.databricks.com/jobs/123"},
        }
        connect._print_connect_summary(
            result,
            catalog="adb_dev",
            schema="governed",
            volume_name=DEFAULT_RUNTIME_VOLUME_NAME,
            profile=None,
        )
        captured = capsys.readouterr()
        assert "DriftSentinel Connect Summary" in captured.err
        assert "Runtime volume" in captured.err


# ---------------------------------------------------------------------------
# poll_run early-exit on terminal states (regression for issue #38)
# ---------------------------------------------------------------------------


class _FakeEnum:
    """Stand-in for the Databricks SDK's RunLifeCycleState/RunResultState enums.

    The real SDK ships enum members whose ``.value`` is the canonical string
    (e.g. ``RunLifeCycleState.TERMINATED.value == "TERMINATED"``). Issue #38
    surfaced because ``poll_run`` was comparing the enum object itself to a
    set of strings — that comparison silently returned False and the loop
    polled until the deadline. This fake reproduces the failure mode.
    """

    def __init__(self, value: str) -> None:
        self.value = value

    def __str__(self) -> str:  # pragma: no cover - debugging aid only
        return f"FakeEnum.{self.value}"


def _make_run(*, life_cycle: Any, result_state: Any = None, message: str = "") -> mock.MagicMock:
    """Build a mock SDK Run object with the specified life-cycle/result state."""
    state = mock.MagicMock()
    state.life_cycle_state = life_cycle
    state.result_state = result_state
    state.state_message = message
    run = mock.MagicMock()
    run.state = state
    run.run_page_url = "https://test.databricks.com/jobs/999/runs/123"
    run.tasks = []
    return run


class TestPollRunEarlyExit:
    """Regression coverage for issue #38: poll_run must exit on terminal states.

    Acceptance criteria (from the issue body):
    - Returns immediately on TERMINATED / SKIPPED / INTERNAL_ERROR
    - Returned RunResult carries the actual result_state
    - JobRunError raised only on real timeouts (still polling at deadline)
    - Regression: simulate a job flipping to terminal at iter N and assert exit
    """

    def test_terminated_success_returns_immediately(self) -> None:
        """Job that terminated SUCCESS on the first poll exits in one iteration."""
        from driftsentinel.databricks.jobs import poll_run

        client = mock.MagicMock()
        client.jobs.get_run.return_value = _make_run(
            life_cycle=_FakeEnum("TERMINATED"),
            result_state=_FakeEnum("SUCCESS"),
            message="ok",
        )
        result = poll_run(client, run_id=1, poll_interval_s=0, timeout_s=60)

        assert result.state == "TERMINATED"
        assert result.result_state == "SUCCESS"
        assert result.succeeded is True
        assert client.jobs.get_run.call_count == 1

    def test_terminated_failed_returns_immediately(self) -> None:
        """Job that terminated FAILED exits with result_state propagated."""
        from driftsentinel.databricks.jobs import poll_run

        client = mock.MagicMock()
        client.jobs.get_run.return_value = _make_run(
            life_cycle=_FakeEnum("TERMINATED"),
            result_state=_FakeEnum("FAILED"),
            message="boom",
        )
        result = poll_run(client, run_id=2, poll_interval_s=0, timeout_s=60)

        assert result.state == "TERMINATED"
        assert result.result_state == "FAILED"
        assert result.succeeded is False
        assert result.message == "boom"

    def test_internal_error_returns_immediately(self) -> None:
        """INTERNAL_ERROR (the demo's iter-1 case) is treated as terminal."""
        from driftsentinel.databricks.jobs import poll_run

        client = mock.MagicMock()
        client.jobs.get_run.return_value = _make_run(
            life_cycle=_FakeEnum("INTERNAL_ERROR"),
            result_state=_FakeEnum("FAILED"),
        )
        result = poll_run(client, run_id=3, poll_interval_s=0, timeout_s=60)

        assert result.state == "INTERNAL_ERROR"
        assert result.result_state == "FAILED"
        assert client.jobs.get_run.call_count == 1

    def test_skipped_returns_immediately(self) -> None:
        """SKIPPED life-cycle is also terminal."""
        from driftsentinel.databricks.jobs import poll_run

        client = mock.MagicMock()
        client.jobs.get_run.return_value = _make_run(
            life_cycle=_FakeEnum("SKIPPED"),
            result_state=_FakeEnum("SKIPPED"),
        )
        result = poll_run(client, run_id=4, poll_interval_s=0, timeout_s=60)

        assert result.state == "SKIPPED"

    def test_string_typed_state_still_works(self) -> None:
        """Plain-string life_cycle_state (defensive path) also exits cleanly."""
        from driftsentinel.databricks.jobs import poll_run

        client = mock.MagicMock()
        client.jobs.get_run.return_value = _make_run(
            life_cycle="TERMINATED",
            result_state="SUCCESS",
        )
        result = poll_run(client, run_id=5, poll_interval_s=0, timeout_s=60)

        assert result.state == "TERMINATED"
        assert result.result_state == "SUCCESS"

    def test_running_then_terminated_exits_at_terminal_iteration(self) -> None:
        """Job pending for 3 polls then TERMINATED on the 4th exits at iter 4, not deadline."""
        from driftsentinel.databricks.jobs import poll_run

        client = mock.MagicMock()
        pending = _make_run(life_cycle=_FakeEnum("RUNNING"))
        terminal = _make_run(
            life_cycle=_FakeEnum("TERMINATED"),
            result_state=_FakeEnum("SUCCESS"),
        )
        client.jobs.get_run.side_effect = [pending, pending, pending, terminal]

        result = poll_run(client, run_id=6, poll_interval_s=0, timeout_s=60)

        assert result.state == "TERMINATED"
        assert result.result_state == "SUCCESS"
        assert client.jobs.get_run.call_count == 4

    def test_real_timeout_still_raises(self) -> None:
        """A run that never terminates raises JobRunError once the deadline passes."""
        from driftsentinel.databricks.jobs import JobRunError, poll_run

        client = mock.MagicMock()
        client.jobs.get_run.return_value = _make_run(life_cycle=_FakeEnum("RUNNING"))

        with pytest.raises(JobRunError, match="timed out"):
            poll_run(client, run_id=7, poll_interval_s=0, timeout_s=0)

    def test_unknown_state_keeps_polling(self) -> None:
        """A None life_cycle_state should not be mistaken for a terminal state."""
        from driftsentinel.databricks.jobs import JobRunError, poll_run

        client = mock.MagicMock()
        client.jobs.get_run.return_value = _make_run(life_cycle=None)

        # With timeout=0 this raises immediately rather than treating UNKNOWN as terminal.
        with pytest.raises(JobRunError):
            poll_run(client, run_id=8, poll_interval_s=0, timeout_s=0)

    def test_task_state_propagates_via_enum(self) -> None:
        """Task-level result_state enum values are also unwrapped."""
        from driftsentinel.databricks.jobs import poll_run

        client = mock.MagicMock()
        run = _make_run(
            life_cycle=_FakeEnum("TERMINATED"),
            result_state=_FakeEnum("FAILED"),
        )
        task_state = mock.MagicMock()
        task_state.result_state = _FakeEnum("FAILED")
        task = mock.MagicMock()
        task.task_key = "run_dataset_pipeline"
        task.state = task_state
        run.tasks = [task]
        client.jobs.get_run.return_value = run

        result = poll_run(client, run_id=9, poll_interval_s=0, timeout_s=60)

        assert result.tasks == [{"task_key": "run_dataset_pipeline", "state": "FAILED"}]
