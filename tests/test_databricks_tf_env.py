"""Tests for driftsentinel.databricks.tf_env — terraform-binary resolution shim.

Covers the precedence in DS-PATCH-035 §4.1:

    1. Operator-set DATABRICKS_TF_EXEC_PATH wins.
    2. ``tofu`` on PATH -> set DATABRICKS_TF_EXEC_PATH and (if unset)
       DATABRICKS_TF_VERSION = OPENTOFU_VERSION_DEFAULT.
    3. ``terraform`` on PATH -> set DATABRICKS_TF_EXEC_PATH only.
    4. Otherwise raise TerraformBinaryMissingError.

Also locks in the env-propagation contract for the bundle subprocess
wrapper so DS-PATCH-035 §4.5 cannot regress.
"""

from __future__ import annotations

import os
import subprocess
from typing import Any
from unittest import mock

import pytest

from driftsentinel.databricks import bundle as bundle_mod
from driftsentinel.databricks.tf_env import (
    OPENTOFU_VERSION_DEFAULT,
    TerraformBinaryMissingError,
    resolve_tf_env,
)


class TestResolveTfEnvOperatorOverride:
    """Branch 1: existing DATABRICKS_TF_EXEC_PATH wins."""

    def test_override_preserved_and_no_lookup_performed(self) -> None:
        base = {"DATABRICKS_TF_EXEC_PATH": "/custom/tf", "PATH": "/usr/bin"}

        with mock.patch("driftsentinel.databricks.tf_env.shutil.which") as mock_which:
            env = resolve_tf_env(base)

        assert env["DATABRICKS_TF_EXEC_PATH"] == "/custom/tf"
        assert "DATABRICKS_TF_VERSION" not in env
        mock_which.assert_not_called()

    def test_empty_override_falls_through_to_detection(self) -> None:
        """Empty DATABRICKS_TF_EXEC_PATH must be treated as unset (matches shell)."""
        base = {"DATABRICKS_TF_EXEC_PATH": "", "PATH": "/usr/bin"}

        with mock.patch(
            "driftsentinel.databricks.tf_env.shutil.which",
            side_effect=lambda name: "/opt/homebrew/bin/tofu" if name == "tofu" else None,
        ):
            env = resolve_tf_env(base)

        assert env["DATABRICKS_TF_EXEC_PATH"] == "/opt/homebrew/bin/tofu"


class TestResolveTfEnvOpenTofu:
    """Branch 2: tofu on PATH wins over terraform; default version applied if unset."""

    def test_tofu_detected_sets_default_version(self) -> None:
        base: dict[str, str] = {"PATH": "/opt/homebrew/bin"}

        with mock.patch(
            "driftsentinel.databricks.tf_env.shutil.which",
            side_effect=lambda name: "/opt/homebrew/bin/tofu" if name == "tofu" else None,
        ):
            env = resolve_tf_env(base)

        assert env["DATABRICKS_TF_EXEC_PATH"] == "/opt/homebrew/bin/tofu"
        assert env["DATABRICKS_TF_VERSION"] == OPENTOFU_VERSION_DEFAULT

    def test_tofu_detected_preserves_operator_set_version(self) -> None:
        base = {"DATABRICKS_TF_VERSION": "1.10.2", "PATH": "/opt/homebrew/bin"}

        with mock.patch(
            "driftsentinel.databricks.tf_env.shutil.which",
            side_effect=lambda name: "/opt/homebrew/bin/tofu" if name == "tofu" else None,
        ):
            env = resolve_tf_env(base)

        assert env["DATABRICKS_TF_EXEC_PATH"] == "/opt/homebrew/bin/tofu"
        assert env["DATABRICKS_TF_VERSION"] == "1.10.2"

    def test_tofu_preferred_over_terraform_when_both_present(self) -> None:
        base: dict[str, str] = {"PATH": "/usr/local/bin"}

        def fake_which(name: str) -> str | None:
            return {
                "tofu": "/opt/homebrew/bin/tofu",
                "terraform": "/usr/local/bin/terraform",
            }.get(name)

        with mock.patch("driftsentinel.databricks.tf_env.shutil.which", side_effect=fake_which):
            env = resolve_tf_env(base)

        assert env["DATABRICKS_TF_EXEC_PATH"] == "/opt/homebrew/bin/tofu"
        assert env["DATABRICKS_TF_VERSION"] == OPENTOFU_VERSION_DEFAULT


