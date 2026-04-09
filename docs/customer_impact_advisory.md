# Customer Impact Advisory

Published: April 9, 2026

Users who ran DriftSentinel `0.4.1` or earlier before upgrading to `0.4.2`
should treat prior bundle-driven control results as `unverified` until rerun.

## Affected Users

This advisory applies to users who used any of the following before April 9,
2026:

- Databricks bundle jobs from DriftSentinel `0.4.1` or earlier
- the Databricks App review surface from DriftSentinel `0.4.1` or earlier
- drift policies that declared per-column methods such as `method: wasserstein`

## What Was Wrong

Before `0.4.2`, some shipped runtime surfaces could present outputs that did
not fully reflect the intended real-workload execution path:

- bundle jobs could fall back to demo or synthetic execution paths instead of
  failing closed when required dataset-backed inputs were missing
- drift policies declaring `wasserstein` were not executed with that method in
  runtime
- the Databricks App could read cluster-local `/tmp` state instead of the
  shared runtime evidence location

## Worst-Case Impact

In the worst case, users could receive outputs that appeared valid but did not
represent:

- their actual registered workload
- their declared drift method
- the correct shared evidence state for review

This could lead to false PASS decisions, missed drift, or incorrect operational
or governance signoff. We found no evidence of source-data corruption. The
primary risk was incorrect or misleading evaluation output.

## Fixed In

- DriftSentinel `0.4.2`, released April 9, 2026

## Required Customer Action

Users who ran `0.4.1` or earlier should:

1. Upgrade to `0.4.2` or later.
2. Redeploy the Databricks bundle and app surfaces.
3. Rerun any intake, drift, or pipeline jobs that informed business,
   governance, publication, or release decisions.
4. Treat earlier affected outputs as `unverified` unless they were
   independently confirmed against real dataset-backed execution and shared
   evidence artifacts.

## Public References

- Release with the fixes: `v0.4.2`
- Strict real-workload validation record:
  `report/2026-04-09T16-14-00Z-strict-real-workload-validation.md`
