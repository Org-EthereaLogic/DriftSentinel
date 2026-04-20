# Bundle Validation Closure — 2026-04-20T16:17:06Z

Follow-up to `report/2026-04-20T15-52-49Z-notion-sync-record.md`, which
recorded `make bundle-catalog-check` and `make bundle-validate` as
BLOCKED because the Databricks CLI was not authenticated under the
default auth context at sync time. This record closes that residual
risk by re-running both targets against a valid profile.

## Residual Risk Under Investigation

> Residual risk is limited to the Databricks-authenticated validation path.

The v0.5.1 cut had PASS evidence for ruff, mypy, and pytest (416/416),
but not for the Databricks-authenticated surfaces. The sync record
explicitly refused to claim PASS for bundle validation without
replayable evidence, per the repository rule "No PASS claims without
replayable evidence."

## Root Cause of the Original BLOCKED Status

The `databricks` CLI was not invoked with an explicit profile. When
called without `-p/--profile` and with no `DATABRICKS_CONFIG_PROFILE`
env var set, the default auth resolver could not locate credentials
and returned:

```
Unable to authenticate: default auth: cannot configure default
credentials, please check
https://docs.databricks.com/en/dev-tools/auth.html#databricks-client-unified-authentication
```

`~/.databrickscfg` was present and contained a valid `e62-trial`
profile (confirmed via `databricks auth profiles` showing
`e62-trial (Default)  Valid: YES`), but the `[DEFAULT]` section
was empty, so the fallback path had nothing to resolve.

The Makefile targets already support `PROFILE=<profile>`. Supplying
`PROFILE=e62-trial` (the intended profile recorded in the previous
sync evidence) is the correct, non-destructive resolution.

## Evidence

### 1. Auth health check (repo-verified)

```
$ databricks --profile e62-trial current-user me --output json | head
{
  "active": true,
  "emails": [
    { "primary": true, "type": "work",
      "value": "anthony.johnsonii@etherealogic.ai" }
  ],
  ...
}
```

Profile `e62-trial` resolves an authenticated user and responds to UC
reads.

### 2. `make bundle-catalog-check CATALOG=adb_dev PROFILE=e62-trial` — PASS

```
databricks catalogs get "adb_dev" -p e62-trial -o json
{
  "browse_only": false,
  "catalog_type": "MANAGED_CATALOG",
  "comment": "ADB MVP development environment for Bronze/Silver/Gold demo",
  "full_name": "adb_dev",
  "isolation_mode": "OPEN",
  "metastore_id": "1028ccdc-a4f5-4a1f-9421-198861b234dd",
  "name": "adb_dev",
  "owner": "anthony.johnsonii@etherealogic.ai",
  "securable_type": "CATALOG",
  ...
}
```

Catalog `adb_dev` exists, is owned by the authenticated user, and is
browsable — the precondition the target is designed to prove.

### 3. `make bundle-validate CATALOG=adb_dev PROFILE=e62-trial` — PASS

```
databricks bundle validate -p e62-trial --target dev \
  --var="catalog=${BUNDLE_VAR_catalog:-${CATALOG:?Set CATALOG or BUNDLE_VAR_catalog}}"
Name: driftsentinel
Target: dev
Workspace:
  User: anthony.johnsonii@etherealogic.ai
  Path: /Workspace/Users/anthony.johnsonii@etherealogic.ai/.bundle/driftsentinel/dev

Validation OK!
```

Per repository sync policy:

> Do not treat `bundle validate` alone as deployment proof.

This record makes the narrower claim only: **the bundle definition
passes validation against the `dev` target with `catalog=adb_dev`
under profile `e62-trial`.** It does not claim deployment, job
execution, or a live run.

## Residual Risk After This Closure

- **Deployment path:** `bundle deploy` and downstream job runs were
  not exercised in this session and remain unclaimed.
- **Non-default profiles and catalogs:** validated only against
  `e62-trial` / `adb_dev`. Other environments must be validated
  independently before claiming parity.
- **CI hermeticity:** GitHub Actions does not have Databricks auth,
  so the CI matrix continues to rely on mocks (see commit `872c049`
  for `bundle.app_get`). This is intentional and not a regression.

## Evidence Classification

| Claim | Class |
|-------|-------|
| `e62-trial` profile is valid and resolves a user | `repo-verified` (CLI output observed) |
| `adb_dev` catalog exists and is managed | `repo-verified` (CLI output observed) |
| `make bundle-catalog-check CATALOG=adb_dev PROFILE=e62-trial` PASS | `repo-verified` |
| `make bundle-validate CATALOG=adb_dev PROFILE=e62-trial` PASS | `repo-verified` |
| Deployment / job-run parity | **unclaimed** — outside this record's scope |
