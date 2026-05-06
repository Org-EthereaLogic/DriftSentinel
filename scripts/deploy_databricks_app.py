"""Deploy the DriftSentinel Databricks App from bundle-uploaded source."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from typing import Any, Callable

import yaml

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


def _resolve_app_resource_values(summary: dict[str, Any], app_key: str) -> dict[str, str]:
    """Map each app `config.resources[].name` to its concrete env value.

    - VOLUME `uc_securable` -> `/Volumes/<catalog>/<schema>/<volume>` parsed
      from `securable_full_name` when concrete, otherwise constructed from
      `summary.variables.{catalog,schema,runtime_volume_name}`.
    - `job` -> the resolved job `id`. When the embedded id is still a
      `${resources.jobs.<key>.id}` reference, look it up under
      `summary.resources.jobs.<key>.id`.
    """
    apps = summary.get("resources", {}).get("apps", {}) or {}
    app = apps.get(app_key) or {}
    config = app.get("config") or {}
    app_resources = config.get("resources") or []

    variables = summary.get("variables") or {}
    catalog = (variables.get("catalog") or {}).get("value", "") or ""
    schema = (variables.get("schema") or {}).get("value", "") or "default"
    volume_name = (variables.get("runtime_volume_name") or {}).get("value", "") or "driftsentinel_runtime"

    jobs_block = summary.get("resources", {}).get("jobs", {}) or {}

    resolutions: dict[str, str] = {}
    for res in app_resources:
        name = res.get("name")
        if not name:
            continue

        uc = res.get("uc_securable")
        if isinstance(uc, dict) and uc.get("securable_type") == "VOLUME":
            full = uc.get("securable_full_name") or ""
            if not full or "${" in full:
                full = f"{catalog}.{schema}.{volume_name}"
            parts = full.split(".")
            if len(parts) == 3 and all(parts):
                resolutions[name] = f"/Volumes/{parts[0]}/{parts[1]}/{parts[2]}"
            else:
                resolutions[name] = ""
            continue

        job = res.get("job")
        if isinstance(job, dict):
            raw_id = job.get("id")
            job_id = "" if raw_id is None else str(raw_id)
            if job_id and not job_id.startswith("${"):
                resolutions[name] = job_id
            else:
                # Reference shape: ${resources.jobs.<key>.id}
                ref_key = ""
                if "resources.jobs." in job_id:
                    after = job_id.split("resources.jobs.", 1)[1]
                    ref_key = after.split(".", 1)[0]
                resolutions[name] = str((jobs_block.get(ref_key) or {}).get("id", "") or "")

    return resolutions


def _build_app_yaml_content(summary: dict[str, Any], app_key: str) -> str | None:
    """Render an app.yml string from the bundle summary, or None if no command."""
    apps = summary.get("resources", {}).get("apps", {}) or {}
    app = apps.get(app_key) or {}
    config = app.get("config") or {}
    command = config.get("command")
    if not command:
        return None

    resolutions = _resolve_app_resource_values(summary, app_key)
    env_in = config.get("env") or []
    env_out: list[dict[str, Any]] = []
    for entry in env_in:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        if not name:
            continue
        if "value" in entry:
            env_out.append({"name": name, "value": entry["value"]})
        elif "value_from" in entry:
            env_out.append({"name": name, "value": resolutions.get(entry["value_from"], "")})
        else:
            env_out.append({"name": name, "value": ""})

    return yaml.safe_dump(
        {"command": list(command), "env": env_out},
        sort_keys=False,
        default_flow_style=False,
    )


def _upload_app_yaml(
    content: str,
    source_code_path: str,
    app_api_args: list[str],
    *,
    env: dict[str, str] | None,
) -> None:
    target = source_code_path.rstrip("/") + "/app.yml"
    fd, local_path = tempfile.mkstemp(suffix=".yml", prefix="driftsentinel-app-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        _run(
            [
                "databricks",
                "workspace",
                "import",
                target,
                "--file",
                local_path,
                "--format",
                "AUTO",
                "--overwrite",
                *app_api_args,
            ],
            env=env,
        )
    finally:
        try:
            os.unlink(local_path)
        except OSError:
            pass


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


def _build_apps_deploy_cmd(
    app_name: str,
    source_code_path: str,
    app_api_args: list[str],
) -> list[str]:
    return [
        "databricks",
        "apps",
        "deploy",
        app_name,
        "--source-code-path",
        source_code_path,
        *app_api_args,
    ]


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
    source_code_path = app.get("source_code_path") or ""
    if not source_code_path:
        raise SystemExit(f"App resource '{args.app_key}' is missing 'source_code_path' in bundle summary")

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

    app_yaml = _build_app_yaml_content(summary, args.app_key)
    if app_yaml is not None:
        _upload_app_yaml(app_yaml, source_code_path, app_api_args, env=env)

    deploy_cmd = _build_apps_deploy_cmd(app_name, source_code_path, app_api_args)
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
