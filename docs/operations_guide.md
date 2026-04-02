# DriftSentinel Operations Guide

## Daily Operations

1. Review the operational handoff summary after each pipeline run.
2. Check quarantine counts — investigate any rows that failed intake.
3. Check drift gate verdicts — verify that Gold publication was allowed or
   blocked with explicit reasons.
4. If a benchmark run was requested, review the evidence bundle for detection
   rates and gate verdicts.

## Troubleshooting

- **Intake quarantine spike**: Check source system for schema drift, duplicate
  batches, or null required fields.
- **Drift gate FAIL**: Compare the current load against the stored baseline.
  Determine whether the distribution shift is a real business change or a
  source failure.
- **Bundle deploy failure**: Run `databricks bundle validate` locally to
  identify configuration issues.

## Evidence Review

Evidence artifacts are written to append-only surfaces. Use
`06_review_evidence.py` to inspect the latest run.

## Updating Policies

- Dataset contracts: edit `templates/dataset_contract.yml`
- Drift policies: edit `templates/drift_policy.yml`
- Benchmark policies: edit `templates/benchmark_policy.yml`
