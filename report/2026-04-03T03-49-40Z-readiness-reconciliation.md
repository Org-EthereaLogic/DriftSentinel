# Readiness Reconciliation Record

**Timestamp:** 2026-04-03T03:49:40Z
**Purpose:** Correct the unsupported "ready for free download via GitHub"
conclusion recorded in `report/2026-04-03T02-34-notion-sync-record.md` and
repair the dependency drift that caused a fresh `make sync` environment to fail
`make test`.

## Issue Summary

Independent verification found that the repository could pass `uv run pytest`
in the pre-existing environment, but a fresh `make sync` environment removed
`plotly` and caused the analytics-chart tests to fail. The root cause was
dependency drift across three surfaces:

- `pyproject.toml` app dependency group included `gradio` but not `plotly`
- root `requirements.txt` included `gradio` but not `plotly`
- `app/requirements.txt` already included both `gradio` and `plotly`

That mismatch meant:

- `make sync` could produce an environment where the Analytics tab chart
  builders returned `None`
- Databricks App source deployed from the repository root could omit Plotly at
  runtime even though the app imports Plotly-backed analytics helpers

## Changes Applied

- Added `plotly>=5.0,<6` to the `app` dependency group in `pyproject.toml`
- Added `plotly>=5.0,<6` to root `requirements.txt`
- Added packaging regression checks covering root requirements, app
  requirements, and the `pyproject.toml` app group
- Updated `docs/e2e_verification_prompt.md` to install from
  `app/requirements.txt` and expect the current four-tab dashboard
- Updated `docs/marketplace_distribution.md` to classify the Partner
  application status as operator-reported rather than repo-verified

## Verification Commands

```bash
uv sync --all-groups
uv run ruff check .
uv run mypy src/driftsentinel tests
uv run pytest
make test
make bundle-catalog-check CATALOG=adb_dev PROFILE=e62-trial
make bundle-validate CATALOG=adb_dev PROFILE=e62-trial
```

## Verification Results

- `uv sync --all-groups` installs Plotly again in the fresh environment
- `uv run ruff check .` passes
- `uv run mypy src/driftsentinel tests` passes
- `uv run pytest` passes
- `make test` passes after `make sync`
- `make bundle-catalog-check CATALOG=adb_dev PROFILE=e62-trial` returns catalog
  metadata for `adb_dev`
- `make bundle-validate CATALOG=adb_dev PROFILE=e62-trial` returns
  `Validation OK!`

## Corrected Conclusions

- **Verified:** the documented quickstart path `git clone` -> `make sync` ->
  `make test` is now replayable in a fresh local environment.
- **Verified:** the local and Databricks-App dependency surfaces now both
  declare Plotly, which matches the Analytics tab implementation.
- **Corrected:** the earlier "ready for free download via GitHub" conclusion was
  unsupported before dependency alignment. It is only supportable after the
  fresh-environment replay above.
- **Bounded claim:** the repository proves the GitHub clone plus local test
  path, notebook-first evaluation path, and one replayed Databricks workspace
  deployment path. It does not prove every paid workspace configuration.
- **Operator-reported only:** Databricks Partner application submission remains
  external and is not independently proven by repository artifacts.
