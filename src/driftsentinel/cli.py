"""DriftSentinel CLI — one-step Databricks bootstrap, sync, run, and diagnostics.

Usage::

    uv run driftsentinel databricks connect --catalog adb_dev --dataset-id my_dataset ...
    uv run driftsentinel databricks run --dataset-id my_dataset --wait
    uv run driftsentinel databricks status --catalog adb_dev
    uv run driftsentinel databricks sync --dataset-id my_dataset --registry ./registry.json
    uv run driftsentinel databricks doctor --catalog adb_dev
    uv run driftsentinel registry add --contract path/to/dataset_contract.yml
    uv run driftsentinel registry list
    uv run driftsentinel registry remove --dataset-id my_dataset --contract-version 1.0.0
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from driftsentinel import __version__

DEFAULT_REGISTRY_PATH = "data/registry.json"


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


def _load_or_new_registry(registry_path: Path) -> "DatasetRegistry":  # type: ignore[name-defined]  # noqa: F821
    from driftsentinel.config.loader import DatasetRegistry

    if registry_path.is_file():
        return DatasetRegistry.load(registry_path)
    return DatasetRegistry()


def _cmd_registry_add(args: argparse.Namespace) -> int:
    from driftsentinel.config.loader import (
        RegistryError,
        _dataset_identity,
        load_dataset_contract,
    )

    contract_path = Path(args.contract)
    registry_path = Path(args.registry)

    contract = load_dataset_contract(
        contract_path,
        catalog=args.catalog,
        schema=args.schema,
        volume_name=args.volume_name,
    )
    dataset_id, contract_version = _dataset_identity(contract)

    registry = _load_or_new_registry(registry_path)

    if registry.contains(dataset_id, contract_version):
        if not args.force:
            print(
                f"error: dataset '{dataset_id}' version '{contract_version}' is already "
                f"registered in {registry_path}. Pass --force to replace it.",
                file=sys.stderr,
            )
            return 1
        registry.remove(dataset_id, contract_version)

    try:
        registry.register(contract)
    except RegistryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    saved_path = registry.save(registry_path)
    print(f"registered {dataset_id}@{contract_version} in {saved_path}")
    return 0


def _cmd_registry_list(args: argparse.Namespace) -> int:
    from driftsentinel.config.loader import DatasetRegistry, RegistryError

    registry_path = Path(args.registry)
    if not registry_path.is_file():
        print(f"error: registry file not found: {registry_path}", file=sys.stderr)
        return 1

    try:
        registry = DatasetRegistry.load(registry_path)
    except RegistryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    entries = registry.list_datasets()
    if not entries:
        print(f"(empty registry: {registry_path})")
        return 0

    width = max(len("DATASET_ID"), max(len(e["dataset_id"]) for e in entries))
    print(f"{'DATASET_ID'.ljust(width)}  CONTRACT_VERSION")
    for entry in entries:
        print(f"{entry['dataset_id'].ljust(width)}  {entry['contract_version']}")
    return 0


def _cmd_registry_remove(args: argparse.Namespace) -> int:
    from driftsentinel.config.loader import DatasetRegistry, RegistryError

    registry_path = Path(args.registry)
    if not registry_path.is_file():
        print(f"error: registry file not found: {registry_path}", file=sys.stderr)
        return 1

    registry = DatasetRegistry.load(registry_path)
    try:
        registry.remove(args.dataset_id, args.contract_version)
    except RegistryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    registry.save(registry_path)
    print(f"removed {args.dataset_id}@{args.contract_version} from {registry_path}")
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

    # driftsentinel registry ...
    reg_parser = top_sub.add_parser("registry", help="Manage the dataset registry JSON")
    _add_registry_subparsers(reg_parser)

    return parser


def _add_registry_subparsers(reg_parser: argparse.ArgumentParser) -> None:
    """Attach add/list/remove subcommands to the registry parser."""
    reg_sub = reg_parser.add_subparsers(dest="command", help="Registry command")

    p_reg_add = reg_sub.add_parser(
        "add",
        help="Register a dataset contract in the registry JSON",
    )
    p_reg_add.add_argument(
        "--contract",
        required=True,
        help="Path to a dataset contract YAML",
    )
    p_reg_add.add_argument(
        "--registry",
        default=DEFAULT_REGISTRY_PATH,
        help=f"Path to registry.json (default: {DEFAULT_REGISTRY_PATH})",
    )
    p_reg_add.add_argument(
        "--catalog",
        default=None,
        help="Substitute ${CATALOG} in the contract before registering",
    )
    p_reg_add.add_argument(
        "--schema",
        default=None,
        help="Substitute ${SCHEMA} in the contract before registering",
    )
    p_reg_add.add_argument(
        "--volume-name",
        default=None,
        help="Substitute ${VOLUME} in the contract before registering",
    )
    p_reg_add.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing (dataset_id, contract_version) entry",
    )
    p_reg_add.set_defaults(func=_cmd_registry_add)

    p_reg_list = reg_sub.add_parser(
        "list",
        help="List datasets registered in the registry JSON",
    )
    p_reg_list.add_argument(
        "--registry",
        default=DEFAULT_REGISTRY_PATH,
        help=f"Path to registry.json (default: {DEFAULT_REGISTRY_PATH})",
    )
    p_reg_list.set_defaults(func=_cmd_registry_list)

    p_reg_remove = reg_sub.add_parser(
        "remove",
        help="Remove a dataset contract entry from the registry JSON",
    )
    p_reg_remove.add_argument("--dataset-id", required=True, help="Registered dataset ID")
    p_reg_remove.add_argument(
        "--contract-version",
        required=True,
        help="Registered contract version (e.g. 1.0.0)",
    )
    p_reg_remove.add_argument(
        "--registry",
        default=DEFAULT_REGISTRY_PATH,
        help=f"Path to registry.json (default: {DEFAULT_REGISTRY_PATH})",
    )
    p_reg_remove.set_defaults(func=_cmd_registry_remove)


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
