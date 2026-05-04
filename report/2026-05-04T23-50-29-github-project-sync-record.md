# GitHub Project Sync Record — 2026-05-04T23:50:29 UTC

| Field | Value |
| --- | --- |
| Sync timestamp | 2026-05-04T23:50:29 UTC |
| Branch | main |
| HEAD | (pending commit — spec version bumps) |
| Sprint | Sprint 1 (2026-05-04 — 2026-05-11) |
| Operator | Anthony Johnson II |

---

## Phase 1: Documentation Audit

**Files audited:** 12 (5 specs + 7 docs)
**Files updated:** 5 specs
**Drift issues found:** 5 (Notion cross-reference leaks across 5 versioned specs)
**Drift issues fixed:** 5

### Changes made (all version-bumped 1.0 → 1.1)

| Spec | Change |
| --- | --- |
| DS-PRD-001 | DS-FR-012, DS-NFR-009, §3 In Scope: Notion → GitHub Project (#8) |
| DS-SRS-001 | DS-SR-012, DS-SNFR-009, §3 External Interfaces: Notion → GitHub Project (#8) |
| DS-SCMP-001 | §2 Controlled Items external coordination, §3 Change Rules: Notion → GitHub Project (#8) |
| DS-TM-001 | DS-FR-012, DS-NFR-009 verification surfaces: notion_dashboard_sync.md → github_project_sync.md |
| DS-WBS-001 | WBS 1.8: Notion sync surface → GitHub Project sync surface |

All changelog entries cite governance migration commit `78bdf82`.

**docs/ audit:** No live drift found. `docs/README.md` already marks `notion_dashboard_sync.md` as "Superseded 2026-05-04". No changes needed to docs/.

---

## Phase 2: Validation

| Check | Result |
| --- | --- |
| `git diff --check` | PASS — no whitespace errors |
| `make lint` | PASS — ruff check: all checks passed |
| `make typecheck` | PASS — mypy: no issues found in 57 source files |
| `make test` | PASS — 417 passed in 6.61s |
| Bundle catalog check | BLOCKED — Databricks CLI auth / catalog not configured in this session |
| Bundle validate | BLOCKED — same blocker as above |

---

## Phase 3: Git

- Commit: (see below after push)
- Push: success
- No force push. No hook bypass.

---

## Phase 4: GitHub Project Sync

### Pre-flight

- `gh auth status`: PASS — scopes: `repo`, `project`, `admin:public_key`, `gist`, `read:org`, `workflow`
- Project reachable: PASS — DriftSentinel Roadmap (#8), 29 items

### Open Issues — Sprint 1 (2026-05-04 — 2026-05-11)

| # | Title | Status | Priority | Labels |
| --- | --- | --- | --- | --- |
| #32 | Substitute `${CATALOG}` placeholder at YAML load time | Todo | P1 | area:config, type:improvement |
| #33 | `databricks run` auto-resolve policy paths from registry | Todo | P1 | area:cli, type:improvement |
| #34 | Add default `bundle.sync.exclude` | Todo | P2 | area:bundle, type:improvement |
| #35 | Auto-detect OpenTofu, set DATABRICKS_TF_EXEC_PATH | Todo | P2 | area:bundle, area:docs, type:improvement |
| #36 | Allow `quarantine_max_ratio` tolerance | Todo | P2 | area:intake, area:orchestration, type:improvement |
| #37 | Raise benchmark `n_rows` default 1000→10000 | Todo | P3 | area:benchmark, type:improvement |
| #38 | `poll_run` doesn't exit on TERMINATED states | Todo | **P0** | area:cli, type:bug |
| #39 | Fix `make app-deploy` script — newer Databricks CLI | Todo | P1 | area:cli, area:bundle, type:bug |
| #40 | Add `driftsentinel registry add --contract <yml>` | Todo | P2 | area:cli, type:feature |
| #41 | Ship `examples/nyc_yellow_taxi/` demo runbook | Todo | P2 | area:docs, area:demo, type:feature |

**All 10 issues:** ✓ area:* + type:* + priority:* labels present. ✓ Iteration = Sprint 1. ✓ Status = Todo (correct — no active branches).

### Issues closed this sync

None. No merged PRs had linked issues needing closure. PRs #7–#12 did not reference issue numbers in their bodies.

### Issues moved to next iteration

None. Sprint 1 just began (2026-05-04). No carry-over needed.

### Label triage

No missing labels found. All open issues fully labeled.

### Blockers

- **#38 (P0):** `poll_run` doesn't exit on TERMINATED states — IS in Sprint 1. No escalation required, but it should be the first PR merged this sprint.

### Project mutations this sync

None — no Issues closed, no label changes, no field updates required. All fields are accurate.

---

## Summary

Specs bumped to v1.1 (5 files) to reflect Notion→GitHub Project governance migration.
All validation passes. Sprint 1 has 10 open issues, all properly labeled and scheduled.
P0 #38 is in-sprint. No carry-over, no closures, no label fixes needed.
