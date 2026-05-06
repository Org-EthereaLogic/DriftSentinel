# DS-PATCH-040: NYC TLC Yellow Taxi Demo Example

| Field | Value |
| --- | --- |
| Document ID | DS-PATCH-040 |
| GitHub Issue | [#41](https://github.com/Org-EthereaLogic/DriftSentinel/issues/41) |
| Version | 1.0 |
| Status | Approved |
| Author | Anthony Johnson |
| Date | 2026-05-05 |
| Labels | area:demo, area:docs, demo:nyc-taxi, type:feature, priority:p2 |
| Methodology precedence | E62_Live_Databricks_Bronze_execution (real public dataset replay), FailLens_Core (explicit failure on missing inputs), DS-SDD-001 §Demo Surface, DS-SRS DS-FR-010 / DS-SR-007 (deterministic demo path) |

## 1. Problem Statement

New users get the runbook (`DEMO_RUNBOOK.md` in the demo workspace, 561 lines)
but no in-repo working example. The corrected NYC Taxi configs (8-column
composite `business_key`, `tpep_pickup_datetime` `batch_identifier`, proven
gate thresholds) live outside the product repo at
`~/Dev/DriftSentinel_demo/configs/nyc_taxi/` and are not discoverable from a
fresh clone. The path from "I cloned this repo" to "I saw it run end-to-end"
is undocumented and undiscoverable.

## 2. Goal

Ship a complete, in-repo, one-shot demo path that lets any operator with a
Databricks workspace and Unity Catalog catalog reproduce the full intake →
drift → benchmark pipeline against real public data with a single command:

```bash
make demo-nyc-taxi CATALOG=<catalog> PROFILE=<profile>
```

## 3. Non-Goals

- Generalizing to other public datasets (Chicago Crimes, NYC 311, etc.).
  Each will be filed as a separate issue if motivated.
- Hosting or mirroring the NYC TLC parquet files. The script downloads from
  the public CloudFront mirror at request time.
- Replacing the demo workspace at `~/Dev/DriftSentinel_demo/`. That repo
  remains the canonical evidence trail for the 2026-05-04 replay; this patch
  only ports the replay-ready configs into the product repo.

## 4. Design

### 4.1 Directory layout

```
examples/
└── nyc_yellow_taxi/
    ├── README.md
    ├── dataset_contract.yml
    ├── drift_policy.yml
    └── benchmark_policy.yml

scripts/
└── run_nyc_taxi_demo.sh
```

The configs are byte-equivalent to
`~/Dev/DriftSentinel_demo/configs/nyc_taxi/` as of the 2026-05-04 replay.
They use `${CATALOG}` placeholders that DS-PATCH-032 substitution resolves at
load time when the CLI is invoked with `--catalog`.

### 4.2 Script contract

`scripts/run_nyc_taxi_demo.sh` is a single bash file with no other helpers.
It runs five stages in order, each idempotent against re-runs:

| Stage | Action |
| --- | --- |
| 1 | Download `yellow_tripdata_<month>.parquet` for the baseline and landing months from `https://d37ci6vzurychx.cloudfront.net/trip-data/`. Cached: skip if the destination file already exists. |
| 2 | Deduplicate each month with the 8-column composite `business_key` via an inline `uv run python` block using pyarrow + pandas. Marker file (`.deduped_<month>`) prevents re-running on cached output. |
| 3 | `driftsentinel registry add --force` against the example contract, with `--catalog/--schema/--volume-name` threaded into placeholder substitution. `--force` is used so re-runs converge instead of failing on the second invocation. |
| 4 | `driftsentinel databricks connect --wait` with the example drift + benchmark policies, the prepared baseline + landing directories, and the freshly registered dataset. The script sources `scripts/databricks_tf_env.sh` first so terraform/OpenTofu detection runs uniformly. |
| 5 | Print a pointer to the runtime evidence path. The script does not parse evidence — verdict reading is intentionally a separate operator step (the run output already prints the verdict). |

### 4.3 Argument surface

```
scripts/run_nyc_taxi_demo.sh --catalog <catalog> [--profile <profile>] \
    [--schema <schema>] [--volume-name <volume>] \
    [--baseline-month YYYY-MM] [--landing-month YYYY-MM] \
    [--work-dir <dir>] [--registry <path>]
```

| Flag | Default | Notes |
| --- | --- | --- |
| `--catalog` | required | Unity Catalog catalog name |
| `--profile` | none | Databricks CLI profile, threaded into both `registry add` and `connect` |
| `--schema` | `default` | Threaded into `${SCHEMA}` substitution |
| `--volume-name` | `driftsentinel_runtime` | Threaded into `${VOLUME}` substitution |
| `--baseline-month` | `2024-01` | NYC TLC YYYY-MM identifier |
| `--landing-month` | `2024-02` | NYC TLC YYYY-MM identifier |
| `--work-dir` | `/tmp/nyc_taxi_demo` | Local cache + dedup workspace |
| `--registry` | `<work-dir>/registry.json` | Registry JSON path |

`--catalog` is the only required flag. Missing `--catalog` fails fast with a
single error message and the inline help.

### 4.4 Failure behavior

- Missing `--catalog`: exit 2, prints help.
- Unknown argument: exit 2, prints help.
- Download failure: `curl --fail --retry 3 --retry-delay 2`; non-zero exit
  propagates via `set -euo pipefail`.
- Dedup script failure: propagates the inline Python exit code.
- `registry add --force` failure: propagates the CLI's exit code.
- `databricks connect --wait` failure: propagates exit 1, which is the
  pipeline's own fail-closed signal.

### 4.5 Makefile target

A new `demo-nyc-taxi` target wraps the script and reuses the existing
`CATALOG`/`PROFILE` convention shared with `bundle-validate`,
`bundle-deploy`, `app-deploy`, and `bootstrap`. It does **not** source
`scripts/databricks_tf_env.sh` itself — the demo script does that internally
ahead of the `databricks connect` call.

### 4.6 Test surface

`tests/test_packaging.py` adds two small tests that gate the example as a
shippable artifact:

- `test_nyc_taxi_example_ships_required_files` — asserts the directory
  contains exactly the four expected files, and that the contract retains the
  8-column composite `business_key` and `tpep_pickup_datetime`
  `batch_identifier`. This catches accidental edits to the canonical configs.
- `test_nyc_taxi_demo_script_is_executable_and_wired` — asserts the script
  exists, is executable, has a bash shebang, references both `registry add`
  and `databricks connect --wait`, and that the Makefile defines the
  `demo-nyc-taxi` target wiring the script.

The script itself is not invoked in CI; it requires Databricks credentials
and network egress to a third-party host. Manual smoke testing under §6.3 is
the verification surface.

### 4.7 Documentation surface

- `examples/nyc_yellow_taxi/README.md` — concise replay instructions plus the
  rationale for each config choice (8-col key, batch identifier, monitor set,
  baseline `min_rows`).
- Root `README.md` — new "One-shot demo: NYC TLC Yellow Taxi" subsection
  inside Quickstart pointing at `make demo-nyc-taxi`.

`docs/deployment_guide.md` is intentionally not changed — the demo lives
under `examples/`, not the canonical deployment surface.

## 5. Files Touched

| File | Change |
| --- | --- |
| `examples/nyc_yellow_taxi/dataset_contract.yml` | New — copied verbatim from the 2026-05-04 demo replay |
| `examples/nyc_yellow_taxi/drift_policy.yml` | New — copied verbatim |
| `examples/nyc_yellow_taxi/benchmark_policy.yml` | New — copied verbatim |
| `examples/nyc_yellow_taxi/README.md` | New — replay instructions and rationale |
| `scripts/run_nyc_taxi_demo.sh` | New — bash one-shot replay script |
| `Makefile` | New `demo-nyc-taxi` target plus help line and `.PHONY` entry |
| `tests/test_packaging.py` | New `test_nyc_taxi_example_ships_required_files`, `test_nyc_taxi_demo_script_is_executable_and_wired` |
| `README.md` | New Quickstart subsection pointing at `make demo-nyc-taxi` |
| `specs/DS-TM-001_Traceability_Matrix.md` | Append DS-PATCH-040 to the DS-FR-010 / DS-SR-007 row and add a 1.8 changelog entry on 2026-05-05 |

No source under `src/driftsentinel/`, bundle resources, or notebook
definitions changes.

## 6. Validation

### 6.1 Unit tests

```bash
uv run pytest tests/test_packaging.py -k nyc_taxi
```

Expected: 2 passed.

### 6.2 Required local checks

```bash
uv run ruff check .
uv run mypy src/driftsentinel tests
uv run pytest
```

### 6.3 Manual smoke test (post-merge)

On a workstation with an authenticated Databricks CLI, OpenTofu installed,
and an existing catalog:

```bash
make demo-nyc-taxi CATALOG=<C> PROFILE=<P>
```

Expected: the script downloads, deduplicates, registers the dataset, runs the
full pipeline, and prints the evidence pointer. The pipeline verdict is
expected to be `BLOCK` on Jan→Feb 2024 (real seasonal drift on `fare_amount`
and `trip_distance`) — that is the demo's headline finding, not a defect.

## 7. Acceptance Criteria

- [x] `examples/nyc_yellow_taxi/` exists with `dataset_contract.yml`,
  `drift_policy.yml`, `benchmark_policy.yml`, and `README.md`.
- [x] The contract preserves the 8-column composite `business_key` and
  `tpep_pickup_datetime` `batch_identifier`.
- [x] `scripts/run_nyc_taxi_demo.sh` exists, is executable, downloads Jan +
  Feb 2024 parquet, deduplicates via the 8-column composite, calls
  `driftsentinel registry add`, and calls `driftsentinel databricks connect
  --wait`.
- [x] `make demo-nyc-taxi CATALOG=<C> PROFILE=<P>` invokes the script with
  the provided catalog and profile.
- [x] `tests/test_packaging.py` asserts the example directory ships the
  required files and that the script is executable + wired into the Makefile.
- [x] `README.md` Quickstart points at `make demo-nyc-taxi`.
- [x] `make lint`, `make typecheck`, `make test` all pass.
- [x] `specs/DS-TM-001_Traceability_Matrix.md` references DS-PATCH-040 under
  DS-FR-010 / DS-SR-007.

## 8. Residual Risks

- **Upstream dataset availability.** The NYC TLC CloudFront mirror is a
  third-party dependency. If the host or path changes, the script's download
  step fails fast with a non-zero curl exit. Mitigation: the URL is the
  documented public mirror (used by every public NYC TLC tutorial); the host
  has been stable for years; the script does not silently degrade.
- **Schema drift on TLC parquet.** The TLC has historically renamed columns
  between schema generations. The example contract pins the column names
  used in the 2024 schema; replays against older months may fail intake on
  schema mismatch. This is intentional fail-closed behavior — replays
  outside Jan–Feb 2024 should be treated as unsupported in this patch.
- **Local disk + memory.** Each parquet file is ~50–60 MB on disk and the
  dedup step materializes the whole frame in pandas. On constrained hosts
  the dedup step can OOM. Mitigation: `--work-dir` is configurable and the
  inline dedup script is small enough to be replaced by a streaming variant
  in a future patch if motivated.
- **Verdict variability.** Replays against month pairs other than Jan→Feb
  2024 may yield different intake/drift/benchmark verdicts. Mitigation: the
  README explicitly documents this; the `--baseline-month/--landing-month`
  flags allow operator choice.

## 9. Traceability

- DS-PRD: §Demo Surface, §Operator-Friendly Bundle.
- DS-SRS: DS-FR-010 (deterministic demo path), DS-SR-007 (replayable demo
  artifacts).
- DS-SDD-001: §Demo Surface, §CLI Surface.
- DS-TP-001: §Packaging tests.
- Issue #41 acceptance criteria mapped 1:1 to §7 above.
- DS-PATCH-032 (placeholder substitution) and DS-PATCH-039 (`registry add`)
  are upstream dependencies — the script consumes both.
