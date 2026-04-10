"""Orchestration layer for DriftSentinel Databricks CLI commands.

Implements: connect, run, status, sync, doctor.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from driftsentinel.databricks import bundle, client, files, jobs
from driftsentinel.runtime_paths import (
    DEFAULT_RUNTIME_VOLUME_NAME,
    runtime_evidence_dir,
    runtime_registry_path,
    runtime_volume_root,
)

APP_NAME = "driftsentinel"
APP_KEY = "driftsentinel_app"
PIPELINE_JOB_KEY = "dataset_pipeline_job"


def _print(msg: str) -> None:
    print(msg, file=sys.stderr)


def _build_job_parameters(
    *,
    catalog: str,
    schema: str,
    volume_name: str,
    dataset_id: str,
    remote_paths: dict[str, str],
) -> dict[str, str]:
    """Build the job parameters dict from remote paths."""
    params: dict[str, str] = {
        "dataset_id": dataset_id,
        "registry_path": remote_paths.get(
            "registry",
            runtime_registry_path(catalog, schema, volume_name=volume_name),
        ),
        "evidence_dir": remote_paths.get(
            "evidence",
            runtime_evidence_dir(catalog, schema, volume_name=volume_name),
        ),
    }
    if "drift_policy" in remote_paths:
        params["drift_policy_path"] = remote_paths["drift_policy"]
    if "benchmark_policy" in remote_paths:
        params["benchmark_policy_path"] = remote_paths["benchmark_policy"]
    return params


# ---------------------------------------------------------------------------
# connect — one-step bootstrap + upload + run
# ---------------------------------------------------------------------------

def connect(
    *,
    catalog: str,
    schema: str = "default",
    volume_name: str = DEFAULT_RUNTIME_VOLUME_NAME,
    dataset_id: str,
    registry: str | Path | None = None,
    drift_policy: str | Path | None = None,
    benchmark_policy: str | Path | None = None,
    landing_path: str | Path | None = None,
    baseline_path: str | Path | None = None,
    profile: str | None = None,
    target: str = "dev",
    wait: bool = False,
    timeout_s: int = 3600,
) -> dict[str, Any]:
    """One-step bootstrap: verify auth, deploy bundle, start app, upload files, run pipeline."""
    result: dict[str, Any] = {}

    # 1. Verify auth
    _print("Verifying Databricks auth...")
    ws = client.get_workspace_client(profile=profile)
    identity = client.resolve_identity(ws)
    _print(f"  Authenticated as {identity.user} on {identity.host}")
    result["identity"] = {"user": identity.user, "host": identity.host}

    # 2. Validate + deploy bundle
    _print("Deploying bundle...")
    bundle.deploy(profile=profile, target=target, catalog=catalog, schema=schema, volume_name=volume_name)

    # 3. Get bundle summary for job IDs
    bsummary = bundle.summary(profile=profile, target=target, catalog=catalog, schema=schema, volume_name=volume_name)
    result["bundle_summary"] = bsummary

    # 4. Start the app
    _print("Starting app...")
    try:
        bundle.app_start(APP_NAME, profile=profile)
    except bundle.BundleError as exc:
        _print(f"  App start note: {exc}")

    # 5. Ensure volume layout + upload files
    _print("Syncing files to runtime volume...")
    remote_paths = files.sync_files(
        ws,
        catalog=catalog,
        schema=schema,
        volume_name=volume_name,
        dataset_id=dataset_id,
        registry_path=registry,
        drift_policy_path=drift_policy,
        benchmark_policy_path=benchmark_policy,
        landing_path=landing_path,
        baseline_path=baseline_path,
    )
    result["remote_paths"] = remote_paths

    # 6. Trigger pipeline job
    job_id = jobs._resolve_job_id(ws, bundle_summary=bsummary, job_key=PIPELINE_JOB_KEY)
    params = _build_job_parameters(
        catalog=catalog,
        schema=schema,
        volume_name=volume_name,
        dataset_id=dataset_id,
        remote_paths=remote_paths,
    )
    _print(f"Triggering dataset pipeline (job {job_id})...")
    result["job_id"] = job_id
    result["job_parameters"] = params

    if wait:
        run_result = jobs.run_and_wait(
            ws,
            job_id=job_id,
            parameters=params,
            timeout_s=timeout_s,
        )
        result["run"] = {
            "run_id": run_result.run_id,
            "state": run_result.state,
            "result_state": run_result.result_state,
            "run_page_url": run_result.run_page_url,
            "succeeded": run_result.succeeded,
            "message": run_result.message,
        }
        _print_run_summary(result, run_result)
    else:
        run_id = jobs.submit_run(ws, job_id=job_id, parameters=params)
        result["run"] = {"run_id": run_id, "state": "SUBMITTED"}
        _print(f"  Run submitted: {run_id} (use --wait to poll to completion)")

    # 7. Print summary
    _print_connect_summary(result, catalog, schema, volume_name, profile)
    return result


def _print_run_summary(result: dict[str, Any], run_result: jobs.RunResult) -> None:
    verdict = "PASS" if run_result.succeeded else "FAIL"
    _print(f"\n  Verdict: {verdict}")
    _print(f"  Run URL: {run_result.run_page_url}")
    if run_result.message:
        _print(f"  Message: {run_result.message}")


def _print_connect_summary(
    result: dict[str, Any],
    catalog: str,
    schema: str,
    volume_name: str,
    profile: str | None,
) -> None:
    _print("\n--- DriftSentinel Connect Summary ---")
    root = runtime_volume_root(catalog, schema, volume_name=volume_name)
    _print(f"  Runtime volume: {root}")
    _print(f"  Evidence dir:   {runtime_evidence_dir(catalog, schema, volume_name=volume_name)}")

    try:
        app_state = bundle.app_get(APP_NAME, profile=profile)
        url = app_state.get("url", "")
        if url:
            _print(f"  App URL:        {url}")
    except bundle.BundleError:
        pass

    run_info = result.get("run", {})
    if run_info.get("run_page_url"):
        _print(f"  Job run URL:    {run_info['run_page_url']}")
    elif run_info.get("run_id"):
        _print(f"  Job run ID:     {run_info['run_id']}")


# ---------------------------------------------------------------------------
# run — rerun an already-registered dataset
# ---------------------------------------------------------------------------

def run(
    *,
    catalog: str,
    schema: str = "default",
    volume_name: str = DEFAULT_RUNTIME_VOLUME_NAME,
    dataset_id: str,
    drift_policy: str | None = None,
    benchmark_policy: str | None = None,
    profile: str | None = None,
    target: str = "dev",
    wait: bool = False,
    timeout_s: int = 3600,
) -> dict[str, Any]:
    """Rerun the dataset pipeline for an already-registered dataset."""
    ws = client.get_workspace_client(profile=profile)
    bsummary = bundle.summary(
        profile=profile, target=target, catalog=catalog,
        schema=schema, volume_name=volume_name,
    )
    job_id = jobs._resolve_job_id(ws, bundle_summary=bsummary, job_key=PIPELINE_JOB_KEY)

    params: dict[str, str] = {
        "dataset_id": dataset_id,
        "registry_path": runtime_registry_path(catalog, schema, volume_name=volume_name),
        "evidence_dir": runtime_evidence_dir(catalog, schema, volume_name=volume_name),
    }
    if drift_policy:
        params["drift_policy_path"] = drift_policy
    if benchmark_policy:
        params["benchmark_policy_path"] = benchmark_policy

    _print(f"Triggering dataset pipeline (job {job_id}) for {dataset_id}...")

    if wait:
        run_result = jobs.run_and_wait(
            ws, job_id=job_id, parameters=params, timeout_s=timeout_s,
        )
        verdict = "PASS" if run_result.succeeded else "FAIL"
        _print(f"  Verdict: {verdict} | Run URL: {run_result.run_page_url}")
        return {
            "run_id": run_result.run_id,
            "state": run_result.state,
            "result_state": run_result.result_state,
            "run_page_url": run_result.run_page_url,
            "succeeded": run_result.succeeded,
        }
    else:
        run_id = jobs.submit_run(ws, job_id=job_id, parameters=params)
        _print(f"  Run submitted: {run_id}")
        return {"run_id": run_id, "state": "SUBMITTED"}


# ---------------------------------------------------------------------------
# status — print app URL, job IDs, latest run state, runtime volume path
# ---------------------------------------------------------------------------

def status(
    *,
    catalog: str,
    schema: str = "default",
    volume_name: str = DEFAULT_RUNTIME_VOLUME_NAME,
    profile: str | None = None,
    target: str = "dev",
) -> dict[str, Any]:
    """Print app URL, job IDs, latest run state, and runtime volume path."""
    result: dict[str, Any] = {}

    root = runtime_volume_root(catalog, schema, volume_name=volume_name)
    result["runtime_volume"] = root
    result["evidence_dir"] = runtime_evidence_dir(catalog, schema, volume_name=volume_name)
    result["registry"] = runtime_registry_path(catalog, schema, volume_name=volume_name)

    try:
        app_state = bundle.app_get(APP_NAME, profile=profile)
        result["app_url"] = app_state.get("url", "")
        result["app_status"] = app_state.get("app_status", {}).get("state", "UNKNOWN")
    except bundle.BundleError as exc:
        result["app_error"] = str(exc)

    try:
        bsummary = bundle.summary(
            profile=profile, target=target, catalog=catalog,
            schema=schema, volume_name=volume_name,
        )
        job_ids: dict[str, str] = {}
        for key, val in bsummary.get("resources", {}).get("jobs", {}).items():
            job_ids[key] = val.get("id", "unknown")
        result["jobs"] = job_ids
    except bundle.BundleError as exc:
        result["bundle_error"] = str(exc)

    print(json.dumps(result, indent=2))
    return result


# ---------------------------------------------------------------------------
# sync — upload or refresh files without running
# ---------------------------------------------------------------------------

def sync(
    *,
    catalog: str,
    schema: str = "default",
    volume_name: str = DEFAULT_RUNTIME_VOLUME_NAME,
    dataset_id: str,
    registry: str | Path | None = None,
    drift_policy: str | Path | None = None,
    benchmark_policy: str | Path | None = None,
    landing_path: str | Path | None = None,
    baseline_path: str | Path | None = None,
    profile: str | None = None,
) -> dict[str, str]:
    """Upload or refresh registry, policy, and dataset files without running."""
    _print("Verifying Databricks auth...")
    ws = client.get_workspace_client(profile=profile)
    identity = client.resolve_identity(ws)
    _print(f"  Authenticated as {identity.user} on {identity.host}")

    _print("Syncing files to runtime volume...")
    remote_paths = files.sync_files(
        ws,
        catalog=catalog,
        schema=schema,
        volume_name=volume_name,
        dataset_id=dataset_id,
        registry_path=registry,
        drift_policy_path=drift_policy,
        benchmark_policy_path=benchmark_policy,
        landing_path=landing_path,
        baseline_path=baseline_path,
    )
    _print("Sync complete.")
    return remote_paths


# ---------------------------------------------------------------------------
# doctor — verify auth, catalog, bundle, volume, resource IDs
# ---------------------------------------------------------------------------

def doctor(
    *,
    catalog: str,
    schema: str = "default",
    volume_name: str = DEFAULT_RUNTIME_VOLUME_NAME,
    profile: str | None = None,
    target: str = "dev",
) -> dict[str, Any]:
    """Verify unified auth, catalog access, bundle state, volume access, and resource IDs."""
    checks: dict[str, Any] = {}

    # Auth
    _print("Checking auth...")
    try:
        ws = client.get_workspace_client(profile=profile)
        identity = client.resolve_identity(ws)
        checks["auth"] = {"status": "OK", "user": identity.user, "host": identity.host}
        _print(f"  Auth: OK ({identity.user})")
    except Exception as exc:
        checks["auth"] = {"status": "FAIL", "error": str(exc)}
        _print(f"  Auth: FAIL ({exc})")
        print(json.dumps(checks, indent=2))
        return checks

    # Catalog access
    _print("Checking catalog access...")
    try:
        ws.catalogs.get(catalog)
        checks["catalog"] = {"status": "OK", "name": catalog}
        _print(f"  Catalog: OK ({catalog})")
    except Exception as exc:
        checks["catalog"] = {"status": "FAIL", "error": str(exc)}
        _print(f"  Catalog: FAIL ({exc})")

    # Bundle validate
    _print("Checking bundle...")
    try:
        bundle.validate(
            profile=profile, target=target, catalog=catalog,
            schema=schema, volume_name=volume_name,
        )
        checks["bundle"] = {"status": "OK"}
        _print("  Bundle: OK")
    except bundle.BundleError as exc:
        checks["bundle"] = {"status": "FAIL", "error": str(exc)}
        _print(f"  Bundle: FAIL ({exc})")

    # Volume access
    _print("Checking runtime volume...")
    root = runtime_volume_root(catalog, schema, volume_name=volume_name)
    try:
        ws.files.get_status(root)
        checks["volume"] = {"status": "OK", "path": root}
        _print(f"  Volume: OK ({root})")
    except Exception as exc:
        checks["volume"] = {"status": "WARN", "path": root, "note": str(exc)}
        _print(f"  Volume: WARN — {exc} (will be created on first deploy)")

    # Job resource IDs
    _print("Checking job resources...")
    try:
        bsummary = bundle.summary(
            profile=profile, target=target, catalog=catalog,
            schema=schema, volume_name=volume_name,
        )
        job_ids: dict[str, str] = {}
        for key, val in bsummary.get("resources", {}).get("jobs", {}).items():
            job_ids[key] = val.get("id", "unknown")
        checks["jobs"] = {"status": "OK", "ids": job_ids}
        _print(f"  Jobs: OK ({len(job_ids)} found)")
    except bundle.BundleError as exc:
        checks["jobs"] = {"status": "FAIL", "error": str(exc)}
        _print(f"  Jobs: FAIL ({exc})")

    print(json.dumps(checks, indent=2))
    return checks
