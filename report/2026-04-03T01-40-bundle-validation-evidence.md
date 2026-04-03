# Bundle Validation Evidence — 2026-04-03T01:40 UTC

## Context

Prior to this session, every Notion sync record noted "bundle validation not
attempted — no Databricks CLI auth configured." This evidence record closes
that gap by validating the Databricks Asset Bundle against a real Unity Catalog.

## Environment

- **Databricks CLI profile:** `e62-trial`
- **Workspace host:** `https://dbc-9cfc36a7-5883.cloud.databricks.com`
- **Workspace user:** `anthony.johnsonii@etherealogic.ai`
- **Unity Catalog:** `adb_dev` (MANAGED_CATALOG)
- **Catalog owner:** `anthony.johnsonii@etherealogic.ai`
- **Bundle target:** `dev`
- **Bundle path:** `/Workspace/Users/anthony.johnsonii@etherealogic.ai/.bundle/driftsentinel/dev`

## Commands Executed

### 1. Catalog Check

```
make bundle-catalog-check CATALOG=adb_dev PROFILE=e62-trial
```

**Result:** Catalog `adb_dev` confirmed as MANAGED_CATALOG with predictive
optimization enabled. Owner matches workspace user.

### 2. Bundle Validate

```
make bundle-validate CATALOG=adb_dev PROFILE=e62-trial
```

**Result:** `Validation OK!`

- Bundle name: `driftsentinel`
- Target: `dev`
- All resource definitions, job configs, and pipeline declarations passed
  schema validation against the Databricks Asset Bundle specification.

## Classification

- **repo-verified:** Bundle validation command executed locally with output
  captured.
- **Scope note:** `bundle validate` confirms schema correctness and workspace
  targeting. It does **not** constitute deployment proof or runtime verification.
  A successful `bundle deploy --target dev` followed by job execution would be
  needed for deployment evidence.

## HEAD at validation time

- **Commit:** `f1664e3` on main
- **Tests:** 296 passed (15 files)
- **Lint:** pass | **Typecheck:** pass