class TestResolveTfEnvSystemTerraform:
    """Branch 3: terraform on PATH only; no version injection."""

    def test_terraform_detected_no_version_set(self) -> None:
        base: dict[str, str] = {"PATH": "/usr/local/bin"}

        def fake_which(name: str) -> str | None:
            return "/usr/local/bin/terraform" if name == "terraform" else None

        with mock.patch("driftsentinel.databricks.tf_env.shutil.which", side_effect=fake_which):
            env = resolve_tf_env(base)

        assert env["DATABRICKS_TF_EXEC_PATH"] == "/usr/local/bin/terraform"
        assert "DATABRICKS_TF_VERSION" not in env


class TestResolveTfEnvFailClosed:
    """Branch 4: neither binary available — raise actionable error."""

    def test_neither_binary_raises_with_actionable_message(self) -> None:
        base: dict[str, str] = {"PATH": "/usr/bin"}

        with mock.patch("driftsentinel.databricks.tf_env.shutil.which", return_value=None):
            with pytest.raises(TerraformBinaryMissingError) as excinfo:
                resolve_tf_env(base)

        msg = str(excinfo.value)
        assert "tofu" in msg
        assert "terraform" in msg
        assert "DATABRICKS_TF_EXEC_PATH" in msg
        assert "brew install opentofu" in msg
        assert "DS-PATCH-035" in msg


class TestResolveTfEnvOsEnvironContract:
    """The function reads os.environ when ``base`` is omitted but never mutates it."""

    def test_os_environ_unchanged_after_call(self) -> None:
        snapshot = dict(os.environ)
        # Force a deterministic branch independent of the host's PATH.
        with (
            mock.patch(
                "driftsentinel.databricks.tf_env.shutil.which",
                side_effect=lambda name: "/opt/homebrew/bin/tofu" if name == "tofu" else None,
            ),
            mock.patch.dict(os.environ, {}, clear=False),
        ):
            os.environ.pop("DATABRICKS_TF_EXEC_PATH", None)
            os.environ.pop("DATABRICKS_TF_VERSION", None)
            resolve_tf_env()

        # Whatever resolve_tf_env did, it must not have mutated the live mapping.
        assert dict(os.environ) == snapshot


