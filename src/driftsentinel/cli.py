"""DriftSentinel CLI — one-step Databricks bootstrap, sync, run, and diagnostics.

Usage::

    uv run driftsentinel databricks connect --catalog adb_dev --dataset-id my_dataset ...
    uv run driftsentinel databricks run --dataset-id my_dataset --wait
    uv run driftsentinel databricks status --catalog adb_dev
    uv run driftsentinel databricks sync --dataset-id my_dataset --registry ./registry.json
    uv run driftsentinel databricks doctor --catalog adb_dev
"""

from __future__ import annotations

import argparse
import sys

from driftsentinel import __version__


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    """Add arguments shared across all databricks subcommands."""
    parser.add_argument("--catalog", required=True, help="Unity Catalog catalog name")
    parser.add_argument("--schema", default="default", help="Unity Catalog schema (default: default)")
    parser.add_argument(
        "--volume-name",
        default="driftsentinel_runtime",
        help="Runtime volume name (default: driftsentinel_runtime)",
    )
    parser.add_argument("--profile", default=None, help="Databricks CLI profile")
    parser.add_argument("--target", default="dev", help="Bundle target (default: dev)")


def _add_dataset_args(parser: argparse.ArgumentParser) -> None:
    """Add dataset-related arguments."""
    parser.add_argument("--dataset-id", required=True, help="Registered dataset ID")


def _add_file_args(parser: argparse.ArgumentParser) -> None:
    """Add file upload arguments."""
    parser.add_argument("--registry", default=None, help="Local path to registry.json")
    parser.add_argument("--drift-policy", default=None, help="Local path to drift policy YAML")
    parser.add_argument("--benchmark-policy", default=None, help="Local path to benchmark policy YAML")
    parser.add_argument("--landing-path", default=None, help="Local directory with landing data files")
    parser.add_argument("--baseline-path", default=None, help="Local directory with baseline data files")


def _add_wait_args(parser: argparse.ArgumentParser) -> None:
    """Add wait/poll arguments."""
    parser.add_argument("--wait", action="store_true", help="Poll the job run to completion")
    parser.add_argument("--timeout", type=int, default=3600, help="Timeout in seconds (default: 3600)")


# ---------------------------------------------------------------------------
# Subcommand handlers
# ---------------------------------------------------------------------------


def _cmd_connect(args: argparse.Namespace) -> int:
    from driftsentinel.databricks.connect import connect

    result = connect(
        catalog=args.catalog,
        schema=args.schema,
        volume_name=args.volume_name,
        dataset_id=args.dataset_id,
        registry=args.registry,
        drift_policy=args.drift_policy,
        benchmark_policy=args.benchmark_policy,
        landing_path=args.landing_path,
        baseline_path=args.baseline_path,
        profile=args.profile,
        target=args.target,
        wait=args.wait,
        timeout_s=args.timeout,
    )
    run_info = result.get("run", {})
    if run_info.get("succeeded") is False:
        return 1
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    from driftsentinel.databricks.connect import run

    result = run(
        catalog=args.catalog,
        schema=args.schema,
        volume_name=args.volume_name,
        dataset_id=args.dataset_id,
        drift_policy=args.drift_policy,
        benchmark_policy=args.benchmark_policy,
        profile=args.profile,
        target=args.target,
        wait=args.wait,
        timeout_s=args.timeout,
    )
    if result.get("succeeded") is False:
        return 1
    return 0


def _cmd_status(args: argparse.Namespace) -> int:
    from driftsentinel.databricks.connect import status

    status(
        catalog=args.catalog,
        schema=args.schema,
        volume_name=args.volume_name,
        profile=args.profile,
        target=args.target,
    )
    return 0


def _cmd_sync(args: argparse.Namespace) -> int:
    from driftsentinel.databricks.connect import sync

    sync(
        catalog=args.catalog,
        schema=args.schema,
        volume_name=args.volume_name,
        dataset_id=args.dataset_id,
        registry=args.registry,
        drift_policy=args.drift_policy,
        benchmark_policy=args.benchmark_policy,
        landing_path=args.landing_path,
        baseline_path=args.baseline_path,
        profile=args.profile,
    )
    return 0


def _cmd_doctor(args: argparse.Namespace) -> int:
    from driftsentinel.databricks.connect import doctor

    checks = doctor(
        catalog=args.catalog,
        schema=args.schema,
        volume_name=args.volume_name,
        profile=args.profile,
        target=args.target,
    )
    for key, val in checks.items():
        if isinstance(val, dict) and val.get("status") == "FAIL":
            return 1
    return 0


# ---------------------------------------------------------------------------
# Parser construction
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser."""
    parser = argparse.ArgumentParser(
        prog="driftsentinel",
        description="DriftSentinel — Enterprise Data Trust CLI",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    top_sub = parser.add_subparsers(dest="group", help="Command group")

    # driftsentinel databricks ...
    db_parser = top_sub.add_parser("databricks", help="Databricks workspace operations")
    db_sub = db_parser.add_subparsers(dest="command", help="Databricks command")

    # connect
    p_connect = db_sub.add_parser("connect", help="One-step bootstrap + upload + run")
    _add_common_args(p_connect)
    _add_dataset_args(p_connect)
    _add_file_args(p_connect)
    _add_wait_args(p_connect)
    p_connect.set_defaults(func=_cmd_connect)

    # run
    p_run = db_sub.add_parser("run", help="Rerun an already-registered dataset")
    _add_common_args(p_run)
    _add_dataset_args(p_run)
    p_run.add_argument(
        "--drift-policy",
        default=None,
        help=(
            "Remote drift policy path override "
            "(defaults to the runtime-volume canonical location uploaded by 'connect')"
        ),
    )
    p_run.add_argument(
        "--benchmark-policy",
        default=None,
        help=(
            "Remote benchmark policy path override "
            "(defaults to the runtime-volume canonical location uploaded by 'connect')"
        ),
    )
    _add_wait_args(p_run)
    p_run.set_defaults(func=_cmd_run)

    # status
    p_status = db_sub.add_parser("status", help="Print app URL, job IDs, and runtime paths")
    _add_common_args(p_status)
    p_status.set_defaults(func=_cmd_status)

    # sync
    p_sync = db_sub.add_parser("sync", help="Upload or refresh files without running")
    _add_common_args(p_sync)
    _add_dataset_args(p_sync)
    _add_file_args(p_sync)
    p_sync.set_defaults(func=_cmd_sync)

    # doctor
    p_doctor = db_sub.add_parser("doctor", help="Verify auth, catalog, bundle, and volume")
    _add_common_args(p_doctor)
    p_doctor.set_defaults(func=_cmd_doctor)

    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if not hasattr(args, "func"):
        parser.print_help()
        return 2

    result: int = args.func(args)
    return result


if __name__ == "__main__":
    sys.exit(main())
