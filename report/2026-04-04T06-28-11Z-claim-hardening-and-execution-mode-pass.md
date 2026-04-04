# Claim Hardening and Execution-Mode Accuracy Pass

Date: 2026-04-04T06:28:11Z
Repository: `/Users/etherealogic-2/Dev/Databricks/DriftSentinel`

## Issue

After the dataset-backed runtime remediation, two evidence-integrity risks
remained:

- older artifacts without explicit execution-mode metadata were visually mixed
  with corrected artifacts in the app
- one operator verification prompt still instructed users to write demo drift
  evidence under a registered dataset filename

Neither issue changed the runtime's corrected execution path, but both weakened
claim clarity for operators reviewing artifacts or following the verification
guide.

## Remediation

Implemented changes:

- Surfaced `execution_mode` explicitly in evidence listing and app views, with
  missing metadata classified as `legacy_or_unknown`.
- Added app filtering and summaries that distinguish dataset-backed,
  reference-sample, synthetic, demo, and legacy/unknown artifacts.
- Rewrote the Day 3 verification flow in
  `docs/e2e_verification_prompt.md` to call `run_dataset_drift()` against the
  registered dataset and trusted baseline instead of writing demo drift output
  under dataset metadata.
- Updated current documentation test counts from `323` to `326`.
- Generalized README exhibit copy that hard-coded sample artifact counts and
  qualified the deployment row so it no longer reads like an unqualified local
  proof when Databricks credentials are absent.
- Tightened the README scope statement to match the implemented supported file
  formats instead of implying an unconstrained arbitrary-schema guarantee.

## Verification

### Static and test checks

- `uv run ruff check .` PASS
- `uv run mypy src/driftsentinel tests` PASS
- `uv run pytest -q` PASS, `326 passed in 5.11s`

### Evidence-mode verification

Measured facts:

- Existing evidence in
  `output/verification_real_pipeline/evidence`
  reported execution modes:
  `dataset_backed`, `reference_data`, and `legacy_or_unknown`.
- A clean rerun in
  `output/verification_real_pipeline_v2/evidence`
  reported only:
  `dataset_backed` and `reference_data`.

Interpretation:

- Post-fix artifacts are now explicitly distinguishable from pre-fix or
  ambiguous artifacts.
- Clean evidence directories generated on the corrected runtime no longer mix
  hidden legacy results into operator review.

## External Blocker

- `CATALOG=main make bundle-validate` remains blocked by local Databricks auth:
  `default auth: cannot configure default credentials`