class TestBundleEnvPropagation:
    """DS-PATCH-035 §4.5 / §6.2: bundle._run_bundle must propagate the resolved env.

    These tests are the regression contract that prevents future edits to
    bundle.py from dropping the ``env=`` kwarg on subprocess.run.
    """

    @mock.patch("driftsentinel.databricks.bundle.subprocess.run")
    @mock.patch(
        "driftsentinel.databricks.bundle.resolve_tf_env",
        return_value={"DATABRICKS_TF_EXEC_PATH": "/opt/homebrew/bin/tofu", "DATABRICKS_TF_VERSION": "1.11.6"},
    )
    def test_validate_passes_env_to_subprocess(
        self,
        mock_resolve: mock.MagicMock,
        mock_run: mock.MagicMock,
    ) -> None:
        proc = mock.MagicMock()
        proc.returncode = 0
        proc.stdout = "Validation OK!"
        proc.stderr = ""
        mock_run.return_value = proc

        bundle_mod.validate(catalog="my_catalog")

        env_kwarg: dict[str, str] = mock_run.call_args.kwargs["env"]
        assert env_kwarg["DATABRICKS_TF_EXEC_PATH"] == "/opt/homebrew/bin/tofu"
        assert env_kwarg["DATABRICKS_TF_VERSION"] == "1.11.6"
        mock_resolve.assert_called_once()

    @mock.patch("driftsentinel.databricks.bundle.subprocess.run")
    @mock.patch(
        "driftsentinel.databricks.bundle.resolve_tf_env",
        return_value={"DATABRICKS_TF_EXEC_PATH": "/opt/homebrew/bin/tofu"},
    )
    def test_deploy_passes_env_to_subprocess(
        self,
        mock_resolve: mock.MagicMock,
        mock_run: mock.MagicMock,
    ) -> None:
        proc = mock.MagicMock()
        proc.returncode = 0
        proc.stdout = "Deployment complete"
        proc.stderr = ""
        mock_run.return_value = proc

        bundle_mod.deploy(catalog="my_catalog")

        env_kwarg: dict[str, str] = mock_run.call_args.kwargs["env"]
        assert env_kwarg["DATABRICKS_TF_EXEC_PATH"] == "/opt/homebrew/bin/tofu"

    @mock.patch("driftsentinel.databricks.bundle.subprocess.run")
    @mock.patch(
        "driftsentinel.databricks.bundle.resolve_tf_env",
        return_value={"DATABRICKS_TF_EXEC_PATH": "/opt/homebrew/bin/tofu"},
    )
    def test_summary_passes_env_to_subprocess(
        self,
        mock_resolve: mock.MagicMock,
        mock_run: mock.MagicMock,
    ) -> None:
        proc = mock.MagicMock()
        proc.returncode = 0
        proc.stdout = '{"resources": {}}'
        proc.stderr = ""
        mock_run.return_value = proc

        bundle_mod.summary(catalog="my_catalog")

        env_kwarg: dict[str, str] = mock_run.call_args.kwargs["env"]
        assert env_kwarg["DATABRICKS_TF_EXEC_PATH"] == "/opt/homebrew/bin/tofu"

    @mock.patch("driftsentinel.databricks.bundle.subprocess.run")
    @mock.patch(
        "driftsentinel.databricks.bundle.resolve_tf_env",
        return_value={"DATABRICKS_TF_EXEC_PATH": "/opt/homebrew/bin/tofu"},
    )
    def test_app_start_passes_env_to_subprocess(
        self,
        mock_resolve: mock.MagicMock,
        mock_run: mock.MagicMock,
    ) -> None:
        proc = mock.MagicMock()
        proc.returncode = 0
        proc.stdout = "started"
        proc.stderr = ""
        mock_run.return_value = proc

        bundle_mod.app_start("driftsentinel")

        env_kwarg: dict[str, str] = mock_run.call_args.kwargs["env"]
        assert env_kwarg["DATABRICKS_TF_EXEC_PATH"] == "/opt/homebrew/bin/tofu"

    @mock.patch("driftsentinel.databricks.bundle.subprocess.run")
    @mock.patch(
        "driftsentinel.databricks.bundle.resolve_tf_env",
        return_value={"DATABRICKS_TF_EXEC_PATH": "/opt/homebrew/bin/tofu"},
    )
    def test_app_get_passes_env_to_subprocess(
        self,
        mock_resolve: mock.MagicMock,
        mock_run: mock.MagicMock,
    ) -> None:
        proc = mock.MagicMock()
        proc.returncode = 0
        proc.stdout = '{"name": "driftsentinel"}'
        proc.stderr = ""
        mock_run.return_value = proc

        bundle_mod.app_get("driftsentinel")

        env_kwarg: dict[str, str] = mock_run.call_args.kwargs["env"]
        assert env_kwarg["DATABRICKS_TF_EXEC_PATH"] == "/opt/homebrew/bin/tofu"

    @pytest.mark.parametrize("method_name", ["app_start", "app_get"])
    def test_app_commands_wrap_resolution_failure_as_bundle_error(self, method_name: str) -> None:
        with (
            mock.patch(
                "driftsentinel.databricks.bundle.resolve_tf_env",
                side_effect=TerraformBinaryMissingError("no tf binary"),
            ),
            mock.patch("driftsentinel.databricks.bundle.subprocess.run") as mock_run,
        ):
            command = getattr(bundle_mod, method_name)
            with pytest.raises(bundle_mod.BundleError, match="no tf binary"):
                command("driftsentinel")
            mock_run.assert_not_called()

    def test_validate_propagates_resolution_failure(self) -> None:
        """If resolve_tf_env raises, bundle.validate must not call subprocess.run."""
        with (
            mock.patch(
                "driftsentinel.databricks.bundle.resolve_tf_env",
                side_effect=TerraformBinaryMissingError("no tf binary"),
            ),
            mock.patch("driftsentinel.databricks.bundle.subprocess.run") as mock_run,
        ):
            with pytest.raises(TerraformBinaryMissingError, match="no tf binary"):
                bundle_mod.validate(catalog="my_catalog")
            mock_run.assert_not_called()


