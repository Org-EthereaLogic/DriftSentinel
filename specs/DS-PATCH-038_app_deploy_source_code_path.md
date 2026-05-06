# DS-PATCH-038 — `apps deploy` Uses `--source-code-path` and Resolved `app.yml`

| Field | Value |
| --- | --- |
| Tracking issue | [Org-EthereaLogic/DriftSentinel#39](https://github.com/Org-EthereaLogic/DriftSentinel/issues/39) |
| Type | bug |
| Area | `area:bundle`, `area:cli` |
| Priority | p1 |
| Status | Planned |
| Owner | lead-software-engineer |
| Methodology precedence | FailLens_Core (explicit, actionable failure), E62 (Databricks runtime path), DS-SDD-001 §Application Layer / §Bundle Operations |

## 1. Problem Statement

`scripts/deploy_databricks_app.py` invokes `databricks apps deploy` with the
bundle flags `--target dev --var=catalog=<C>`:

```python
deploy_cmd = ["databricks", "apps", "deploy", *bundle_args]
```

Databricks CLI `v0.295.0` (verified 2026-05-04) removed `--target` and `--var`
from `apps deploy`. The current invocation fails with:

> `subprocess.CalledProcessError: Command '... apps deploy --target dev --var=catalog=<C>' returned non-zero exit status 1`

after `bundle deploy` completes successfully. Both `make app-deploy` and direct
`uv run python scripts/deploy_databricks_app.py …` are blocked. The CLI now
expects `apps deploy <APP_NAME> --source-code-path <workspace_path>` and reads
runtime configuration from an `app.yml` at the source-code-path root (or from
the App's `config` previously set by `databricks apps update`).

`EVIDENCE_LOG.md` Phase 11 records four consecutive deploy failures before the
operator manually wrote a real `app.yml` at the bundle workspace path and ran
`databricks apps deploy driftsentinel --source-code-path …`, which then
reached `state=RUNNING` on Free Edition.

## 2. Goal

Restore a single-command `make app-deploy CATALOG=<C> PROFILE=<P>` flow that
succeeds end-to-end on the current Databricks CLI by:

1. Resolving the bundle's app source-code-path from `bundle summary`.
2. Auto-generating a self-contained `app.yml` at that path, with the bundle
   resource's `command:` plus all env entries resolved against the bundle
   variables and resource bindings.
3. Calling `databricks apps deploy <APP_NAME> --source-code-path <PATH>` with
   no `--target` or `--var` flags.

## 3. Non-Goals

- Changing the bundle directory layout, runtime volume schema, or job
  parameters.
- Replacing the existing bundle resource definition in
  `resources/driftsentinel_app.yml` (it remains the source of truth for the
  App's command and env).
- Removing the local `app/app.yaml` fallback used for non-bundle local runs of
  `gradio app/app.py`.
- Pinning a Databricks CLI version; the script targets the current CLI shape
  (`v0.295.0`+) but does not enforce it.

## 4. Design

### 4.1 `apps deploy` invocation contract

The script no longer reuses `bundle_args` for `apps deploy`. The only flags
passed to `apps deploy` are:

| Flag | Source |
| --- | --- |
| `<APP_NAME>` (positional) | `summary.resources.apps.<app_key>.name` |
| `--source-code-path <PATH>` | `summary.resources.apps.<app_key>.source_code_path` |
| `-p <profile>` | from CLI `--profile` (when set) |

`--target` and `--var` are removed from this call. `bundle deploy` and `bundle
summary` continue to receive the existing `--target`/`--var` flags because
those subcommands still accept them.

### 4.2 Auto-generated `app.yml`

After `bundle deploy` and `bundle summary`, the script generates an `app.yml`
file from the summary and uploads it to `<source_code_path>/app.yml` via
`databricks workspace import --format AUTO --overwrite`.

The generated content is a strict YAML mapping of `command` and `env`:

```yaml
command:
  - gradio
  - app/app.py
env:
  - name: RUNTIME_VOLUME_PATH
    value: /Volumes/<catalog>/<schema>/<runtime_volume_name>
  - name: DATASET_PIPELINE_JOB_ID
    value: "<resolved_job_id>"
  - name: DRIFTSENTINEL_ALLOWED_PATH_ROOTS
    value: ""
```

The script generates the file only when the bundle resource defines a
`config.command` block (every other shape is a misconfiguration the script
must not paper over).

#### 4.2.1 Resolution rules

For each entry in `summary.resources.apps.<app_key>.config.env`:

| Input shape | Output |
| --- | --- |
| `{name, value}` | Pass through verbatim. |
| `{name, value_from: <ref>}` where `<ref>` is a `uc_securable` VOLUME in `config.resources` | `value: /Volumes/<catalog>/<schema>/<volume>` (parsed from `securable_full_name`, falling back to `summary.variables.{catalog,schema,runtime_volume_name}`). |
| `{name, value_from: <ref>}` where `<ref>` is a `job` in `config.resources` | `value: <job_id>` taken from the resource's resolved `id`, falling back to `summary.resources.jobs.<key>.id` when the embedded id is still a `${resources.jobs.<key>.id}` reference. |
| Unrecognized `value_from` | `value: ""` (empty string, not silent omission — the env var is preserved so the App still starts and the operator sees the gap). |

The empty-string fallback is intentional: missing references must surface as
an empty env var that the App's read-only paths handle, not as a missing key
that crashes the runtime.

### 4.3 `databricks.yml` `sync.exclude`

DS-PATCH-034 already ships the canonical `sync.exclude` block in
`databricks.yml`. No further change to this file is required by DS-PATCH-038;
the issue's third acceptance criterion is satisfied transitively by
DS-PATCH-034 and the existing packaging test
(`tests/test_packaging.py::test_bundle_sync_excludes_default_artifacts`).

### 4.4 Source-code-path resolution

The source-code-path is resolved from the bundle summary's
`resources.apps.<app_key>.source_code_path`, which the Databricks CLI populates
to the deployed workspace path (e.g.,
`/Workspace/Users/<user>/.bundle/driftsentinel/dev/files`). The script does
not hard-code a path or attempt to construct one from the user identity.

### 4.5 Failure behavior

- If `apps[<app_key>]` is missing from the summary: the script raises
  `SystemExit` with the exact missing key (existing behavior).
- If `source_code_path` is missing or empty in the summary: the script raises
  `SystemExit` rather than calling `apps deploy` with an empty path.
- If the `databricks workspace import` of `app.yml` fails: the script raises
  the underlying `CalledProcessError` and aborts before `apps deploy`.

No silent fallbacks, no demo-mode degradation.

### 4.6 Documentation surface

`docs/deployment_guide.md` is updated in two places:

1. The "Databricks App" section replaces the raw CLI sequence
   `databricks apps deploy -p <P> --target dev --var="catalog=<C>"` with the
   correct two-step form (write `app.yml`, then
   `apps deploy <name> --source-code-path <path>`) and points operators at
   `make app-deploy` as the supported wrapper.
2. The same section names the auto-generated `app.yml` and links to this
   patch document for full context.

The issue text references `docs/deployment.md`; this repository's canonical
deployment doc is `docs/deployment_guide.md`. The change lands in that file.

## 5. Files Touched

| File | Change |
| --- | --- |
| `scripts/deploy_databricks_app.py` | New helpers `_resolve_app_resource_values`, `_build_app_yaml_content`, `_upload_app_yaml`. Replace `apps deploy *bundle_args` with `apps deploy <app_name> --source-code-path <path> *app_api_args`. Generate and upload `app.yml` before each non-pending deploy. |
| `tests/test_app.py` | New `TestDeployScript` class covering env resolution, app.yml content shape, and the `apps deploy` command shape (no `--target`/`--var`). |
| `docs/deployment_guide.md` | Update the Databricks App section per §4.6. |
| `specs/DS-TM-001_Traceability_Matrix.md` | Append DS-PATCH-038 to the DS-FR-002 / DS-SR-009 row and add a 1.6 changelog entry on 2026-05-05. |

No source under `src/driftsentinel/` changes. No bundle resource definition,
runtime volume layout, or job parameter list changes.

## 6. Validation

### 6.1 Unit tests (new in `tests/test_app.py`)

- `test_apps_deploy_command_shape_uses_source_code_path` — asserts the deploy
  command list begins `["databricks", "apps", "deploy", "<app_name>",
  "--source-code-path", "<path>"]` and contains neither `--target` nor any
  `--var=` flag.
- `test_app_yaml_resolves_volume_value_from_reference` — feeds a fixture
  summary with a `value_from: runtime_volume` env entry and asserts the
  generated yaml resolves to `/Volumes/<catalog>/<schema>/<volume>`.
- `test_app_yaml_resolves_job_value_from_reference` — feeds a fixture summary
  with a `value_from: dataset_pipeline_job` env entry and asserts the
  generated yaml carries the resolved `id`.
- `test_app_yaml_passes_through_literal_value_entries` — `DRIFTSENTINEL_ALLOWED_PATH_ROOTS`
  with `value: ""` is preserved verbatim.
- `test_app_yaml_returns_none_when_no_command` — when the bundle resource has
  no `config.command`, the generator returns `None` and the script does not
  upload `app.yml`.

### 6.2 Required local checks

```bash
uv run ruff check .
uv run mypy src/driftsentinel tests
uv run pytest -k "test_app or test_packaging"
uv run pytest
```

The full suite must pass before commit. The `test_app or test_packaging`
slice is the minimum coverage bar for this patch.

### 6.3 Manual smoke test (post-merge)

On Databricks Free Edition with OpenTofu installed and an existing catalog:

```bash
make app-deploy CATALOG=<C> PROFILE=<P>
databricks apps get driftsentinel -p <P> -o json
```

Expected: the script reaches `App URL: https://…` without error, and
`apps get` reports `app_status.state=RUNNING` and
`active_deployment.status.state=SUCCEEDED`.

## 7. Acceptance Criteria

- [ ] `scripts/deploy_databricks_app.py` resolves the bundle's source-code-path
  from `bundle summary` and invokes
  `apps deploy <APP_NAME> --source-code-path <PATH>` with no `--target` or
  `--var` flags.
- [ ] When the bundle resource defines `config.command`, the script
  auto-generates an `app.yml` at the source-code-path root containing the
  command plus env entries resolved against the catalog/schema/volume bundle
  variables and any embedded `value_from` references.
- [ ] `databricks.yml` ships with the canonical `sync.exclude` block (already
  present from DS-PATCH-034; verified by the existing packaging test).
- [ ] `make app-deploy CATALOG=<C> PROFILE=<P>` succeeds end-to-end on
  Databricks Free Edition (manual smoke test recorded under §6.3).
- [ ] `docs/deployment_guide.md` documents the new flow and references this
  patch.
- [ ] `make lint`, `make typecheck`, `make test` all pass.
- [ ] `specs/DS-TM-001_Traceability_Matrix.md` references DS-PATCH-038 under
  the bundle/deployment row (DS-FR-002 / DS-SR-009).

## 8. Residual Risks

- **CLI shape drift.** A future Databricks CLI release may change the
  `apps deploy` flag set again. Mitigation: the script's deploy invocation is
  a single line; a future patch can update it without restructuring the rest
  of the script. The unit test pins the current command shape so regressions
  surface in CI.
- **Workspace import format.** `databricks workspace import --format AUTO`
  is documented but the precise behavior for arbitrary `.yml` files can vary
  across CLI minor versions. Mitigation: `--overwrite` is set so re-runs
  always converge; if a future CLI rejects AUTO for yaml, this patch's
  upload helper is the only change point.
- **Resource resolution gaps.** A bundle resource using a `value_from`
  reference whose binding shape this patch does not understand resolves to
  an empty string. Mitigation: §4.2.1 documents this fail-soft choice
  explicitly. The App still starts; the operator sees the gap in `apps get`
  env output.
- **Two-step rollout.** Operators who continue to call
  `databricks apps deploy -p <P> --target dev --var="catalog=<C>"` directly
  will still hit the underlying CLI failure. Mitigation: `make app-deploy`
  is the supported surface, and `docs/deployment_guide.md` is updated to
  remove the broken raw CLI sequence.

## 9. Traceability

- DS-PRD: §Deployment Assets, §Operator-Friendly Bundle.
- DS-SRS: DS-FR-002 (deployable Databricks bundle), DS-SR-009 (bundle resource
  resolution).
- DS-SDD-001: §Application Layer, §Bundle Operations, §Deployment Assets.
- DS-TP-001: §Packaging tests, §App test surface, §Bundle validation surface.
- Issue #39 acceptance criteria mapped 1:1 to §7 above.
- DS-PATCH-034 (sync.exclude defaults) is the upstream dependency for the
  third acceptance criterion.
