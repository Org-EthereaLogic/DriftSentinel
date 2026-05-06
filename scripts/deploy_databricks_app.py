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
        if not proc.stdout:
            raise SystemExit(f"Command returned no JSON output: {' '.join(cmd)}")
        return json.loads(proc.stdout)
    return proc


def _run_json(cmd: list[str], *, env: dict[str, str] | None = None) -> dict[str, Any]:
    result = _run(cmd, capture_json=True, env=env)
    if not isinstance(result, dict):
        raise SystemExit(f"Command did not return a JSON object: {' '.join(cmd)}")
    return result


def _run_process(
    cmd: list[str],
    *,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    result = _run(cmd, check=check, env=env)
    if not isinstance(result, subprocess.CompletedProcess):
        raise SystemExit(f"Command did not return a process result: {' '.join(cmd)}")
    return result


def _bundle_flag_args(profile: str | None, target: str, catalog: str) -> list[str]:
    args = ["--target", target, f"--var=catalog={catalog}"]
    if profile:
        args = ["-p", profile, *args]
    return args


def _app_api_args(profile: str | None) -> list[str]:
    return ["-p", profile] if profile else []


def _mapping_entry(mapping: dict[str, Any], key: str) -> dict[str, Any]:
    value = mapping.get(key)
    return value if isinstance(value, dict) else {}


def _summary_resources(summary: dict[str, Any]) -> dict[str, Any]:
    return _mapping_entry(summary, "resources")


def _summary_apps(summary: dict[str, Any]) -> dict[str, Any]:
    return _mapping_entry(_summary_resources(summary), "apps")


def _summary_jobs(summary: dict[str, Any]) -> dict[str, Any]:
    return _mapping_entry(_summary_resources(summary), "jobs")


def _summary_variables(summary: dict[str, Any]) -> dict[str, Any]:
    return _mapping_entry(summary, "variables")


def _summary_variable_value(summary: dict[str, Any], key: str, default: str) -> str:
    value = _mapping_entry(_summary_variables(summary), key).get("value")
    if value in (None, ""):
        return default
    return str(value)


def _summary_app(summary: dict[str, Any], app_key: str) -> dict[str, Any]:
    return _mapping_entry(_summary_apps(summary), app_key)


def _app_resource_bindings(app: dict[str, Any]) -> list[dict[str, Any]]:
    resources = app.get("resources")
    if isinstance(resources, list):
        return [resource for resource in resources if isinstance(resource, dict)]

    config = app.get("config") or {}
    config_resources = config.get("resources")
    if isinstance(config_resources, list):
        return [resource for resource in config_resources if isinstance(resource, dict)]

    return []


def _resolve_volume_resource(
    resource: dict[str, Any],
    *,
    catalog: str,
    schema: str,
    volume_name: str,
) -> str | None:
    uc = resource.get("uc_securable")
    if not isinstance(uc, dict) or uc.get("securable_type") != "VOLUME":
        return None

    full_name = uc.get("securable_full_name") or ""
    if not full_name or "${" in full_name:
        full_name = f"{catalog}.{schema}.{volume_name}"

    parts = full_name.split(".")
    if len(parts) != 3 or not all(parts):
        return ""

    return f"/Volumes/{parts[0]}/{parts[1]}/{parts[2]}"


def _resolve_job_resource(resource: dict[str, Any], jobs_block: dict[str, Any]) -> str | None:
    job = resource.get("job")
    if not isinstance(job, dict):
        return None

    raw_id = job.get("id")
    job_id = "" if raw_id is None else str(raw_id)
    if job_id and not job_id.startswith("${"):
        return job_id

    ref_key = ""
    if "resources.jobs." in job_id:
        after = job_id.split("resources.jobs.", 1)[1]
        ref_key = after.split(".", 1)[0]
    return str((jobs_block.get(ref_key) or {}).get("id", "") or "")


def _resolve_resource_value(
    resource: dict[str, Any],
    *,
    catalog: str,
    schema: str,
    volume_name: str,
    jobs_block: dict[str, Any],
) -> str | None:
    volume_value = _resolve_volume_resource(
        resource,
        catalog=catalog,
        schema=schema,
        volume_name=volume_name,
    )
    if volume_value is not None:
        return volume_value
    return _resolve_job_resource(resource, jobs_block)


def _named_app_resources(app: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    named_resources: list[tuple[str, dict[str, Any]]] = []
    for resource in _app_resource_bindings(app):
        name = resource.get("name")
        if isinstance(name, str) and name:
            named_resources.append((name, resource))
    return named_resources


def _resolve_app_resource_values(summary: dict[str, Any], app_key: str) -> dict[str, str]:
    """Map each app `resources[].name` to its concrete env value.

    - VOLUME `uc_securable` -> `/Volumes/<catalog>/<schema>/<volume>` parsed
      from `securable_full_name` when concrete, otherwise constructed from
      `summary.variables.{catalog,schema,runtime_volume_name}`.
    - `job` -> the resolved job `id`. When the embedded id is still a
      `${resources.jobs.<key>.id}` reference, look it up under
      `summary.resources.jobs.<key>.id`.
    """
    app = _summary_app(summary, app_key)
    catalog = _summary_variable_value(summary, "catalog", "")
    schema = _summary_variable_value(summary, "schema", "default")
    volume_name = _summary_variable_value(summary, "runtime_volume_name", "driftsentinel_runtime")
    jobs_block = _summary_jobs(summary)

    resolutions: dict[str, str] = {}
    for name, resource in _named_app_resources(app):
        resource_value = _resolve_resource_value(
            resource,
            catalog=catalog,
            schema=schema,
            volume_name=volume_name,
            jobs_block=jobs_block,
        )
        if resource_value is not None:
            resolutions[name] = resource_value

    return resolutions


def _normalize_command(command: Any) -> list[str]:
    if isinstance(command, str):
        return [command]
    return [str(part) for part in command]


def _resolve_env_entry(entry: Any, resolutions: dict[str, str]) -> dict[str, Any] | None:
    if not isinstance(entry, dict):
        return None

    name = entry.get("name")
    if not name:
        return None

    if "value" in entry:
        return {"name": name, "value": entry["value"]}
    if "value_from" in entry:
        return {"name": name, "value": resolutions.get(entry["value_from"], "")}
    return {"name": name, "value": ""}


def _resolved_env_entries(config: dict[str, Any], resolutions: dict[str, str]) -> list[dict[str, Any]]:
    env_out: list[dict[str, Any]] = []
    for entry in config.get("env") or []:
        resolved = _resolve_env_entry(entry, resolutions)
        if resolved is not None:
            env_out.append(resolved)
    return env_out


def _build_app_yaml_content(summary: dict[str, Any], app_key: str) -> str | None:
    """Render an app.yml string from the bundle summary, or None if no command."""
    app = _summary_app(summary, app_key)
    config = app.get("config") or {}
    command = config.get("command")
    if not command:
        return None

    resolutions = _resolve_app_resource_values(summary, app_key)
    env_out = _resolved_env_entries(config, resolutions)

    return yaml.safe_dump(
        {"command": _normalize_command(command), "env": env_out},
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
            # Best-effort cleanup: ignore temp-file removal failures here.
            pass


def _get_app_state(
    app_name: str,
    app_api_args: list[str],
    *,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    return _run_json(
        ["databricks", "apps", "get", app_name, *app_api_args, "-o", "json"],
        env=env,
    )


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


def _bundle_deploy_and_summary(
    *,
    profile: str | None,
    target: str,
    catalog: str,
    env: dict[str, str] | None,
) -> dict[str, Any]:
    bundle_args = _bundle_flag_args(profile, target, catalog)
    _run(["databricks", "bundle", "deploy", *bundle_args], env=env)
    return _run_json(
        ["databricks", "bundle", "summary", *bundle_args, "-o", "json"],
        env=env,
    )


def _resolve_app_deploy_target(summary: dict[str, Any], app_key: str) -> tuple[str, str]:
    app = _summary_app(summary, app_key)
    if not app:
        raise SystemExit(f"App resource '{app_key}' not found in bundle summary")

    app_name = str(app.get("name") or "")
    if not app_name:
        raise SystemExit(f"App resource '{app_key}' is missing 'name' in bundle summary")

    source_code_path = str(app.get("source_code_path") or "")
    if not source_code_path:
        raise SystemExit(f"App resource '{app_key}' is missing 'source_code_path' in bundle summary")

    return app_name, source_code_path


def _has_pending_source_deployment(state: dict[str, Any], source_code_path: str) -> bool:
    pending = _mapping_entry(state, "pending_deployment")
    return pending.get("source_code_path") == source_code_path


def _start_app_and_wait_for_compute(
    app_name: str,
    app_api_args: list[str],
    *,
    env: dict[str, str] | None,
) -> dict[str, Any]:
    _run(["databricks", "apps", "start", app_name, *app_api_args], env=env)
    return _wait_for_active_compute(app_name, app_api_args, env=env)


def _deploy_source_code(
    summary: dict[str, Any],
    *,
    app_key: str,
    app_name: str,
    source_code_path: str,
    app_api_args: list[str],
    env: dict[str, str] | None,
) -> dict[str, Any]:
    app_yaml = _build_app_yaml_content(summary, app_key)
    if app_yaml is not None:
        _upload_app_yaml(app_yaml, source_code_path, app_api_args, env=env)

    deploy_cmd = _build_apps_deploy_cmd(app_name, source_code_path, app_api_args)
    deploy_proc = _run_process(deploy_cmd, check=False, env=env)
    if deploy_proc.returncode != 0 and "pending deployment in progress" not in (deploy_proc.stderr or ""):
        raise subprocess.CalledProcessError(
            deploy_proc.returncode,
            deploy_cmd,
            deploy_proc.stdout,
            deploy_proc.stderr,
        )

    return _wait_for_deployment(
        app_name,
        app_api_args,
        source_code_path=source_code_path,
        env=env,
    )


def _require_running_app(app_state: dict[str, Any]) -> None:
    deployment = _mapping_entry(app_state, "active_deployment").get("status", {})
    app_status = _mapping_entry(app_state, "app_status")
    if deployment.get("state") != "SUCCEEDED":
        raise SystemExit(f"Active deployment did not succeed: {deployment.get('state')} {deployment.get('message')}")
    if app_status.get("state") != "RUNNING":
        raise SystemExit(f"App is not running: {app_status.get('state')} {app_status.get('message')}")


def _print_app_url(app_state: dict[str, Any]) -> None:
    print(f"App URL: {app_state['url']}")


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

    summary = _bundle_deploy_and_summary(
        profile=args.profile,
        target=args.target,
        catalog=args.catalog,
        env=env,
    )
    app_name, source_code_path = _resolve_app_deploy_target(summary, args.app_key)
    app_api_args = _app_api_args(args.profile)

    app_state = _start_app_and_wait_for_compute(app_name, app_api_args, env=env)
    if _has_pending_source_deployment(app_state, source_code_path):
        _print_app_url(
            _wait_for_deployment(
                app_name,
                app_api_args,
                source_code_path=source_code_path,
                env=env,
            )
        )
        return 0

    app_state = _deploy_source_code(
        summary,
        app_key=args.app_key,
        app_name=app_name,
        source_code_path=source_code_path,
        app_api_args=app_api_args,
        env=env,
    )
    _require_running_app(app_state)
    _print_app_url(app_state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
