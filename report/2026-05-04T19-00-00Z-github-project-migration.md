# GitHub Project Migration — 2026-05-04T19:00Z

## Scope

Migrated DriftSentinel project management from Notion to GitHub. Canonical
surface is now [DriftSentinel Roadmap](https://github.com/orgs/Org-EthereaLogic/projects/8)
(Project #8) with 1-week iterations, Status/Iteration/Priority fields, and a
22-label taxonomy on `Org-EthereaLogic/DriftSentinel`.

## What changed

### GitHub artifacts created

| Artifact | Detail |
| --- | --- |
| Project #8 | `DriftSentinel Roadmap`, org-level under `Org-EthereaLogic`, ID `PVT_kwDODUNeJc4BWsb9` |
| Iteration field | 1-week sprints; Sprint 1 = `2026-05-04` |
| Priority field | `P0`/`P1`/`P2`/`P3` single-select |
| Labels | 22 new: `area:cli|bundle|intake|drift|benchmark|evidence|orchestration|config|app|notebook|docs|demo`, `type:bug|feature|improvement|refactor|chore|test`, `priority:p0|p1|p2|p3`, `demo:nyc-taxi|friction` |
| Migrated Issues | `#13`–`#31` (19 closed Issues, status Done) — full provenance in body via `Migrated from Notion: <url>` |
| New Issues | `#32`–`#41` (10 open improvement Issues from the 2026-05-04 NYC TLC demo retro), all in Sprint 1 with Priority set |

### Repo files updated

| File | Change |
| --- | --- |
| `CLAUDE.md` | External Coordination table replaced (GitHub Project canonical, Notion archived); `/sync` description updated; Working Rules note about canonical PM surface |
| `DIRECTIVES.md` | `IMP-003` rewritten: Notion Sync Truthful → GitHub Project Sync Truthful |
| `.claude/commands/sync.md` | Phase 4 fully rewritten: Notion Sync → GitHub Project Sync. Reference IDs updated. Allowed/disallowed mutations enumerated. |
| `.claude/commands/README.md` | `/sync` row + Notes section updated |
| `docs/github_project_sync.md` | **NEW** — canonical sync policy: field schema, label taxonomy, governance rules, sync workflow |
| `docs/notion_dashboard_sync.md` | Superseded banner added; preserved for historical traceability |
| `docs/README.md` | Doc index updated to reflect new canonical + superseded sync policies |
| `tests/test_scaffold_layout.py` | Added `github_project_sync.md` to required-doc parametrize list |

### Notion mutations

- Added a clear `ARCHIVED — see GitHub Project` banner to the top of the
  DriftSentinel Notion project page (`4d85af16161b42ed92071933bc90fb10`).
- The 19 task pages on Notion are NOT modified (left intact for historical
  reference). Going forward they are read-only.

## Validation

- `make lint` — `All checks passed!`
- `make test` — `417 passed in 6.79s` (+1 vs prior baseline; the added test is `test_doc_exists[github_project_sync.md]`)
- `make typecheck` — not re-run in this commit; deferred to first /sync after
  any source code change.
- `make bundle-validate` — not re-exercised; this migration touches no bundle
  resources.

## Out of scope (deferred)

- Spec files (`specs/DS-SCMP-001`, `DS-SRS-001`, `DS-TM-001`, `DS-WBS-001`,
  `DS-PRD-001`) still reference Notion. Per the canonical specs rule ("never
  modify existing decisions without a version bump"), these will be updated
  in a future PR with explicit version bumps.
- The historical `report/*notion-sync-record.md` artifacts are append-only
  and remain unchanged.
- `.github/prompts/` and `docs/prompts/` artifacts that reference Notion are
  prompt history; they are not actively executed and remain unchanged.

## Evidence

- Migration catalog: `~/Dev/DriftSentinel_demo/migration/notion_tasks.json`
  (19 source tasks) + `improvement_issues.json` (10 demo-retro improvements)
- Created-issues catalog: `~/Dev/DriftSentinel_demo/migration/notion_issues.json`
  + `improvement_issues_created.json`
- Project items map: `~/Dev/DriftSentinel_demo/migration/project_items.tsv`
  + `improvement_items.tsv`
- Project metadata: `~/Dev/DriftSentinel_demo/migration/project_meta.json`

## Reproducibility

A future operator can replay this migration against a different repo by:

1. Reading `migration/notion_tasks.json` for source task content
2. Replaying the label-creation block from this report's commit history
3. Recreating the org-level Project + 1-week Iteration + Priority fields
   via the GraphQL mutations preserved in this commit's diff context
4. Bulk-creating Issues from the JSON catalog with the same `area:*`/`type:*`
   labeling pattern
5. Adding each Issue to the Project via `gh project item-add`
6. Setting Status/Priority/Iteration field values via `updateProjectV2ItemFieldValue`
