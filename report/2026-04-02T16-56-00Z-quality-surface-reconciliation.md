# Quality Surface Reconciliation

| Field | Value |
| --- | --- |
| Timestamp (UTC) | 2026-04-02T16:56:00Z |
| Scope | Reconcile Codacy and Codecov CI surfaces with current official documentation and remove unsupported repo assumptions |

## Findings

1. The repository CI used `codecov/codecov-action@v4` with `CODECOV_PROJECT_TOKEN`, while the current official action recommends `@v5` and `CODECOV_TOKEN`.
2. The repository Codacy workflow shape did not document that Codacy client-side upload mode requires enabling `Run analysis on your build server`.
3. The repository did not need to depend on Codacy client-side upload mode to satisfy its pre-implementation quality-control gate. Codacy's default GitHub Action analysis mode is a valid CI quality surface.
4. The README badge text `pending setup` was stale once the repository had a live Codacy dashboard link.

## Resolution Applied

- Upgraded the Codecov GitHub Action to `codecov/codecov-action@v5`
- Configured Codecov auth through `CODECOV_TOKEN`, while preserving fallback to `CODECOV_PROJECT_TOKEN`
- Set `fail_ci_if_error: true` on the Codecov upload step
- Simplified the Codacy job to default analysis mode so it no longer depends on the optional Codacy build-server upload setting
- Updated canonical build/spec documentation to distinguish Codacy default analysis mode from optional client-side upload mode
- Replaced the stale README Codacy `pending setup` badge with a neutral dashboard badge

## External Note

If the project owner later wants Codacy client-side upload results to appear in Codacy dashboards from CI, they must:

1. Reintroduce `upload: true` plus Codacy token auth in the workflow
2. Enable `Run analysis on your build server` in Codacy repository settings

That external setting was not changed as part of this repository reconciliation.
