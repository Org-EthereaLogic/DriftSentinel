#!/usr/bin/env bash
# scripts/run_nyc_taxi_demo.sh
#
# One-shot replay of the NYC TLC Yellow Taxi DriftSentinel demo:
#   1. Download Jan + Feb 2024 parquet from the public CloudFront mirror.
#   2. Deduplicate each month with the 8-column composite business_key.
#   3. Upload to the runtime UC volume (baseline + landing).
#   4. Register the dataset in a JSON registry.
#   5. Run `driftsentinel databricks connect --wait`.
#   6. Print the final verdict.
#
# Usage:
#   scripts/run_nyc_taxi_demo.sh --catalog <catalog> [--profile <profile>] \
#       [--schema <schema>] [--volume-name <volume>] \
#       [--baseline-month YYYY-MM] [--landing-month YYYY-MM] \
#       [--work-dir <dir>] [--registry <path>]
#
# Defaults:
#   schema=default, volume=driftsentinel_runtime,
#   baseline=2024-01, landing=2024-02,
#   work-dir=/tmp/nyc_taxi_demo, registry=<work-dir>/registry.json
#
# Prerequisites: databricks CLI authenticated, OpenTofu/terraform on PATH
# (see scripts/databricks_tf_env.sh and docs/deployment_guide.md).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXAMPLE_DIR="${REPO_ROOT}/examples/nyc_yellow_taxi"

CATALOG=""
PROFILE=""
SCHEMA="default"
VOLUME_NAME="driftsentinel_runtime"
BASELINE_MONTH="2024-01"
LANDING_MONTH="2024-02"
WORK_DIR="/tmp/nyc_taxi_demo"
REGISTRY=""

usage() {
  sed -n '2,22p' "${BASH_SOURCE[0]}"
  exit "${1:-0}"
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --catalog) CATALOG="$2"; shift 2 ;;
    --profile) PROFILE="$2"; shift 2 ;;
    --schema) SCHEMA="$2"; shift 2 ;;
    --volume-name) VOLUME_NAME="$2"; shift 2 ;;
    --baseline-month) BASELINE_MONTH="$2"; shift 2 ;;
    --landing-month) LANDING_MONTH="$2"; shift 2 ;;
    --work-dir) WORK_DIR="$2"; shift 2 ;;
    --registry) REGISTRY="$2"; shift 2 ;;
    -h|--help) usage 0 ;;
    *) echo "error: unknown argument: $1" >&2; usage 2 ;;
  esac
done

if [ -z "${CATALOG}" ]; then
  echo "error: --catalog is required" >&2
  usage 2
fi

REGISTRY="${REGISTRY:-${WORK_DIR}/registry.json}"
BASELINE_DIR="${WORK_DIR}/baseline"
LANDING_DIR="${WORK_DIR}/landing"

mkdir -p "${BASELINE_DIR}" "${LANDING_DIR}"

PROFILE_ARG=()
if [ -n "${PROFILE}" ]; then
  PROFILE_ARG=(--profile "${PROFILE}")
fi

# ---------------------------------------------------------------------------
# 1. Download
# ---------------------------------------------------------------------------

NYC_BASE_URL="https://d37ci6vzurychx.cloudfront.net/trip-data"

download_month() {
  local month="$1"
  local dest="$2"
  local url="${NYC_BASE_URL}/yellow_tripdata_${month}.parquet"
  local target="${dest}/yellow_tripdata_${month}.parquet"

  if [ -s "${target}" ]; then
    echo "[1/5] cached: ${target}"
    return 0
  fi
  echo "[1/5] downloading ${url}"
  curl -fL --retry 3 --retry-delay 2 -o "${target}.partial" "${url}"
  mv "${target}.partial" "${target}"
}

download_month "${BASELINE_MONTH}" "${BASELINE_DIR}"
download_month "${LANDING_MONTH}" "${LANDING_DIR}"

# ---------------------------------------------------------------------------
# 2. Dedupe via 8-col composite business_key
# ---------------------------------------------------------------------------

dedupe_month() {
  local month="$1"
  local dir="$2"
  local raw="${dir}/yellow_tripdata_${month}.parquet"
  local marker="${dir}/.deduped_${month}"

  if [ -f "${marker}" ]; then
    echo "[2/5] already deduplicated: ${raw}"
    return 0
  fi

  echo "[2/5] deduplicating ${raw} on 8-col composite key"
  uv run python - "${raw}" <<'PY'
import sys
from pathlib import Path

import pyarrow.parquet as pq

path = Path(sys.argv[1])
table = pq.read_table(path)
df = table.to_pandas()
key_cols = [
    "VendorID",
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "PULocationID",
    "DOLocationID",
    "fare_amount",
    "total_amount",
    "trip_distance",
]
before = len(df)
df = df.drop_duplicates(subset=key_cols, keep="first")
after = len(df)
df.to_parquet(path, index=False)
print(f"  rows: {before} -> {after} (-{before - after})")
PY
  : > "${marker}"
}

dedupe_month "${BASELINE_MONTH}" "${BASELINE_DIR}"
dedupe_month "${LANDING_MONTH}" "${LANDING_DIR}"

# ---------------------------------------------------------------------------
# 3. Register dataset (and 4. upload via `databricks connect`)
# ---------------------------------------------------------------------------

echo "[3/5] registering nyc_yellow_taxi in ${REGISTRY}"
uv run driftsentinel registry add \
  --contract "${EXAMPLE_DIR}/dataset_contract.yml" \
  --registry "${REGISTRY}" \
  --catalog "${CATALOG}" \
  --schema "${SCHEMA}" \
  --volume-name "${VOLUME_NAME}" \
  --force

# ---------------------------------------------------------------------------
# 4. Run the full pipeline (uploads files, deploys bundle, runs the job)
# ---------------------------------------------------------------------------

echo "[4/5] driftsentinel databricks connect --wait"
# shellcheck disable=SC1091
. "${REPO_ROOT}/scripts/databricks_tf_env.sh"
uv run driftsentinel databricks connect \
  --catalog "${CATALOG}" \
  --schema "${SCHEMA}" \
  --volume-name "${VOLUME_NAME}" \
  --dataset-id "nyc_yellow_taxi" \
  --registry "${REGISTRY}" \
  --drift-policy "${EXAMPLE_DIR}/drift_policy.yml" \
  --benchmark-policy "${EXAMPLE_DIR}/benchmark_policy.yml" \
  --landing-path "${LANDING_DIR}" \
  --baseline-path "${BASELINE_DIR}" \
  "${PROFILE_ARG[@]}" \
  --wait

# ---------------------------------------------------------------------------
# 5. Print verdict pointer
# ---------------------------------------------------------------------------

echo
echo "[5/5] Run complete. Inspect evidence under:"
echo "  /Volumes/${CATALOG}/${SCHEMA}/${VOLUME_NAME}/evidence/nyc_yellow_taxi/"
echo
echo "From a Databricks notebook or CLI:"
PROFILE_FLAG="${PROFILE:+--profile ${PROFILE}}"
echo "  databricks fs ls /Volumes/${CATALOG}/${SCHEMA}/${VOLUME_NAME}/evidence/nyc_yellow_taxi/ ${PROFILE_FLAG}"
