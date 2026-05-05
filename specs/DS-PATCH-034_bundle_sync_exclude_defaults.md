# DS-PATCH-034 — Default `sync.exclude` for Local Build Artifacts

| Field | Value |
| --- | --- |
| Tracking issue | [Org-EthereaLogic/DriftSentinel#34](https://github.com/Org-EthereaLogic/DriftSentinel/issues/34) |
| Type | improvement |
| Area | `area:bundle` |
| Priority | p2 |
| Status | Planned |
| Owner | lead-software-engineer |
| Methodology precedence | FailLens_Core (fail-closed defaults), E62 (Databricks runtime path), DS-SDD-001 §Deployment Assets |

## 1. Problem Statement

A fresh `databricks.yml` syncs the entire repository to the workspace bundle
path. Operators staging local data files frequently exceed the Databricks
workspace per-file ceiling and surface this error during `apps deploy`:

> `File ... is larger than the maximum allowed file size of 52428800 bytes`

Concrete demo evidence: NYC Taxi parquet files (~48 MB each) staged under a
local `data/` directory broke `apps deploy` on first deploy in
`/Users/etherealogic-2/Dev/DriftSentinel_demo/DriftSentinel`. Adding an
explicit `sync.exclude` block to `databricks.yml` resolved the failure on the
next attempt.

The same default sync also pushes `__pycache__/`, `.venv/`, evidence dumps,
report artifacts, and tool caches that have no value in the workspace and
inflate deploy times.

## 2. Goal

Ship a default `sync.exclude` block in `databricks.yml` covering the local
artifacts that operators should never push to the workspace, and lock the
contract via a packaging test so future edits cannot regress the list.

## 3. Non-Goals

- Adding new bundle variables, targets, or runtime parameters.
- Changing the bundle directory layout, runtime volume, or job parameters.
- Modifying `.gitignore` (already covers most of these patterns; `sync.exclude`
  is a separate Databricks bundle concern).
- Documenting every Databricks bundle-sync edge case — only the canonical
  default exclusions and the rationale.

## 4. Design

### 4.1 Canonical exclusion list

`databricks.yml` adds a top-level `sync.exclude` block listing each pattern
on its own line. The order is deliberate (largest blast radius first):

| Pattern | Rationale |
| --- | --- |
| `/data/` | Top-level local dataset staging directory; can contain >50 MB files |
| `/evidence_pulled/` | Top-level operator-side dump of pulled evidence; never needed in the workspace |
| `/archive_exports/` | Top-level local archive exports of evidence or registry state |
| `/orphaned_state_backup/` | Top-level local backup of orphaned bundle state |
| `/report/` | Top-level append-only local evidence; canonical production surface lives in the runtime volume, not the workspace |
| `.venv/` | Python virtual environment; large and machine-specific |
| `**/__pycache__/` | Python bytecode caches anywhere in the tree |
| `.pytest_cache/` | Test runner cache |
| `.mypy_cache/` | Type-checker cache |
| `.ruff_cache/` | Linter cache |

The list intentionally mirrors and slightly extends the patterns named in
issue #34 acceptance criteria. `report/` is excluded because canonical
evidence in production lives in the Unity Catalog runtime volume; the local
`report/` directory is a development surface, not a deployment artifact.

### 4.2 `databricks.yml` shape

The new block is a sibling of `bundle:`, `include:`, `variables:`, and
`targets:`. Databricks Asset Bundles read the top-level `sync` mapping during
upload; patterns are gitignore-style and are honored in addition to the
implicit `.git/` exclusion that the CLI applies on its own.

```yaml
sync:
  exclude:
    - /data/
    - /evidence_pulled/
    - /archive_exports/
    - /orphaned_state_backup/
    - /report/
    - .venv/
    - "**/__pycache__/"
    - .pytest_cache/
    - .mypy_cache/
    - .ruff_cache/
```

### 4.3 Test contract

`tests/test_packaging.py` adds a single new test that loads `databricks.yml`
once and asserts each canonical pattern is present in `sync.exclude`. The
test fails closed if `sync` or `sync.exclude` is missing entirely. This
guarantees that any future edit to `databricks.yml` that drops or renames a
pattern is caught locally and in CI.

### 4.4 Documentation

`docs/deployment_guide.md` gains a short subsection under the existing
deployment section that:

1. Names the default `sync.exclude` patterns shipped in `databricks.yml`.
2. States the operational reason (50 MB workspace per-file ceiling, deploy
   time, audit-clean workspace).
3. Tells operators to add additional local-only paths under `sync.exclude`
   if they stage other large files.

No new top-level doc file is created. The existing deployment guide is the
canonical operator-facing surface.

## 5. Files Touched

| File | Change |
| --- | --- |
| `databricks.yml` | Add top-level `sync.exclude` block per §4.1–§4.2 |
| `tests/test_packaging.py` | New test asserting each canonical exclude pattern is present |
| `docs/deployment_guide.md` | Short subsection documenting the default exclusion list and rationale |
| `specs/DS-TM-001_Traceability_Matrix.md` | Append a row mapping DS-FR-002 / DS-SR-009 to this patch's verification surface |

No source code under `src/driftsentinel/` changes. No bundle variables,
resources, or job parameters change.

## 6. Validation

### 6.1 Unit test (new)

In `tests/test_packaging.py`, add `test_bundle_sync_excludes_default_artifacts`:

- Loads `databricks.yml` as YAML.
- Asserts the top-level `sync` key exists and is a mapping.
- Asserts `sync.exclude` is a list.
- Asserts the following patterns are each present in the list (order
  insensitive but exact-string match):
  `data/`, `evidence_pulled/`, `archive_exports/`,
  `orphaned_state_backup/`, `report/`, `.venv/`, `**/__pycache__/`,
  `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`.

### 6.2 Required local checks

```bash
uv run ruff check .
uv run mypy src/driftsentinel tests
uv run pytest -k packaging
uv run pytest
```

The packaging-scoped pytest invocation is the minimum bar for the change;
the full suite must pass before commit.

### 6.3 Manual deploy smoke test (post-merge, optional)

With a populated local `data/` directory containing a >50 MB file:

```bash
make bundle-validate CATALOG=<C> PROFILE=<P>
databricks bundle deploy -p <P> --target dev --var="catalog=<C>"
```

Both must succeed without the 50 MB ceiling error. This is operator-side
verification, captured in `report/` if performed.

## 7. Acceptance Criteria

- [ ] `databricks.yml` ships with `sync.exclude` containing each pattern
   listed in §4.1.
- [ ] The new packaging test passes locally and in CI.
- [ ] `docs/deployment_guide.md` documents the default exclusion list and
   the rationale (workspace 50 MB per-file ceiling, deploy hygiene).
- [ ] `specs/DS-TM-001_Traceability_Matrix.md` references this patch under
   the bundle/deployment row (DS-FR-002 / DS-SR-009).
- [ ] `make lint`, `make typecheck`, `make test` all pass.
- [ ] No existing test changes behavior; this is an additive change.

## 8. Residual Risks

- **Operator surprise.** A workspace that previously included `report/` or
  `data/` after deploy will no longer have them in subsequent deploys.
  Mitigation: documented in `docs/deployment_guide.md`; canonical evidence
  lives in the runtime volume, not the workspace.
- **Pattern drift.** Future contributors may add new local artifact
  directories without extending `sync.exclude`. Mitigation: the packaging
  test fails closed if any required pattern is removed; new patterns are
  reviewer judgment per CONTRIBUTING guidance.
- **Schema validation.** `databricks bundle validate` does not enforce the
  `sync.exclude` shape beyond YAML well-formedness; the packaging test is
  the structural contract.

## 9. Traceability

- DS-PRD: §Deployment Assets, §Operator-Friendly Bundle.
- DS-SRS: DS-FR-002 (deployable Databricks bundle), DS-SR-009 (bundle resource
  resolution).
- DS-SDD-001: §Deployment Assets, §Bundle Layout.
- DS-TP-001: §Packaging tests, §Bundle validation surface.
- Issue #34 acceptance criteria mapped 1:1 to §7 above.
