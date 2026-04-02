# Bundle Proof Reconciliation Record

**Timestamp:** 2026-04-02T07:36:36Z
**Purpose:** Correct the unsupported catalog and deployment conclusions in
`report/2026-04-02T07-17-bundle-validation-evidence.md` without rewriting that
earlier artifact.

## Reconciled Findings

- `e62_trial_catalog` is **not** a valid catalog in the `e62-trial` workspace.
- `adb_dev` **is** a valid Unity Catalog catalog in that workspace.
- `databricks bundle validate` can return `Validation OK!` even when the
  supplied catalog name does not exist, so validation alone does not prove
  catalog existence.
- The stronger deployment path is now replayed from the current repository:
  catalog check, bundle validate, bundle deploy, benchmark job run, and bundle
  destroy all succeeded against `adb_dev`.

## Commands Executed

```bash
env -i HOME="$HOME" PATH="$PATH" SHELL="$SHELL" TMPDIR="${TMPDIR:-/tmp}" \
  databricks catalogs get e62_trial_catalog -p e62-trial -o json

env -i HOME="$HOME" PATH="$PATH" SHELL="$SHELL" TMPDIR="${TMPDIR:-/tmp}" \
  databricks catalogs get adb_dev -p e62-trial -o json

env -i HOME="$HOME" PATH="$PATH" SHELL="$SHELL" TMPDIR="${TMPDIR:-/tmp}" \
  databricks bundle validate -p e62-trial --target dev --var="catalog=zz_does_not_exist_20260402"

env -i HOME="$HOME" PATH="$PATH" SHELL="$SHELL" TMPDIR="${TMPDIR:-/tmp}" \
  databricks bundle validate -p e62-trial --target dev --var="catalog=adb_dev"

env -i HOME="$HOME" PATH="$PATH" SHELL="$SHELL" TMPDIR="${TMPDIR:-/tmp}" \
  databricks bundle deploy -p e62-trial --target dev --var="catalog=adb_dev" --auto-approve

env -i HOME="$HOME" PATH="$PATH" SHELL="$SHELL" TMPDIR="${TMPDIR:-/tmp}" \
  databricks bundle run benchmark_job -p e62-trial --target dev --var="catalog=adb_dev"

env -i HOME="$HOME" PATH="$PATH" SHELL="$SHELL" TMPDIR="${TMPDIR:-/tmp}" \
  databricks jobs get-run 102152955457777 -p e62-trial -o json

env -i HOME="$HOME" PATH="$PATH" SHELL="$SHELL" TMPDIR="${TMPDIR:-/tmp}" \
  databricks bundle destroy -p e62-trial --target dev --var="catalog=adb_dev" --auto-approve
```

## Observed Results

### Invalid Catalog Check

```text
Error: Catalog 'e62_trial_catalog' does not exist.
```

### Valid Catalog Check

`databricks catalogs get adb_dev -p e62-trial -o json` returned metadata with:

- `"name":"adb_dev"`
- `"catalog_type":"MANAGED_CATALOG"`
- `"owner":"anthony.johnsonii@etherealogic.ai"`

### Validation Behavior

Both commands below returned `Validation OK!`:

- `databricks bundle validate -p e62-trial --target dev --var="catalog=zz_does_not_exist_20260402"`
- `databricks bundle validate -p e62-trial --target dev --var="catalog=adb_dev"`

That proves the current bundle validation step checks bundle/auth/resource
resolution, but not remote catalog existence.

### Deployment Proof

```text
Deploying resources...
Updating deployment state...
Deployment complete!
```

### Benchmark Run Proof

```text
Run URL: https://dbc-9cfc36a7-5883.cloud.databricks.com/?o=7474657966305346#job/1108483589772914/run/102152955457777
2026-04-02 00:29:46 "[dev anthony_johnsonii] driftsentinel_benchmark" TERMINATED SUCCESS
```

`databricks jobs get-run 102152955457777 -p e62-trial -o json` confirmed:

- `"job_id":1108483589772914`
- `"run_id":102152955457777`
- `"result_state":"SUCCESS"`
- notebook parameter `"catalog":"adb_dev"`

### Cleanup Proof

```text
Deleting files...
Destroy complete!
```

Post-destroy verification:

- `databricks jobs get 1108483589772914 -p e62-trial -o json` returned
  `Error: Job 1108483589772914 does not exist.`
- `databricks workspace get-status /Workspace/Users/anthony.johnsonii@etherealogic.ai/.bundle/driftsentinel/dev -p e62-trial -o json`
  returned `Error: Path (...) doesn't exist.`

## Corrected Conclusions

- **Verified:** profile `e62-trial` authenticates successfully against
  `dbc-9cfc36a7-5883.cloud.databricks.com`.
- **Verified:** `adb_dev` exists and is a valid Unity Catalog input for the
  current DriftSentinel bundle workflow.
- **Verified:** the current repository can validate, deploy, run
  `benchmark_job`, and destroy the dev bundle resources against `adb_dev`.
- **Superseded from the earlier artifact:** the claim that
  `e62_trial_catalog` exists, and the claim that `bundle validate` alone proved
  "no catalog errors" or a complete deployment foundation.
