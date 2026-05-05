"""Deploy the DriftSentinel Databricks App from bundle-uploaded source."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from typing import Any, Callable

from driftsentinel.databricks.tf_env import (
    TerraformBinaryMissingError,
    resolve_tf_env,
)


def _run(
    cmd: list[str],
    *,
    capture_json: bool = False,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> dict[str, Any] | subprocess.CompletedProcess[str] | None:
    print("+", " ".join(cmd))
    proc = subprocess.run(cmd, text=True, capture_output=True, env=env, check=False)
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    if check and proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, cmd, proc.stdout, proc.stderr)
    if capture_json:
        assert proc.stdout
        return json.loads(proc.stdout)
    return proc


def _bundle_flag_args(profile: str | None, target: str, catalog: str) -> list[str]:
    args = ["--target", target, f"--var=catalog={catalog}"]
    if profile:
        args = ["-p", profile, *args]
    return args


def _app_api_args(profile: str | None) -> list[str]:
    return ["-p", profile] if profile else []


def _get_app_state(
    app_name: str,
    app_api_args: list[str],
    *,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    state = _run(
        ["databricks", "apps", "get", app_name, *app_api_args, "-o", "json"],
        capture_json=True,
        env=env,
    )
    assert isinstance(state, dict)
    return state


def _wait_for_app_state(
    app_name: str,
    app_api_args: list[str],
    *,
    env: dict[str, str] | None = None,
    timeout_s: int,
    timeout_message: str,
    is_ready: Callable[[dict[str, Any]], bool],
    waiting_message: Callable[[dict[str, Any]], str],
) -> dict[str, Any]:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        state = _get_app_state(app_name, app_api_args, env=env)
        if is_ready(state):
            return state
        print(waiting_message(state))
        time.sleep(5)
    raise SystemExit(timeout_message)


def _wait_for_active_compute(
    app_name: str,
    app_api_args: list[str],
    *,
    env: dict[str, str] | None = None,
    timeout_s: int = 1200,
) -> dict[str, Any]:
    def _is_ready(state: dict[str, Any]) -> bool:
        compute = state.get("compute_status", {})
        return compute.get("state") == "ACTIVE"

    def _waiting_message(state: dict[str, Any]) -> str:
        compute = state.get("compute_status", {})
        return f"Waiting for app compute to become ACTIVE: {compute.get('state')} {compute.get('message')}"

    return _wait_for_app_state(
        app_name,
        app_api_args,
        env=env,
        timeout_s=timeout_s,
        timeout_message="Timed out waiting for app compute to become ACTIVE",
        is_ready=_is_ready,
        waiting_message=_waiting_message,
    )


def _wait_for_deployment(
    app_name: str,
    app_api_args: list[str],
    *,
    source_code_path: str,
    env: dict[str, str] | None = None,
    timeout_s: int = 1200,
) -> dict[str, Any]:
    def _is_ready(state: dict[str, Any]) -> bool:
        active = state.get("active_deployment", {})
        app_status = state.get("app_status", {})
        return (
            active.get("source_code_path") == source_code_path
            and active.get("status", {}).get("state") == "SUCCEEDED"
            and app_status.get("state") == "RUNNING"
        )

    def _waiting_message(state: dict[str, Any]) -> str:
        active = state.get("active_deployment", {})
        pending = state.get("pending_deployment", {})
        app_status = state.get("app_status", {})

        if pending and pending.get("source_code_path") == source_code_path:
            status = pending.get("status", {})
            return (
                f"Waiting for pending deployment {pending.get('deployment_id')}: "
                f"{status.get('state')} {status.get('message')}"
            )

        if active.get("source_code_path") == source_code_path and active.get("status", {}).get("state") == "FAILED":
            status = active.get("status", {})
            raise SystemExit(f"Active deployment failed: {status.get('state')} {status.get('message')}")

        return f"Waiting for app to report RUNNING: {app_status.get('state')} {app_status.get('message')}"

    return _wait_for_app_state(
        app_name,
        app_api_args,
        env=env,
        timeout_s=timeout_s,
        timeout_message="Timed out waiting for app deployment to succeed",
        is_ready=_is_ready,
        waiting_message=_waiting_message,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--target", default="dev")
    parser.add_argument("--profile")
    parser.add_argument("--app-key", default="driftsentinel_app")
    args = parser.parse_args()

    try:
        env = resolve_tf_env()
    except TerraformBinaryMissingError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    bundle_args = _bundle_flag_args(args.profile, args.target, args.catalog)

    _run(["databricks", "bundle", "deploy", *bundle_args], env=env)

    summary = _run(
        ["databricks", "bundle", "summary", *bundle_args, "-o", "json"],
        capture_json=True,
        env=env,
    )
    assert summary is not None

    apps = summary.get("resources", {}).get("apps", {})
    if args.app_key not in apps:
        raise SystemExit(f"App resource '{args.app_key}' not found in bundle summary")
    app = apps[args.app_key]
    app_name = app["name"]
    source_code_path = app["source_code_path"]

    app_api_args = _app_api_args(args.profile)

    _run(["databricks", "apps", "start", app_name, *app_api_args], env=env)
    app_state = _wait_for_active_compute(app_name, app_api_args, env=env)

    pending = app_state.get("pending_deployment", {})

    if pending and pending.get("source_code_path") == source_code_path:
        app_state = _wait_for_deployment(
            app_name,
            app_api_args,
            source_code_path=source_code_path,
            env=env,
        )
        print(f"App URL: {app_state['url']}")
        return 0

    deploy_cmd = ["databricks", "apps", "deploy", *bundle_args]
    deploy_proc = _run(deploy_cmd, check=False, env=env)
    assert isinstance(deploy_proc, subprocess.CompletedProcess)
    if deploy_proc.returncode != 0:
        conflict = "pending deployment in progress" in (deploy_proc.stderr or "")
        if not conflict:
            raise subprocess.CalledProcessError(
                deploy_proc.returncode,
                deploy_cmd,
                deploy_proc.stdout,
                deploy_proc.stderr,
            )
    app_state = _wait_for_deployment(
        app_name,
        app_api_args,
        source_code_path=source_code_path,
        env=env,
    )

    deployment = app_state.get("active_deployment", {}).get("status", {})
    app_status = app_state.get("app_status", {})
    if deployment.get("state") != "SUCCEEDED":
        raise SystemExit(f"Active deployment did not succeed: {deployment.get('state')} {deployment.get('message')}")
    if app_status.get("state") != "RUNNING":
        raise SystemExit(f"App is not running: {app_status.get('state')} {app_status.get('message')}")

    print(f"App URL: {app_state['url']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