class TestShellHelperParity:
    """The shell helper exists and exports the same env vars as the Python helper."""

    def test_shell_helper_file_exists(self) -> None:
        from pathlib import Path

        repo_root = Path(__file__).resolve().parents[1]
        helper = repo_root / "scripts" / "databricks_tf_env.sh"

        assert helper.is_file(), "scripts/databricks_tf_env.sh must exist"
        body = helper.read_text()
        # Anchor on the contract surfaces, not the exact wording, so minor
        # editorial changes do not break the test.
        assert "DATABRICKS_TF_EXEC_PATH" in body
        assert "DATABRICKS_TF_VERSION" in body
        assert "tofu" in body
        assert "terraform" in body
        assert "brew install opentofu" in body
        assert "DS-PATCH-035" in body

    def test_shell_helper_resolves_tofu_when_present(self, tmp_path: Any) -> None:
        """End-to-end: a stub 'tofu' on PATH must yield the expected exports."""
        from pathlib import Path

        repo_root = Path(__file__).resolve().parents[1]
        helper = repo_root / "scripts" / "databricks_tf_env.sh"

        stub_dir = tmp_path / "bin"
        stub_dir.mkdir()
        tofu_stub = stub_dir / "tofu"
        tofu_stub.write_text("#!/bin/sh\nexit 0\n")
        tofu_stub.chmod(0o755)

        env = {"PATH": str(stub_dir)}
        # Run a child shell that sources the helper and prints the resolved values.
        cmd = f'. {helper} && printf \'%s\\n%s\\n\' "$DATABRICKS_TF_EXEC_PATH" "$DATABRICKS_TF_VERSION"'
        result = subprocess.run(
            ["/bin/sh", "-c", cmd],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        lines = result.stdout.strip().splitlines()
        assert lines[0] == str(tofu_stub)
        assert lines[1] == OPENTOFU_VERSION_DEFAULT

    def test_shell_helper_fails_closed_when_no_binary(self, tmp_path: Any) -> None:
        from pathlib import Path

        repo_root = Path(__file__).resolve().parents[1]
        helper = repo_root / "scripts" / "databricks_tf_env.sh"

        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        env = {"PATH": str(empty_dir)}

        result = subprocess.run(
            ["/bin/sh", "-c", f". {helper} && echo OK"],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        assert result.returncode != 0
        assert "OK" not in result.stdout
        assert "brew install opentofu" in result.stderr
        assert "DS-PATCH-035" in result.stderr

    def test_shell_helper_preserves_operator_override(self, tmp_path: Any) -> None:
        from pathlib import Path

        repo_root = Path(__file__).resolve().parents[1]
        helper = repo_root / "scripts" / "databricks_tf_env.sh"

        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        env = {
            "PATH": str(empty_dir),
            "DATABRICKS_TF_EXEC_PATH": "/operator/override/tf",
        }

        cmd = f'. {helper} && printf \'%s\\n%s\\n\' "$DATABRICKS_TF_EXEC_PATH" "${{DATABRICKS_TF_VERSION:-UNSET}}"'
        result = subprocess.run(
            ["/bin/sh", "-c", cmd],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        lines = result.stdout.strip().splitlines()
        assert lines[0] == "/operator/override/tf"
        assert lines[1] == "UNSET"
