"""Thin subprocess wrapper for Databricks Asset Bundle CLI operations."""

from __future__ import annotations

import json
import subprocess
import sys
from typing import Any

from driftsentinel.databricks.tf_env import TerraformBinaryMissingError, resolve_tf_env


class BundleError(RuntimeError):
    """Raised when a bundle CLI command fails."""


def _run_cli(
    cmd: list[str],
    *,
    failure_context: str,
    capture_json: bool = False,
    wrap_tf_env_error: bool = False,
) -> dict[str, Any] | str:
    """Run a Databricks CLI command and return stdout or parsed JSON."""
    print("+", " ".join(cmd), file=sys.stderr)
    try:
        env = resolve_tf_env()
    except TerraformBinaryMissingError as exc:
        if wrap_tf_env_error:
            raise BundleError(str(exc)) from exc
        raise

    proc = subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip()
        raise BundleError(f"{failure_context} failed (exit {proc.returncode}): {detail}")

    stdout = proc.stdout.strip()
    if capture_json:
        return json.loads(stdout)  # type: ignore[no-any-return]
    return stdout


def _run_bundle(
    args: list[str],
    *,
    profile: str | None = None,
    target: str = "dev",
    catalog: str | None = None,
    schema: str | None = None,
    volume_name: str | None = None,
    capture_json: bool = False,
) -> dict[str, Any] | str:
    """Run a ``databricks bundle`` subcommand and return stdout or parsed JSON."""
    cmd = ["databricks", "bundle", *args]
    if profile:
        cmd.extend(["-p", profile])
    cmd.extend(["--target", target])
    if catalog:
        cmd.append(f"--var=catalog={catalog}")
    if schema and schema != "default":
        cmd.append(f"--var=schema={schema}")
    if volume_name and volume_name != "driftsentinel_runtime":
        cmd.append(f"--var=runtime_volume_name={volume_name}")
    if capture_json:
        cmd.extend(["-o", "json"])
    return _run_cli(
        cmd,
        failure_context=f"bundle {args[0]}",
        capture_json=capture_json,
    )


def validate(
    *,
    profile: str | None = None,
    target: str = "dev",
    catalog: str,
    schema: str | None = None,
    volume_name: str | None = None,
) -> str:
    """Run ``databricks bundle validate`` and return stdout."""
    result = _run_bundle(
        ["validate"],
        profile=profile,
        target=target,
        catalog=catalog,
        schema=schema,
        volume_name=volume_name,
    )
    if not isinstance(result, str):
        raise BundleError("bundle validate returned non-text output")
    return result


def deploy(
    *,
    profile: str | None = None,
    target: str = "dev",
    catalog: str,
    schema: str | None = None,
    volume_name: str | None = None,
) -> str:
    """Run ``databricks bundle deploy`` and return stdout."""
    result = _run_bundle(
        ["deploy"],
        profile=profile,
        target=target,
        catalog=catalog,
        schema=schema,
        volume_name=volume_name,
    )
    if not isinstance(result, str):
        raise BundleError("bundle deploy returned non-text output")
    return result


def summary(
    *,
    profile: str | None = None,
    target: str = "dev",
    catalog: str,
    schema: str | None = None,
    volume_name: str | None = None,
) -> dict[str, Any]:
    """Run ``databricks bundle summary -o json`` and return the parsed dict."""
    result = _run_bundle(
        ["summary"],
        profile=profile,
        target=target,
        catalog=catalog,
        schema=schema,
        volume_name=volume_name,
        capture_json=True,
    )
    if not isinstance(result, dict):
        raise BundleError("bundle summary returned a non-object JSON payload")
    return result


def app_start(
    app_name: str,
    *,
    profile: str | None = None,
) -> str:
    """Run ``databricks apps start <app_name>`` and return stdout."""
    cmd = ["databricks", "apps", "start", app_name]
    if profile:
        cmd.extend(["-p", profile])
    result = _run_cli(cmd, failure_context="apps start", wrap_tf_env_error=True)
    if not isinstance(result, str):
        raise BundleError("apps start returned non-text output")
    return result


def app_get(
    app_name: str,
    *,
    profile: str | None = None,
) -> dict[str, Any]:
    """Run ``databricks apps get <app_name> -o json`` and return parsed state."""
    cmd = ["databricks", "apps", "get", app_name, "-o", "json"]
    if profile:
        cmd.extend(["-p", profile])
    result = _run_cli(
        cmd,
        failure_context="apps get",
        capture_json=True,
        wrap_tf_env_error=True,
    )
    if not isinstance(result, dict):
        raise BundleError("apps get returned a non-object JSON payload")
    return result
