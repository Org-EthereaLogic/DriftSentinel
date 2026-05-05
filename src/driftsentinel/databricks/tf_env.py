"""Resolve DATABRICKS_TF_EXEC_PATH for subprocess invocations of the Databricks CLI.

Works around the upstream terraform 1.5.5 PGP key expiry. Mirrors the
detection precedence in scripts/databricks_tf_env.sh:

    1. Existing DATABRICKS_TF_EXEC_PATH wins (operator override).
    2. ``tofu`` on PATH -> set DATABRICKS_TF_EXEC_PATH and (if unset)
       DATABRICKS_TF_VERSION = OPENTOFU_VERSION_DEFAULT.
    3. ``terraform`` on PATH -> set DATABRICKS_TF_EXEC_PATH only.
    4. Otherwise raise TerraformBinaryMissingError.

See specs/DS-PATCH-035_opentofu_auto_detection.md for the upstream context.
"""

from __future__ import annotations

import os
import shutil
from collections.abc import Mapping

OPENTOFU_VERSION_DEFAULT = "1.11.6"


class TerraformBinaryMissingError(RuntimeError):
    """Raised when no terraform-compatible binary is resolvable."""


def resolve_tf_env(base: Mapping[str, str] | None = None) -> dict[str, str]:
    """Return a copy of ``base`` (or ``os.environ``) with the terraform-binary vars set.

    The input mapping is never mutated. The returned dict can be passed
    directly as the ``env=`` kwarg to :func:`subprocess.run`.
    """
    source: Mapping[str, str] = base if base is not None else os.environ
    env: dict[str, str] = dict(source)

    if env.get("DATABRICKS_TF_EXEC_PATH"):
        return env

    tofu = shutil.which("tofu")
    if tofu:
        env["DATABRICKS_TF_EXEC_PATH"] = tofu
        env.setdefault("DATABRICKS_TF_VERSION", OPENTOFU_VERSION_DEFAULT)
        return env

    terraform = shutil.which("terraform")
    if terraform:
        env["DATABRICKS_TF_EXEC_PATH"] = terraform
        return env

    raise TerraformBinaryMissingError(
        "DriftSentinel: neither 'tofu' nor 'terraform' is on PATH and "
        "DATABRICKS_TF_EXEC_PATH is unset. Install OpenTofu "
        "(recommended): 'brew install opentofu'. Or set "
        "DATABRICKS_TF_EXEC_PATH to an existing terraform-compatible "
        "binary. See specs/DS-PATCH-035_opentofu_auto_detection.md."
    )
