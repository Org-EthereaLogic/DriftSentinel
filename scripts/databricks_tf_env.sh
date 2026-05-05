#!/bin/sh
# scripts/databricks_tf_env.sh
# Source me. I export DATABRICKS_TF_EXEC_PATH (and DATABRICKS_TF_VERSION
# when unset) so 'databricks bundle ...' bypasses the upstream
# terraform 1.5.5 PGP-expired download path.
#
# Detection precedence (mirrors src/driftsentinel/databricks/tf_env.py):
#   1. Operator-set DATABRICKS_TF_EXEC_PATH wins.
#   2. tofu on PATH -> DATABRICKS_TF_EXEC_PATH=$(command -v tofu),
#      DATABRICKS_TF_VERSION=1.11.6 (only if unset).
#   3. terraform on PATH -> DATABRICKS_TF_EXEC_PATH=$(command -v terraform).
#   4. Otherwise fail with an actionable message recommending
#      'brew install opentofu'.
#
# See specs/DS-PATCH-035_opentofu_auto_detection.md for the upstream
# context (terraform 1.5.5 PGP signature expired in 2025).

if [ -n "${DATABRICKS_TF_EXEC_PATH:-}" ]; then
  return 0 2>/dev/null || exit 0
fi

if command -v tofu >/dev/null 2>&1; then
  DATABRICKS_TF_EXEC_PATH="$(command -v tofu)"
  export DATABRICKS_TF_EXEC_PATH
  if [ -z "${DATABRICKS_TF_VERSION:-}" ]; then
    DATABRICKS_TF_VERSION=1.11.6
    export DATABRICKS_TF_VERSION
  fi
  return 0 2>/dev/null || exit 0
fi

if command -v terraform >/dev/null 2>&1; then
  DATABRICKS_TF_EXEC_PATH="$(command -v terraform)"
  export DATABRICKS_TF_EXEC_PATH
  return 0 2>/dev/null || exit 0
fi

echo "DriftSentinel: neither 'tofu' nor 'terraform' is on PATH and DATABRICKS_TF_EXEC_PATH is unset." >&2
echo "  Install OpenTofu (recommended, wire-compatible drop-in for terraform):" >&2
echo "    brew install opentofu" >&2
echo "  Or set DATABRICKS_TF_EXEC_PATH to an existing terraform-compatible binary." >&2
echo "  See specs/DS-PATCH-035_opentofu_auto_detection.md for the upstream PGP-expired context." >&2
return 1 2>/dev/null || exit 1
