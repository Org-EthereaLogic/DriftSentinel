# DS-PATCH-033 — `databricks run` Auto-Resolves Drift + Benchmark Policy Paths

| Field | Value |
| --- | --- |
| Tracking issue | [Org-EthereaLogic/DriftSentinel#33](https://github.com/Org-EthereaLogic/DriftSentinel/issues/33) |
| Type | improvement |
| Area | `area:cli` |
| Priority | p1 |
| Status | Planned |
| Owner | lead-software-engineer |
| Methodology precedence | FailLens_Core (explicit failure), E62 (Databricks runtime path), DS-SDD-001 §CLI |

## 1. Problem Statement

Today, `uv run driftsentinel databricks run --catalog X --dataset-id Y --wait`
fails with:

> `ValueError: Set drift_policy_path to a dataset-compatible drift policy
> before running the pipeline.`

The runtime volume already contains the dataset's drift and benchmark policies
because `connect` uploaded them. Forcing the operator to re-pass
`--drift-policy /Volumes/.../policies/drift_policy.yml` on every replay is
redundant and brittle. Demo evidence: Phase 12 of
`/Users/etherealogic-2/Dev/DriftSentinel_demo/EVIDENCE_LOG.md` records this
friction.

## 2. Goal

`databricks run` must auto-resolve drift and benchmark policy paths to the
canonical runtime-volume locations when the CLI flags are omitted, while
preserving operator overrides and failing closed when the volume does not
contain the expected files.

## 3. Non-Goals

- Reading policy paths from the dataset contract or registry payload (the
  contract schema does not currently carry policy bindings; introducing that
  would change `DS-SDD-001 §Configuration`).
- Changes to bundle resources or job parameter schemas beyond default
  resolution behavior.

## 4. Design

### 4.1 Canonical on-volume layout

`connect` already uploads policies under `/Volumes/<catalog>/<schema>/<volume>/policies/`
but uses the **local file's basename** for the destination filename. The fix
standardizes the on-volume basenames under a dataset-scoped subdirectory so
`run` can resolve them deterministically without cross-dataset overwrites:

| Input | Canonical remote path |
| --- | --- |
| `--drift-policy <local>.yml` | `<volume_root>/policies/<dataset_id>/drift_policy.yml` |
| `--benchmark-policy <local>.yml` | `<volume_root>/policies/<dataset_id>/benchmark_policy.yml` |

Local filename is irrelevant; the remote layout is fixed per dataset.

### 4.2 New runtime-path helpers

Add to `src/driftsentinel/runtime_paths.py`:

```python
def runtime_dataset_policies_dir(catalog, schema, dataset_id, *, volume_name=DEFAULT_RUNTIME_VOLUME_NAME) -> str
def runtime_drift_policy_path(catalog, schema, dataset_id, *, volume_name=DEFAULT_RUNTIME_VOLUME_NAME) -> str
def runtime_benchmark_policy_path(catalog, schema, dataset_id, *, volume_name=DEFAULT_RUNTIME_VOLUME_NAME) -> str
```

The directory helper returns `<volume_root>/policies/<dataset_id>`. The file
helpers return `<volume_root>/policies/<dataset_id>/{drift,benchmark}_policy.yml`.

### 4.3 `connect` change — standardize upload basename

`src/driftsentinel/databricks/files.py:sync_files` writes drift policy to the
canonical filename instead of preserving local basename:

```python
if drift_policy_path:
   dest = runtime_drift_policy_path(catalog, schema, dataset_id, volume_name=volume_name)
    remote["drift_policy"] = upload_file(client, drift_policy_path, dest)
if benchmark_policy_path:
   dest = runtime_benchmark_policy_path(catalog, schema, dataset_id, volume_name=volume_name)
    remote["benchmark_policy"] = upload_file(client, benchmark_policy_path, dest)
```

### 4.4 `run` change — default + actionable failure

`src/driftsentinel/databricks/connect.py:run` resolves missing policy args:

1. If `drift_policy is None`, default to
   `runtime_drift_policy_path(catalog, schema, dataset_id, volume_name)`.
   Verify it exists on the volume via `ws.files.get_metadata(...)` (or
   `get_status`). Treat only Databricks `NotFound` /
   `ResourceDoesNotExist` failures as missing. If the file is absent, raise
   `ValueError` with the message:

   > `No drift policy registered for dataset '<dataset_id>'. Run
   > 'driftsentinel databricks connect --drift-policy <path>' to register one,
   > or pass '--drift-policy' explicitly.`

2. Same logic for `benchmark_policy`. The benchmark policy is **optional** at
   the orchestration layer; if the canonical file is absent and the operator
   did not pass `--benchmark-policy`, omit the parameter entirely (do not
   fail). Non-missing Files API errors must propagate instead of silently
   bypassing the benchmark stage. This preserves today's "intake + drift only"
   replay path.

3. Explicit `--drift-policy` / `--benchmark-policy` arguments always win and
   are passed through unchanged (no existence check — operator responsibility).

### 4.5 CLI help text

Update `src/driftsentinel/cli.py` `p_run.add_argument(...)` help text to read:

> `Remote drift policy path override (defaults to runtime-volume canonical
> location uploaded by 'connect')`

Same wording for `--benchmark-policy`.

## 5. Files Touched

| File | Change |
| --- | --- |
| `src/driftsentinel/runtime_paths.py` | Add dataset-scoped policy-path helpers |
| `src/driftsentinel/databricks/files.py` | Use canonical destination filenames in `sync_files` |
| `src/driftsentinel/databricks/connect.py` | Default + verify policy paths in `run`; reuse helpers |
| `src/driftsentinel/cli.py` | Help text update for `--drift-policy` / `--benchmark-policy` on `run` |
| `tests/test_databricks_connect.py` | New cases per §6 |
| `tests/test_databricks_files.py` | New module — canonical-naming coverage for `sync_files` |
| `tests/test_runtime_paths.py` | Cover the new policy-path helpers |

## 6. Validation

### 6.1 Unit Tests (`tests/test_databricks_connect.py`)

Mock `WorkspaceClient`. Validate the four cases from the issue:

1. **Both omitted, files present** — `run(...)` builds job params with
   `drift_policy_path` and `benchmark_policy_path` set to canonical runtime
   volume paths.
2. **Both explicit** — operator-provided paths win over defaults (no existence
   check performed on overrides).
3. **One of each** — explicit drift override + auto-resolved benchmark.
4. **Drift omitted, file missing** — raises `ValueError` with the exact
   actionable message from §4.4(1).
5. **Benchmark omitted, file missing** — `benchmark_policy_path` is **not**
   added to job params (graceful omission, no exception).
6. **`sync_files` canonical naming** — uploading `./local_filename.yml`
   produces remote path `<volume_root>/policies/<dataset_id>/drift_policy.yml`.
7. **Operational probe failures propagate** — auth/network/permission errors
   from the Files API do not get rewritten as missing policy files.
8. **Dataset isolation** — two datasets resolve to distinct remote policy
   paths under the shared runtime volume.

### 6.2 Required Local Checks

```bash
uv run ruff check .
uv run mypy src/driftsentinel tests
uv run pytest -k "connect or files or runtime_paths"
uv run pytest
```

### 6.3 Manual Replay Smoke Test (post-merge, optional)

```bash
uv run driftsentinel databricks connect --catalog <C> --dataset-id <D> \
  --drift-policy ./my_drift.yml --benchmark-policy ./my_bench.yml --wait
uv run driftsentinel databricks run --catalog <C> --dataset-id <D> --wait
```

Second command must succeed without `--drift-policy`/`--benchmark-policy`.

## 7. Acceptance Criteria

- [ ] `run` with both flags omitted resolves canonical policy paths and
      submits the job successfully when the volume contains them.
- [ ] `run` with explicit `--drift-policy` honors the override unchanged.
- [ ] `run` with explicit `--benchmark-policy` honors the override unchanged.
- [ ] Mixed (one explicit, one auto) works.
- [ ] Drift policy missing on volume raises `ValueError` with the exact
      actionable message specified in §4.4(1).
- [ ] Benchmark policy missing on volume omits the parameter (graceful).
- [ ] `connect` writes drift policy to
   `<volume>/policies/<dataset_id>/drift_policy.yml`
      regardless of local filename.
- [ ] `connect` writes benchmark policy to
   `<volume>/policies/<dataset_id>/benchmark_policy.yml` regardless of local filename.
- [ ] Non-missing Files API failures propagate without being rewritten as
   missing policy configuration.
- [ ] Unit tests cover the cases in §6.1.
- [ ] `make lint`, `make typecheck`, `make test` all pass.

## 8. Residual Risks

- **Backwards compatibility for existing volumes.** Volumes deployed by
  `connect` versions ≤ `0.4.x` may contain the policy under the local-file
   basename (e.g., `policies/my_drift.yml`). Volumes created by earlier branch
   revisions may also use the shared canonical filename without a dataset
   subdirectory. After this patch, `run` will look for
   `policies/<dataset_id>/drift_policy.yml` and may fail on those volumes.
   Mitigation: actionable error message tells the operator to rerun `connect`
   to refresh the policy under the canonical dataset-scoped name. Document in
   PR notes; flag in
  `docs/operations_guide.md` if the operator-facing impact is non-trivial.

## 9. Traceability

- DS-SRS: §CLI ergonomics; failure-closed orchestration.
- DS-SDD-001: §CLI Layer; §Runtime Volume Layout.
- DS-TP-001: §CLI tests; §Databricks integration tests.
- Issue #33 acceptance criteria mapped 1:1 to §7 above.
