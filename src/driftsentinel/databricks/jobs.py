"""Submit, poll, and inspect Databricks job runs."""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RunResult:
    """Outcome of a completed job run."""

    run_id: int
    state: str
    result_state: str
    run_page_url: str
    message: str = ""
    tasks: list[dict[str, Any]] = field(default_factory=list)

    @property
    def succeeded(self) -> bool:
        return self.result_state == "SUCCESS"


class JobRunError(RuntimeError):
    """Raised when a job run fails or times out."""


def _resolve_job_id(
    client: Any,
    *,
    bundle_summary: dict[str, Any] | None = None,
    job_key: str = "dataset_pipeline_job",
    job_id: int | None = None,
) -> int:
    """Resolve a job ID from a bundle summary or explicit value."""
    if job_id is not None:
        return job_id
    if bundle_summary:
        jobs = bundle_summary.get("resources", {}).get("jobs", {})
        if job_key in jobs:
            return int(jobs[job_key]["id"])
    raise ValueError(
        f"Cannot resolve job ID for '{job_key}'. "
        "Provide --job-id or ensure the bundle is deployed."
    )


def submit_run(
    client: Any,
    *,
    job_id: int,
    parameters: dict[str, str],
) -> int:
    """Submit a ``run_now`` request and return the ``run_id``."""
    response = client.jobs.run_now(job_id=job_id, job_parameters=parameters)
    run_id: int = response.run_id
    print(f"  Submitted run {run_id} for job {job_id}", file=sys.stderr)
    return run_id


def poll_run(
    client: Any,
    run_id: int,
    *,
    poll_interval_s: int = 10,
    timeout_s: int = 3600,
) -> RunResult:
    """Poll a run until it reaches a terminal state or times out."""
    deadline = time.time() + timeout_s
    terminal = {"TERMINATED", "SKIPPED", "INTERNAL_ERROR"}

    while time.time() < deadline:
        run = client.jobs.get_run(run_id)
        state = run.state
        life_cycle = state.life_cycle_state if state else "UNKNOWN"

        if life_cycle in terminal:
            result_state = state.result_state.value if state and state.result_state else "UNKNOWN"
            message = state.state_message if state and state.state_message else ""
            tasks_info: list[dict[str, Any]] = []
            if hasattr(run, "tasks") and run.tasks:
                for t in run.tasks:
                    tasks_info.append({
                        "task_key": t.task_key,
                        "state": t.state.result_state.value if t.state and t.state.result_state else "UNKNOWN",
                    })
            return RunResult(
                run_id=run_id,
                state=life_cycle,
                result_state=result_state,
                run_page_url=run.run_page_url or "",
                message=message,
                tasks=tasks_info,
            )

        print(
            f"  Run {run_id}: {life_cycle} ...",
            file=sys.stderr,
        )
        time.sleep(poll_interval_s)

    raise JobRunError(f"Run {run_id} timed out after {timeout_s}s")


def run_and_wait(
    client: Any,
    *,
    job_id: int,
    parameters: dict[str, str],
    poll_interval_s: int = 10,
    timeout_s: int = 3600,
) -> RunResult:
    """Submit a run and poll to completion."""
    run_id = submit_run(client, job_id=job_id, parameters=parameters)
    return poll_run(client, run_id, poll_interval_s=poll_interval_s, timeout_s=timeout_s)
