# Real-World UI Stress Test

| Field | Value |
| --- | --- |
| Date (UTC) | 2026-04-04T05:21:48Z |
| Scope | DriftSentinel local Gradio app UI, registry/evidence read path, app performance under large evidence volume |
| Claim status | repo-verified for code, tests, local app behavior; external dataset scale claims source-linked below |

## Dataset Set

The stress fixture used real public dataset identities and source metadata:

| Dataset ID | Source | Scale note |
| --- | --- | --- |
| `nyc_tlc_yellow_tripdata` | NYC Taxi & Limousine Commission trip record data | public trip-record archive with large monthly trip extracts |
| `noaa_ghcnd_daily` | NOAA GHCN-Daily | long-running global daily climate record |
| `sec_financial_statements` | SEC Financial Statement Data Sets | quarterly ZIP archives, including 2025 Q3 at 121.92 MB |
| `common_crawl_monthly` | Common Crawl | large public web corpus |

Source URLs:

- https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
- https://www.ncei.noaa.gov/products/land-based-station/global-historical-climatology-network-daily
- https://www.sec.gov/data-research/sec-markets-data/financial-statement-data-sets
- https://commoncrawl.org/overview

## Fixture and Evidence

- Registry fixture: `output/stress_real_world_20260403/registry.json`
- Evidence fixture: `output/stress_real_world_20260403/evidence`
- Registered datasets: 4
- Valid evidence artifacts generated: 3,780
- Intentionally malformed artifacts generated: 24
- Total files exercised by the UI: 3,804

Measured local helper timings against the 3,804-file fixture:

| Operation | Measured time |
| --- | --- |
| `load_registry_table()` | 0.0003s |
| `query_evidence()` unfiltered | 0.1721s |
| `query_evidence()` filtered | 0.0121s |
| Full analytics helper pipeline | 0.1940s |

## Issues Found

### 1. Run Status had no default cap for large result sets

- Surface: `app/app.py`
- Symptom: querying a large evidence directory returned every matching row to the browser at once.
- Root cause: `query_evidence()` returned the full filtered row set and the UI rendered the entire payload with no operator-facing cap.
- Fix: added a `Max Results` control with a default of `250` and a truncation notice in the Run Status summary.

### 2. Run Status to Evidence Explorer handoff was not reliable under Gradio's dataframe DOM

- Surface: `app/app.py`
- Symptom: clicking visible table cells did not provide a stable interaction path into Evidence Explorer under the Gradio dataframe wrapper.
- Root cause: the rendered dataframe lives inside Gradio's import/drop wrapper, which intercepts pointer interactions in a way that is not reliable for this read-only workflow.
- Fix: added a `Visible Artifact Filename` picker populated from the displayed results and wired it to open the selected artifact in Evidence Explorer without manual retyping.

## Code Changes

- `app/app.py`
  - added result trimming helpers
  - added `Max Results` dropdown to Run Status
  - added `Visible Artifact Filename` handoff control
  - updated Run Status summary text for truncated result sets
- `tests/test_app.py`
  - added coverage for `max_results`
  - added coverage for visible artifact choice generation
  - made the app-load dependency assertion resilient to component ID shifts
- `app/README.md`
  - documented the large-result cap and artifact picker behavior

## Visual Evidence

- Registry baseline: `output/playwright/registry-baseline.png`
- Run Status before fix: `output/playwright/run-status-3804.png`
- Run Status after fix: `output/playwright/run-status-postfix.png`
- Evidence Explorer after fix: `output/playwright/evidence-explorer-postfix.png`

## Verification

| Check | Result |
| --- | --- |
| `uv run pytest tests/test_app.py tests/test_stress.py -q` | PASS |
| `uv run ruff check .` | PASS |
| `uv run mypy src/driftsentinel tests` | PASS |
| `uv run pytest` | PASS (313 passed) |
| `CATALOG=main make bundle-validate` | BLOCKED by missing Databricks credentials in local auth context |

Bundle validation blocker detail:

```text
default auth: cannot configure default credentials
```

## Residual Notes

- `run_dataset_pipeline()` still uses deterministic demo domain data and tags dataset identity/metadata; it does not yet execute controls against arbitrary external public tables. This stress test therefore verified the app and evidence surfaces with real dataset registrations plus large evidence volume, not raw external-table execution.
