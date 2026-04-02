# DS-IP-001-P4: Phase 4 — Databricks App UI Plan

| Field | Value |
| --- | --- |
| Document ID | DS-IP-001-P4 |
| Version | 0.1 |
| Status | Draft |
| Author | Anthony Johnson |
| Date | 2026-04-02 |
| Parent | DS-IP-001 Phase 4 |
| Depends on | Phase 3 (complete), bundle deploy/run proof (complete) |

## 1. Phase 4 Exit Criterion

> Operators onboard and review without editing notebooks.
> — DS-IP-001 Phase 4

One Databricks App, deployed through the existing bundle, provides three
operator-facing views: dataset registration, control execution status, and
evidence review. The App reads from the same first-party package code that
notebooks use. No new runtime dependencies beyond the Databricks Apps
framework (Gradio or Dash).

## 2. Constraints

| Constraint | Source | Impact |
| --- | --- | --- |
| Databricks Apps require a Premium workspace | [Databricks Apps docs](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/) | Free Edition cannot host the App; notebook path must remain functional |
| App must be defined in `app.yaml` or bundle `config`, plus `databricks.yml` | [DAB apps tutorial](https://docs.databricks.com/aws/en/dev-tools/bundles/apps-tutorial) | Bundle resource definition required alongside existing jobs/pipelines |
| App code runs in a managed container, not a cluster | [App runtime docs](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/app-runtime) | No PySpark; App reads via SQL Connector or REST, delegates logic to package |
| Resources (SQL warehouse, secrets) via `app.yaml` | [App resources docs](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/resources) | SQL warehouse ID must be a configurable resource, not hardcoded |
| DS-SNFR-005: Notebook-first for Free Edition | DS-SRS-001 | App is additive; notebook path cannot be removed or broken |
| Evidence is append-only | DS-SNFR-001 | App reads evidence but never modifies or deletes artifacts |

## 3. Architecture

### 3.1 New Surfaces

| Path | Purpose |
| --- | --- |
| `app/` | Databricks App source directory |
| `app/app.py` | App entry point (Gradio or Dash) |
| `app/app.yaml` | App runtime configuration, resource bindings |
| `app/requirements.txt` | App-specific pip dependencies |
| `resources/driftsentinel_app.yml` | DAB resource definition for the App |

### 3.2 Existing Surfaces Used (Read-Only)

| Surface | App Usage |
| --- | --- |
| `src/driftsentinel/config/loader.py` | `DatasetRegistry.load()` for registry display |
| `src/driftsentinel/evidence/writer.py` | `list_evidence()`, `load_evidence()` for evidence browsing |
| `src/driftsentinel/config/loader.py` | `check_policy_compatibility()` for policy validation display |
| `templates/*.yml` | Contract/policy template reference |

### 3.3 App Does NOT Do

- Execute intake, drift, or benchmark runs (that stays in notebooks/jobs)
- Write evidence artifacts
- Modify the dataset registry
- Access PySpark or cluster compute
- Replace the notebook path

### 3.4 Layer Diagram

```text
┌──────────────────────────────────────────┐
│  Databricks App (Gradio/Dash)            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │ Registry │ │ Run      │ │ Evidence │ │
│  │ View     │ │ Status   │ │ Explorer │ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ │
│       │             │             │       │
│  ┌────▼─────────────▼─────────────▼────┐ │
│  │  driftsentinel package (read-only)  │ │
│  │  config.DatasetRegistry.load()      │ │
│  │  evidence.list_evidence()           │ │
│  │  evidence.load_evidence()           │ │
│  └─────────────────────────────────────┘ │
└──────────────────────────────────────────┘
         │ (SQL Connector for table queries)
┌────────▼─────────────────────────────────┐
│  Unity Catalog (catalog.schema.tables)   │
│  Evidence directory (Volume or /tmp)     │
└──────────────────────────────────────────┘
```

## 4. Framework Decision

**Recommendation: Gradio**

| Factor | Gradio | Dash |
| --- | --- | --- |
| Databricks first-party support | Yes (app template) | Yes (app template) |
| Layout complexity needed | Low (tables, filters, JSON viewer) | Medium (more boilerplate) |
| Package size | Smaller | Larger (Flask dependency) |
| Interactive widgets (dropdowns, date pickers) | Built-in | Built-in |
| Learning curve for this scope | Lower | Higher |

Gradio is sufficient for the three views. If the App grows beyond Phase 4
scope, migration to Dash or a JS framework is possible later.

## 5. Views

### 5.1 Registry View

- Load the registry JSON from a configurable path (widget/env var)
- Display registered datasets as a table: dataset_id, contract_version, catalog, schema, table
- Show policy compatibility status for each dataset
- No write operations

### 5.2 Run Status View

- List recent evidence artifacts via `list_evidence()`
- Filter by dataset_id, run_kind, date range
- Show summary: run_id, dataset, kind, timestamp, verdict (extracted from payload)
- Click-to-expand for full evidence JSON

### 5.3 Evidence Explorer

- Browse evidence artifacts from the configured evidence directory
- Filter by dataset_id, run_kind, run_id, date range
- Display artifact metadata and full JSON payload
- Handle malformed files gracefully (show parse_error entries)

## 6. Implementation Phases

### 6.1 App Scaffold (WBS 3.1)

1. Create `app/` directory with `app.py`, `app.yaml`, `requirements.txt`
2. Add `resources/driftsentinel_app.yml` with DAB app resource definition
3. Update `databricks.yml` to include the app resource
4. Verify `databricks bundle validate` still passes with the app resource
5. Add `app/` to the repo taxonomy in DS-SDD-001 and README

### 6.2 Registry View (WBS 3.2)

1. Implement registry loading from a configurable path
2. Build the Gradio table display with dataset and policy summary
3. Test locally with a sample registry JSON

### 6.3 Run Status + Evidence Explorer (WBS 3.3)

1. Implement evidence listing with filter controls
2. Build the summary table with click-to-expand detail
3. Handle empty directories, malformed files, and missing filters
4. Test locally against evidence artifacts from `make test` or prior runs

### 6.4 Bundle Integration and Deployment Proof (WBS 3.4)

1. Create or update the app resource via `databricks bundle deploy`
2. Deploy and start the app runtime via `databricks apps deploy`
3. Confirm SQL warehouse resource binding if table queries are added
4. Run `databricks bundle destroy` after proof

### 6.5 Tests and Documentation (WBS 3.5)

1. Add `tests/test_app.py` for app layout, import hygiene, and no-write assertions
2. Update `tests/test_packaging.py` for app file expectations
3. Update `tests/test_scaffold_layout.py` for `app/` directory
4. Update `docs/operations_guide.md` and `docs/deployment_guide.md`
5. Update `README.md` and module READMEs

## 7. Acceptance Criteria

| ID | Criterion | Verification |
| --- | --- | --- |
| P4-AC-1 | A Gradio-based Databricks App exists under `app/` | File inspection |
| P4-AC-2 | The App is defined as a DAB resource in `resources/driftsentinel_app.yml` | Bundle validate passes |
| P4-AC-3 | Registry View displays registered datasets from a loaded registry JSON | Local app run + screenshot |
| P4-AC-4 | Run Status View lists and filters evidence artifacts | Local app run + screenshot |
| P4-AC-5 | Evidence Explorer shows full artifact detail with malformed-file handling | Local app run + test |
| P4-AC-6 | The App reads but never writes evidence or registry state | Code review + test assertion |
| P4-AC-7 | The notebook path remains fully functional | `make test` passes, no notebook regressions |
| P4-AC-8 | `make lint`, `make typecheck`, `make test` pass | CI green |
| P4-AC-9 | Bundle validates and the Databricks App deploys from the repo root with the app resource | `make bundle-validate` + `make app-deploy` + deploy proof |
| P4-AC-10 | The App does not introduce new runtime dependencies on sibling repos | Import scan |

## 8. Risks

| Risk | Mitigation |
| --- | --- |
| Free Edition workspace cannot host Apps | Notebook path remains primary; App is additive for Premium users |
| Trial workspace may lack Apps permission | Test locally first; deploy proof is best-effort on trial tier |
| Gradio version incompatibility with managed runtime | Pin version in `requirements.txt`; test against Databricks container |
| SQL Connector needed for table queries beyond evidence files | Defer table queries to Phase 4.1 if SQL warehouse setup adds complexity |
| App scope creep into control execution | App is read-only by design; execution stays in notebooks/jobs |

## 9. Out of Scope

- Running intake, drift, or benchmark controls from the App
- Writing or modifying evidence artifacts from the App
- Dataset registration through the App (stays in notebooks)
- Marketplace distribution (Phase 5)
- SQL warehouse table queries beyond evidence file reading (defer to 4.1 if needed)
- Custom styling, branding, or production UI polish

## 10. Dependencies

| Dependency | Status |
| --- | --- |
| Phase 3 multi-dataset registry | Complete |
| Phase 3 evidence lookup helpers | Complete |
| Bundle deploy/run proof | Complete (adb_dev) |
| Gradio package | Available on PyPI |
| Databricks Apps on workspace | Requires Premium tier; verify on trial |
