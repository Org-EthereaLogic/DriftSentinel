# DS-PATCH-036 — Allow `quarantine_max_ratio` Tolerance in `_validate_dataset_readiness`

| Field | Value |
| --- | --- |
| Tracking issue | [Org-EthereaLogic/DriftSentinel#36](https://github.com/Org-EthereaLogic/DriftSentinel/issues/36) |
| Type | improvement |
| Area | `area:intake`, `area:orchestration` |
| Priority | p2 |
| Status | Planned |
| Owner | lead-software-engineer |
| Methodology precedence | FailLens_Core (explicit, actionable failure), E62 (Databricks runtime path), DS-SDD-001 §Intake / §Orchestration |

## 1. Problem Statement

`src/driftsentinel/orchestration/runner.py:230-256` — `_validate_dataset_readiness` —
raises `ValueError` when `evaluation["quarantined"] > 0`, regardless of the
quarantine *ratio*. Real-world enterprise feeds carry low-rate, business-known
quirks (the demo's NYC TLC iteration recorded ~2.2% true business-key
duplicates over a 3 M row landed parquet). The current zero-tolerance gate
forces operators to one of three undesirable workarounds:

1. Pre-clean parquet files before upload — silently deletes evidence.
2. Engineer wider business keys (the demo widened `business_key` from 4 to 8
   columns) — distorts the contract to satisfy the gate, not the data model.
3. Drop `business_key` entirely — disables a meaningful intake check.

The repository EVIDENCE_LOG (issue #36 §Evidence: NYC TLC iter-1) records
66,651 quarantined rows out of 3,000,000 (2.22%). That is a real-world floor,
not a DriftSentinel defect. The control surface should let the contract
declare the operator-known floor explicitly, gate on that ratio, and persist
the gate decision in evidence.

## 2. Goal

The dataset contract grows an optional `quarantine_max_ratio` knob. The
default is `0.0`, which is identical to the current zero-tolerance behavior
(backward compatible). When set, `_validate_dataset_readiness` raises only
when the *ratio* of quarantined rows exceeds the threshold. The intake
evaluation result and the readiness check both record `quarantine_ratio` and
`tolerance_applied` so audits can see the gate decision.

Schema-level violations (missing required columns, unparseable types, missing
business-key columns, missing batch identifier) continue to fail closed
regardless of tolerance — the ratio applies only to row-level violations
(business-key duplicates, batch-identifier nulls, type-mismatches on present
columns, rescued data, null violations on present non-nullable columns).

## 3. Non-Goals

- Per-violation-type tolerance (e.g. "allow 1% dupes but 0% null
  violations"). A single ratio knob is enough; the issue states this is out
  of scope.
- Changing the existing `quarantined` / `quarantine_ratio` numeric outputs
  of `evaluate_dataframe_contract`. That surface stays; the new behavior is
  additive.
- Loosening the existing schema-validity contract. `schema_valid == False`
  still blocks the run regardless of `quarantine_max_ratio`.
- Adding a runtime knob anywhere other than the dataset contract. Drift
  policy and benchmark policy do not gain this knob; the readiness check is
  contract-scoped.
- Modifying `evaluate_batch` or the row-by-row demo intake surface — the
  ratio knob applies to the dataset-backed `_validate_dataset_readiness`
  path that gates `run_dataset_drift` and `run_dataset_benchmark`.

## 4. Design

### 4.1 Contract surface

The dataset contract YAML grows one optional key under `contract`:

```yaml
contract:
  required_columns:
    - column_name: id
      type: long
      nullable: false
  business_key: [id]
  batch_identifier: batch_id
  quarantine_max_ratio: 0.0  # optional; default 0.0; range [0.0, 1.0]
```

- Type: `float`.
- Default: `0.0` (preserves current zero-tolerance behavior on contracts
  that omit the key).
- Allowed range: `[0.0, 1.0]`. Values outside the range raise `ConfigError`
  at load time (defensive — operators expressing `5%` as `5` get a clean
  failure instead of silently allowing all rows to be quarantined).
- Negative values, non-numeric values, and missing keys all coerce to the
  documented behavior:
  - missing → `0.0` (default).
  - present-but-non-numeric → `ConfigError` from the loader (caught at the
    boundary, not at evaluation time).

Loader validation lives in
`src/driftsentinel/config/loader.py:_validate_dataset_contract`. The
existing `_require_keys` call is unchanged (the new key is optional). A new
helper `_validate_quarantine_max_ratio(contract_section, context)` runs
after the required-keys check and:

- Returns silently when the key is absent.
- Raises `ConfigError` when the value is not a number, not finite, less
  than `0.0`, or greater than `1.0`.

This catches misconfiguration at load time on every public loader entry
point (`load_dataset_contract`, `load_packaged_dataset_contract`, and the
registry `register` path that calls `_validate_dataset_contract`), so
downstream evaluation can trust the value.

### 4.2 Evaluation surface

`src/driftsentinel/intake/contracts.py:evaluate_dataframe_contract` already
records `quarantine_ratio`. No change is required there — the evaluation is
*pure measurement*. The tolerance decision is a downstream gate; conflating
it into the evaluator would muddy the measured-fact-vs-interpretation
boundary that AGENTS.md §Standard Workflow calls out.

### 4.3 Gate surface — `_validate_dataset_readiness`

`src/driftsentinel/orchestration/runner.py:_validate_dataset_readiness`
becomes the single decision point:

```python
def _validate_dataset_readiness(
    contract: dict[str, Any],
    frame: pd.DataFrame,
    *,
    dataset_label: str,
) -> dict[str, Any]:
    evaluation = evaluate_dataframe_contract(frame, contract)
    contract_section = contract.get("contract", {})
    threshold = float(contract_section.get("quarantine_max_ratio", 0.0) or 0.0)
    quarantine_ratio = float(evaluation.get("quarantine_ratio", 0.0))

    schema_invalid = not evaluation["schema_valid"]
    over_threshold = evaluation["quarantined"] > 0 and quarantine_ratio > threshold
    tolerance_applied = (
        threshold > 0.0
        and evaluation["quarantined"] > 0
        and not over_threshold
        and not schema_invalid
    )

    evaluation["quarantine_max_ratio"] = threshold
    evaluation["tolerance_applied"] = tolerance_applied

    if schema_invalid or over_threshold:
        # existing error-message construction, augmented with the threshold
        # and the measured ratio when over_threshold.
        ...
        raise ValueError(...)

    return evaluation
```

Error-message construction stays as it is today, plus two augmentations:

- When the failure is `over_threshold` (not schema), append
  `quarantine_ratio={ratio:.4f}` and `quarantine_max_ratio={threshold:.4f}`
  to the details list so the operator immediately sees how far over they
  are.
- When the failure is schema-invalid, the existing message is preserved
  unchanged. The threshold is irrelevant in that branch by design.

The function still returns the evaluation dict on the pass path. Callers
(`run_dataset_drift`, `run_dataset_benchmark`) do not change — they ignore
the return value today, and after this patch they still ignore it. The
`tolerance_applied` and `quarantine_max_ratio` fields land in evidence via
the upstream evaluation dict, which is already merged into the intake
payload by `run_dataset_intake` (see §4.4).

### 4.4 Evidence surface

`run_dataset_intake` writes the full evaluation dict to evidence today
(`payload = {**result, "overall_verdict": ..., ...}`). The two new fields
appear in the intake artifact automatically:

- `quarantine_max_ratio`: float, the threshold that was active for the run.
- `tolerance_applied`: bool, true iff quarantined rows existed and were
  tolerated by the ratio gate.
- `quarantine_ratio`: float, already present, no change.

`run_dataset_intake` does not call `_validate_dataset_readiness`; it calls
`evaluate_dataframe_contract` directly and computes its own
`PASS`/`FAIL` verdict. To keep the evidence consistent, that verdict logic
also adopts the threshold:

```python
result = evaluate_dataframe_contract(current.frame, contract)
contract_section = contract.get("contract", {})
threshold = float(contract_section.get("quarantine_max_ratio", 0.0) or 0.0)
ratio = float(result.get("quarantine_ratio", 0.0))
schema_invalid = not result["schema_valid"]
over_threshold = result["quarantined"] > 0 and ratio > threshold
tolerance_applied = (
    threshold > 0.0
    and result["quarantined"] > 0
    and not over_threshold
    and not schema_invalid
)
intake_verdict = "FAIL" if (schema_invalid or over_threshold) else "PASS"
result["quarantine_max_ratio"] = threshold
result["tolerance_applied"] = tolerance_applied
```

This guarantees that:

- A dataset with `quarantine_max_ratio: 0.05` and 3% dupes gets
  `intake_verdict = PASS`, `tolerance_applied = True`, and the drift /
  benchmark stages run.
- A dataset with `quarantine_max_ratio: 0.05` and 7% dupes gets
  `intake_verdict = FAIL`, `tolerance_applied = False`, and `_validate_
  dataset_readiness` (called from drift/benchmark) raises before any
  drift/benchmark scoring.
- A dataset with a schema violation always gets `intake_verdict = FAIL`,
  `tolerance_applied = False`, regardless of threshold.

A small private helper
`src/driftsentinel/orchestration/runner.py::_evaluate_with_tolerance(contract, frame)`
encapsulates this computation and is reused by both `run_dataset_intake`
and `_validate_dataset_readiness` so the gate logic is single-sourced.

### 4.5 Template surface

`templates/dataset_contract.yml` documents the knob with an inline comment
naming the default and the range. The example value stays at `0.0` so the
shipped contract is byte-stable for operators relying on the existing
default behavior:

```yaml
contract:
  required_columns:
    - ...
  business_key: [id]
  batch_identifier: batch_id
  # Optional ratio in [0.0, 1.0]. Default 0.0 (zero tolerance — current
  # behavior). Set above 0.0 to allow up to that ratio of row-level
  # quarantine (business-key duplicates, batch-identifier nulls, type or
  # null violations on present columns) before drift / benchmark stages
  # fail closed. Schema-level violations (missing required columns or
  # missing business-key columns) always fail regardless of this value.
  quarantine_max_ratio: 0.0
```

### 4.6 Out of scope (re-stated)

- Per-violation tolerance buckets.
- Changing the registry on-disk JSON schema (the new key rides inside the
  embedded contract dict, no migration needed).
- Drift / benchmark policy gating (the threshold is a contract concern).
- Notebook UI or Gradio app changes — the operator dashboard already
  surfaces the full evidence JSON and will display the two new fields
  without code change.

## 5. Files Touched

| File | Change |
| --- | --- |
| `src/driftsentinel/orchestration/runner.py` | `_validate_dataset_readiness` honors the threshold and records `tolerance_applied` / `quarantine_max_ratio`; `run_dataset_intake` re-uses the same helper for verdict computation |
| `src/driftsentinel/config/loader.py` | New `_validate_quarantine_max_ratio` helper; `_validate_dataset_contract` calls it after the required-keys check |
| `templates/dataset_contract.yml` | Document the new optional knob with default and range |
| `tests/test_intake.py` | Cover `quarantine_ratio` numerator/denominator on existing surface (already partially present) — extended to assert `quarantine_ratio` rounding behavior on a known fraction |
| `tests/test_orchestration.py` | New tests for `_validate_dataset_readiness` covering all four ratio cases per §6 |
| `tests/test_dataset_orchestration.py` | New tests asserting `tolerance_applied` and `quarantine_max_ratio` land in the intake evidence payload |
| `tests/test_config_loading.py` | Cover loader rejection of out-of-range and non-numeric `quarantine_max_ratio` |
| `specs/DS-TM-001_Traceability_Matrix.md` | Append a row mapping DS-FR-005 / DS-SR-002 to this patch and bump version + changelog |
| `specs/README.md` | No new entry required — existing DS-PATCH-* convention does not list each patch in the index; no precedent to add one (DS-PATCH-032..035 are not indexed there). Verify and skip unless the convention has changed. |

No bundle resources, job parameters, runtime volume layout, CLI flags,
notebooks, or Gradio app modules change.

## 6. Validation

### 6.1 Unit tests — `tests/test_orchestration.py`

A new test class `TestValidateDatasetReadiness` covers:

1. **`ratio = 0` (default), 0 quarantined → PASS.** Frame fully clean
   against a contract that omits `quarantine_max_ratio`. `_validate_
   dataset_readiness` returns the evaluation dict; `tolerance_applied`
   is `False`; `quarantine_max_ratio` is `0.0`.
2. **`ratio = 0` (default), 1+ quarantined → FAIL.** Backward-compat
   guard: existing zero-tolerance behavior still applies when the contract
   omits the key. `ValueError` is raised; message contains the
   `quarantined=` count and the violation summary.
3. **`ratio = 0.05`, 3% dupes → PASS.** Contract sets `quarantine_max_
   ratio: 0.05`. Frame has 100 rows with exactly 3 business-key dupes (3%).
   The function returns the evaluation dict with
   `tolerance_applied = True`, `quarantine_max_ratio = 0.05`, and
   `quarantine_ratio` recorded.
4. **`ratio = 0.05`, 7% dupes → FAIL.** Contract sets the same threshold;
   frame has 100 rows with 7 business-key dupes. `ValueError` raised;
   message includes `quarantine_ratio=` and `quarantine_max_ratio=`
   substrings.
5. **Schema violation regardless of ratio → FAIL.** Contract sets
   `quarantine_max_ratio: 1.0` (would tolerate everything). Frame is
   missing a required column. `ValueError` raised; message names the
   missing column. The test guards the §2 invariant.
6. **`tolerance_applied` is False on the schema-invalid path even when
   quarantined rows are present.** Defensive: schema invalidity does not
   set `tolerance_applied = True`.
7. **`tolerance_applied` is False when threshold is `0.0` even with 0
   quarantined.** Documented invariant: the field is `True` iff the gate
   actively tolerated something.

### 6.2 Unit tests — `tests/test_dataset_orchestration.py`

Add `TestIntakeToleranceEvidence`:

1. **Tolerance fields land in intake evidence.** Using the existing
   in-memory fixtures, build a contract with `quarantine_max_ratio: 0.10`
   and a frame with ~5% row-level dupes. Run `run_dataset_intake` with a
   `tmp_path` evidence dir and assert the written intake artifact contains
   `quarantine_max_ratio=0.10`, `tolerance_applied=true`, and
   `overall_verdict="PASS"`.
2. **Schema-invalid evidence still records the threshold but with
   `tolerance_applied=false` and `overall_verdict="FAIL"`.**

### 6.3 Unit tests — `tests/test_config_loading.py`

Add three loader-boundary tests:

1. Contract with `quarantine_max_ratio: 0.05` loads cleanly and the value
   round-trips into the parsed dict.
2. Contract with `quarantine_max_ratio: 1.5` raises `ConfigError`
   referencing `quarantine_max_ratio` and the allowed range.
3. Contract with `quarantine_max_ratio: "five percent"` raises
   `ConfigError` referencing `quarantine_max_ratio`.
4. Contract that omits `quarantine_max_ratio` loads cleanly and the
   parsed dict does not synthesize the key (so absence is preserved; the
   default is applied at the gate, not at load time).

### 6.4 Unit tests — `tests/test_intake.py`

The existing `evaluate_dataframe_contract` tests already exercise
`quarantine_ratio`. Extend with one test that asserts a known fraction
(e.g. 3 quarantined rows over 100 total → `quarantine_ratio == 0.03`)
to lock the rounding semantics relied on by the new gate.

### 6.5 Required local checks

```bash
uv run ruff check .
uv run mypy src/driftsentinel tests
uv run pytest -k "readiness or tolerance or quarantine_max_ratio"
uv run pytest
```

### 6.6 Manual smoke (post-merge, optional)

On the demo dataset that motivated this issue, set
`quarantine_max_ratio: 0.03` in the dataset contract, re-run
`uv run driftsentinel databricks run --catalog <C> --dataset-id
nyc_tlc_<...>`, and confirm the intake evidence artifact records
`tolerance_applied=true`, `quarantine_ratio` ~0.022, and the drift /
benchmark stages execute. This is operator-side verification and is
captured in `report/` under the existing append-only convention if
performed.

## 7. Acceptance Criteria

- [ ] Dataset contract schema accepts an optional `quarantine_max_ratio`
   under `contract`, defaulting to `0.0`, with allowed range `[0.0, 1.0]`.
- [ ] Loader rejects out-of-range and non-numeric values at load time with
   a `ConfigError` that names the key.
- [ ] `_validate_dataset_readiness` raises `ValueError` only when
   `schema_valid == False` *or* `quarantine_ratio > quarantine_max_ratio`.
- [ ] When the gate raises on the ratio path, the message includes
   `quarantine_ratio=` and `quarantine_max_ratio=` substrings alongside the
   existing `quarantined=`/`top_violations=` details.
- [ ] Schema violations still fail closed regardless of
   `quarantine_max_ratio` (verified by §6.1 case 5).
- [ ] Intake evidence payload gains `quarantine_max_ratio: float` and
   `tolerance_applied: bool` fields; `quarantine_ratio` retains its
   current semantics.
- [ ] `run_dataset_intake` PASS/FAIL verdict honors the same threshold so
   the intake artifact and the drift/benchmark gate agree.
- [ ] `templates/dataset_contract.yml` documents the new knob with default
   and range.
- [ ] Unit tests cover all four ratio cases (0/0, 0/>0, 5%/3%, 5%/7%) plus
   the schema-violation invariant and the loader-boundary cases.
- [ ] `make lint`, `make typecheck`, `make test` all pass.
- [ ] `specs/DS-TM-001_Traceability_Matrix.md` is updated; version bumped
   and changelog entry added.

## 8. Residual Risks

- **Operator confusion with mixed-method ratios.** A contract that sets
  the threshold at the row-level ratio still gates the *raw count* into
  evidence. Mitigation: the readiness error message names both the count
  and the ratio so operators can debug both axes.
- **Threshold drift.** Operators may set the ratio above the actual
  data-quality floor, masking a regression. Mitigation: `tolerance_
  applied=true` in evidence makes every tolerated run auditable; analytics
  in the operator dashboard already surface the full payload.
- **Backward compatibility.** Contracts authored before this patch
  continue to work unchanged because the default is `0.0`. Verified by
  §6.1 cases 1 and 2 and by the intake/dataset-orchestration test suites
  that do not set the new key.
- **Per-violation tolerance demand.** Operators may later request
  per-violation buckets (e.g. allow dupes but never null batch IDs).
  Mitigation: out of scope per §3 and per the issue. The single ratio
  knob is composable with future per-violation gates because the
  evaluator already records per-violation counts in `violation_counts`.
- **Confused intake verdict semantics.** A `PASS` intake artifact with
  `tolerance_applied=true` could be misread as "no quarantine occurred."
  Mitigation: the artifact also records `quarantined`, `quarantine_ratio`,
  and the populated `violation_counts` / `violation_examples` fields, so
  downstream consumers see the tolerated population explicitly.

## 9. Traceability

- DS-PRD: §Intake Certification, §Dataset Contracts, §Evidence Discipline.
- DS-SRS: DS-FR-005 (intake quarantine outputs), DS-SR-002 (intake
  certification with explicit failure detail).
- DS-SDD-001: §Intake Module, §Orchestration Module, §Evidence Module.
- DS-TP-001: §Intake tests, §Dataset orchestration tests, §Config loader
  tests.
- Issue #36 acceptance criteria mapped 1:1 to §7 above.
