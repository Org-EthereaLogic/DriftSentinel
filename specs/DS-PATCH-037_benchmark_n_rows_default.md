# DS-PATCH-037 — Raise Benchmark `n_rows` Default From 1000 to 10000

| Field | Value |
| --- | --- |
| Tracking issue | [Org-EthereaLogic/DriftSentinel#37](https://github.com/Org-EthereaLogic/DriftSentinel/issues/37) |
| Type | improvement |
| Area | `area:benchmark` |
| Priority | p3 |
| Status | Planned |
| Owner | lead-software-engineer |
| Methodology precedence | FailLens_Core (no PASS/FAIL claims without trustworthy evidence), E62 (Databricks runtime path), DS-SDD-001 §Benchmark Module / §Bundle Operations |

## 1. Problem Statement

`resources/dataset_pipeline_job.yml:18-19` and `resources/benchmark_job.yml:18-19`
default the benchmark sample size parameter `n_rows` to `"1000"`. At
n=1000 the dual-track benchmark hits a statistical recall floor: the
`EVIDENCE_LOG.md` Phase 6 (iter-2) record shows the challenger quality
track measuring `quality_recall = 0.347` on a clean 3 M-row NYC TLC
landed parquet sampled at n=1000, well below the `0.80` PASS gate
threshold defined at `templates/benchmark_policy.yml:35-40`.

Because `templates/benchmark_policy.yml`'s `quality_recall` gate is a
`FAIL` gate and the dataset pipeline applies `verdict_on_fail: block`,
healthy installations get a confusing `FAIL` verdict on first run and
downstream consumers see the dataset blocked. A workaround exists —
operators can override `n_rows` via job parameter or
`uv run driftsentinel databricks run --n-rows 10000` — but the
wrong-by-default behavior is bad first-impression UX. This is a
demo-friction P3, not a correctness bug.

## 2. Goal

Raise the bundle-resource defaults for `n_rows` from `"1000"` to
`"10000"` so that out-of-the-box benchmark runs land above the
statistical recall floor. Document the floor in
`templates/benchmark_policy.yml` so an operator who lowers the value
sees the consequence inline. Add one regression test that exercises
the full benchmark on the synthetic clean dataset at `n=10000` and
asserts `quality_recall >= 0.80`. Note the default change in the
deployment guide so operators upgrading existing bundles see the new
value.

## 3. Non-Goals

- Changing the Python API default of `run_benchmark(n_rows=1000)` in
  `src/driftsentinel/benchmark/orchestrator.py:38-40`. The bundle
  defaults are the operator-visible knob; the Python default is held
  invariant by the existing test suite (`tests/test_benchmark.py`
  uses `N_ROWS = 200` for fast unit tests). Touching it would
  silently inflate every `run_benchmark()` call that omits the
  parameter, including in-process consumers and notebook ad-hoc use.
- Changing `src/driftsentinel/orchestration/runner.py:479,527` (which
  default `n_rows=200` in the orchestration entry points used by
  unit tests) — these are CI-fast paths and out of scope.
- Changing the notebook widget defaults at
  `notebooks/05_run_control_benchmark.py:53` and
  `notebooks/07_run_dataset_pipeline.py:60`. Bundle job execution
  passes `n_rows` as a `base_parameter`, which overrides the widget
  default; the widget default is only relevant for manual notebook
  runs and is left alone to keep "open notebook, click Run" fast.
- Tightening or relaxing any benchmark gate threshold. The
  `quality_recall` `>= 0.80` `FAIL` gate stays as-is; this patch
  only changes the sample size that feeds the gate.
- Bumping `templates/benchmark_policy.yml.seed` or any other policy
  field. Only the comment near the `quality_recall` gate is added.
- Modifying `verdict_on_fail` semantics or downstream blocked-publish
  behavior. Issue #37 is explicit that this is a P3 first-impression
  fix.

## 4. Design

### 4.1 Bundle resource defaults

Update the two bundle resources that declare `n_rows` as a job
parameter with a `default`:

- `resources/dataset_pipeline_job.yml:18-19` — change
  `default: "1000"` → `default: "10000"`.
- `resources/benchmark_job.yml:18-19` — change
  `default: "1000"` → `default: "10000"`.

No other resource under `resources/` declares an `n_rows` parameter
(verified by `grep -n n_rows resources/`). The two values are
`"10000"` (string-quoted) to match the existing convention for job
parameter defaults in this repository — Databricks job parameters are
typed as strings and the consuming notebooks already
`int(dbutils.widgets.get("n_rows"))` at
`notebooks/05_run_control_benchmark.py:66` and
`notebooks/07_run_dataset_pipeline.py:72`.

### 4.2 Template documentation

`templates/benchmark_policy.yml` adds a single inline comment block
above the `gates` list naming the recall floor at low N. The comment
is anchored above the gates (not above just `quality_recall`)
because all four `quality_*` gates suffer the same statistical
noise at small N — the recall gate is just where it surfaces first
in practice.

```yaml
  # Recall, precision, F1, and FPR are statistically noisy below
  # n_rows ~ 5000 because the injected fault population is small in
  # absolute terms; recommend n_rows >= 10000 for trustworthy gates.
  # See specs/DS-PATCH-037_benchmark_n_rows_default.md.
  gates:
    - name: quality_recall
      ...
```

The example `seed: 42` and the gate thresholds are unchanged — the
template stays byte-stable for operators relying on the existing
defaults.

### 4.3 Regression test

`tests/test_benchmark.py` gains one new test, `test_run_benchmark_at_default_n_rows_meets_recall_gate`,
near the existing full-orchestrator block (after
`test_run_benchmark_with_evidence`). The test:

```python
def test_run_benchmark_at_default_n_rows_meets_recall_gate() -> None:
    """At the bundle default n=10000, challenger quality_recall must clear
    the 0.80 FAIL gate on the synthetic clean dataset (DS-PATCH-037)."""
    result = run_benchmark(seed=SEED, n_rows=10000)
    assert result["measured"]["quality_recall"] >= 0.80, (
        f"quality_recall {result['measured']['quality_recall']:.3f} below 0.80 "
        "PASS gate at n=10000 — see DS-PATCH-037"
    )
```

Rationale for placement and shape:

- Reuses the module-level `SEED = 42` for determinism. The
  benchmark orchestrator is fully seed-controlled
  (`src/driftsentinel/benchmark/orchestrator.py:38-79`) so the
  assertion is byte-stable on a fixed seed and `n_rows`.
- Runs against the synthetic dataset (no `reference_df=` argument)
  so the test is self-contained and does not require any fixture.
- Asserts only `quality_recall >= 0.80` per the issue acceptance
  criterion — does not over-bind on precision, F1, or FPR. Future
  changes to detector behavior should be free to move those metrics
  within their own gates without breaking this test.
- The test runs the full orchestrator at n=10000. Local timing
  measurement: existing `test_run_benchmark_deterministic` runs the
  full orchestrator twice at n=200 in well under 1 second; the
  detector code is O(n) on row count, so a single n=10000 run is on
  the order of seconds. This is acceptable for the unit suite. If
  the test ever materially slows the suite, mark it `@pytest.mark.
  slow` or move it to an integration-only path; that is a future
  concern, not this patch's.

The existing `test_run_benchmark_deterministic` and
`test_run_benchmark_with_evidence` continue to use `N_ROWS = 200`
for speed. Only the new test exercises `n=10000`.

### 4.4 Deployment guide note

`docs/deployment_guide.md` (the canonical operator surface — the
issue's `docs/deployment.md` reference is a near-miss; this is the
correct path) gains one line in the runtime-inputs paragraph
(currently at line 207, "Runtime inputs (`dataset_id`, policy paths,
`seed`, `n_rows`) are Databricks job parameters …"). The line names
the `n_rows` default and points at this spec for context:

> The `n_rows` parameter defaults to `10000` in the bundle resources
> (raised from `1000` in DS-PATCH-037). Lower values are statistically
> noisy on the quality recall gate; see
> `specs/DS-PATCH-037_benchmark_n_rows_default.md`.

This is intentionally one short sentence — the deployment guide is
already long; deep context belongs in this spec.

### 4.5 Traceability

`specs/DS-TM-001_Traceability_Matrix.md` gains a row mapping the
benchmark requirement to this patch and a changelog entry.

- Requirement: `DS-FR-007` (control effectiveness benchmarking) and
  `DS-SR-004`.
- Verification surface: `resources/benchmark_job.yml`,
  `resources/dataset_pipeline_job.yml`,
  `templates/benchmark_policy.yml`, `tests/test_benchmark.py`,
  `docs/deployment_guide.md`.

The matrix already has a row for `DS-FR-007 / DS-SR-004` — augment
its `Verification Surface` cell with this patch and the regression
test, and add a new changelog row. Bump version `1.4` → `1.5`.

### 4.6 Out of scope (re-stated)

- The Python `run_benchmark` default and the orchestration runner
  default. Both stay at their current values per §3.
- Notebook widget defaults. Bundle-backed runs override them; manual
  notebook runs are not the failure surface this patch addresses.
- Gate thresholds, gate types, fault profiles, drift profiles,
  scoring math, evidence schema. None change.
- Any `report/` artifact regeneration. The append-only convention
  applies; existing artifacts stay.

## 5. Files Touched

| File | Change |
| --- | --- |
| `resources/dataset_pipeline_job.yml` | `n_rows` default `"1000"` → `"10000"` |
| `resources/benchmark_job.yml` | `n_rows` default `"1000"` → `"10000"` |
| `templates/benchmark_policy.yml` | Inline comment block above `gates:` per §4.2 |
| `tests/test_benchmark.py` | New `test_run_benchmark_at_default_n_rows_meets_recall_gate` per §4.3 |
| `docs/deployment_guide.md` | One-sentence note in the runtime-inputs paragraph per §4.4 |
| `specs/DS-TM-001_Traceability_Matrix.md` | DS-FR-007/DS-SR-004 row + changelog entry per §4.5 |

No source code under `src/driftsentinel/{intake,drift,benchmark,
evidence,orchestration,config}/` changes. No CLI flags, notebook
widgets, bundle variables, or runtime volume layout change.

## 6. Validation

### 6.1 Unit test — `tests/test_benchmark.py`

Per §4.3:

1. **Recall meets gate at default n=10000.** Run
   `run_benchmark(seed=42, n_rows=10000)` end-to-end and assert
   `result["measured"]["quality_recall"] >= 0.80`. No fixture, no
   reference_df, no tmp_path. The seeded synthetic dataset is the
   exact surface the bundle defaults exercise.

### 6.2 Bundle validation

`make bundle-validate CATALOG=<C> [PROFILE=<P>]` must continue to
parse the bundle cleanly with the updated `n_rows` defaults. This is
exercised manually post-merge — CI does not currently run
`databricks bundle validate` end-to-end (no Databricks credentials).

### 6.3 Required local checks

```bash
make lint
make typecheck
make test
uv run pytest tests/test_benchmark.py::test_run_benchmark_at_default_n_rows_meets_recall_gate -v
```

### 6.4 Manual smoke (post-merge, optional)

Re-run the demo flow on the NYC TLC dataset with the bundle-resolved
defaults (no `--n-rows` override):

```bash
make bootstrap CATALOG=<C> DATASET_ID=<D> DRIFT_POLICY=<path>
```

Confirm the benchmark evidence artifact at
`/Volumes/<C>/<S>/driftsentinel_runtime/evidence/<run-id>/bench_*.json`
records `meta.n_rows == 10000` and the `quality_recall` gate clears
`>= 0.80`. Captured in `report/` under the existing append-only
convention if performed.

## 7. Acceptance Criteria

- [ ] `resources/dataset_pipeline_job.yml` `n_rows` parameter
  `default` is `"10000"`.
- [ ] `resources/benchmark_job.yml` `n_rows` parameter `default` is
  `"10000"`.
- [ ] No other resource under `resources/` declares an `n_rows`
  default (verified by grep).
- [ ] `templates/benchmark_policy.yml` adds a comment near the gate
  thresholds explaining the recall floor at low N and recommending
  `n_rows >= 10000`.
- [ ] `tests/test_benchmark.py` adds one regression test that runs
  the full benchmark on the synthetic clean dataset at `n=10000`
  and asserts `quality_recall >= 0.80`.
- [ ] `docs/deployment_guide.md` benchmark/runtime-inputs section
  records the new default and points at this spec.
- [ ] `specs/DS-TM-001_Traceability_Matrix.md` is updated; version
  bumped and changelog entry added.
- [ ] `make lint`, `make typecheck`, `make test` all pass.

## 8. Residual Risks

- **Bundle-default drift vs Python API default.** After this patch,
  `n_rows=10000` is the bundle-resource default but
  `run_benchmark()` still defaults to `1000`. This is intentional
  per §3 (CI determinism, fast unit tests, in-process callers). The
  divergence is documented in this spec and in §4.4 of the
  deployment guide so operators reading either surface understand
  which default applies. Future cleanup can unify the two when the
  test suite is restructured to mark slow tests; out of scope here.
- **Slower demo first-run.** A factor-of-10 row count increase
  raises the per-run benchmark cost. The synthetic dataset
  generation and detectors are O(n) on row count, so a Free Edition
  cluster benchmark moves from ~seconds to ~tens of seconds. This
  is acceptable for a one-time first-run demo and well below the
  notebook timeout. Operators who need the fast path can still
  override with `--n-rows 1000` or pass `n_rows: "1000"` in
  `--params`.
- **Regression-test cost.** The new test runs the full orchestrator
  at n=10000 every CI run. Local measurement (see §4.3) puts this
  on the order of seconds, which is acceptable. If future detector
  changes inflate the cost, the test gets `@pytest.mark.slow` —
  not handled in this patch because the cost is currently
  acceptable.
- **Recall floor moves.** If a future detector change lowers
  quality_recall at n=10000 below `0.80`, the regression test
  catches it immediately and forces a conscious decision (raise
  n_rows further, lower the gate, or fix the detector regression).
  That is the intended forcing function and not a defect of this
  patch.
- **Operators on existing bundles.** Operators who deployed the
  bundle before this patch and run with the explicit
  `--n-rows 1000` override (or their own `--params` JSON pinning
  `1000`) continue to see the old behavior. The deployment-guide
  note names the new default so an upgrade-time read informs them.
  This is acceptable for a P3 first-impression fix.

## 9. Traceability

- DS-PRD: §Control Benchmarking, §Operator-Friendly Bundle.
- DS-SRS: DS-FR-007 (control effectiveness benchmarking),
  DS-SR-004 (benchmark scoring and gates).
- DS-SDD-001: §Benchmark Module, §Bundle Operations.
- DS-TP-001: §Benchmark tests, §Bundle deploy checks.
- Issue #37 acceptance criteria mapped 1:1 to §7 above.
