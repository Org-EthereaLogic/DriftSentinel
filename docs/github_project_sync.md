# DriftSentinel GitHub Project Sync Policy

**Effective:** 2026-05-04 (replaces `notion_dashboard_sync.md` — see archived banner on the legacy Notion page).

## Verified Target

| Field | Value |
| --- | --- |
| Project URL | [DriftSentinel Roadmap](https://github.com/orgs/Org-EthereaLogic/projects/8) |
| Project ID | `PVT_kwDODUNeJc4BWsb9` |
| Project number | `8` |
| Owner | `Org-EthereaLogic` |
| Sprint cadence | 1 week (Iteration field, starts Mondays) |
| Repo | [`Org-EthereaLogic/DriftSentinel`](https://github.com/Org-EthereaLogic/DriftSentinel) |

## Field Schema

| Field | Type | Notes |
| --- | --- | --- |
| `Status` | Single-select | `Todo`, `In Progress`, `Done` (default 3 — expand later if needed) |
| `Iteration` | Iteration | 1-week sprints (Sprint 1 = `2026-05-04`) |
| `Priority` | Single-select | `P0 — Critical`, `P1 — High`, `P2 — Medium`, `P3 — Low` |
| `Title`, `Assignees`, `Labels`, `Milestone`, `Repository` | Built-in | Native GitHub Project fields |

## Label Taxonomy

Labels live in `Org-EthereaLogic/DriftSentinel` and apply to Issues + PRs.

- **`area:*`** — mirrors `src/driftsentinel/` subpackages plus build/docs surfaces:
  `area:cli`, `area:bundle`, `area:intake`, `area:drift`, `area:benchmark`, `area:evidence`, `area:orchestration`, `area:config`, `area:app`, `area:notebook`, `area:docs`, `area:demo`
- **`type:*`** — work classification:
  `type:bug`, `type:feature`, `type:improvement`, `type:refactor`, `type:chore`, `type:test`
- **`priority:p0`–`priority:p3`** — explicit triage signal (mirrors Project Priority field)
- **`demo:*`** — demo-related signal:
  `demo:nyc-taxi`, `demo:friction`
- Default GitHub labels (`bug`, `documentation`, `enhancement`, `good first issue`, `help wanted`, `question`, `wontfix`) remain available for backward compatibility.

## Governance Rules

- The GitHub Project is the canonical project-management surface. The repository code in this repo and the Project board are the two sources of truth; everything else is derivative.
- Every issue lives in the `Org-EthereaLogic/DriftSentinel` repo (no draft-only project items unless explicitly intentional).
- Every issue must carry at minimum: one `area:*` label, one `type:*` label, one `priority:p*` label, and Iteration/Status fields on the Project.
- Status transitions follow PR/commit evidence — do not move to `Done` without a merged PR or evidence link.
- `report/` records under this repo remain append-only (no overwrites of existing sync artifacts).
- The legacy Notion page (ID `4d85af16161b42ed92071933bc90fb10`) is read-only. Updates pushed there after 2026-05-04 are not authoritative.

## Sync Record

Create a timestamped record for every sync attempt:

`report/YYYY-MM-DDTHH-MM-SS-github-project-sync-record.md`

Include:

- Project URL + project number
- Local branch, commit SHA, validation results (`make lint`, `make typecheck`, `make test`, optional `make bundle-validate`)
- Issues opened / closed / re-labeled / re-prioritized in this sync
- Items moved between iterations
- Evidence references for each closure claim (commit SHA or merged PR)
- Any blockers, unknowns, or items that need human triage

## Sync Workflow (used by `/sync`)

1. **Pre-flight** — verify `gh auth status` and that `Org-EthereaLogic/DriftSentinel` is reachable.
2. **Read repo state** — `git log --oneline -10`, branch name, `make test` summary, open PRs.
3. **Reconcile open issues:**
   - For each open issue assigned to the current iteration: confirm a PR exists or move it to next iteration.
   - For each merged PR since the last sync: close the corresponding issue with the merge commit SHA in the close comment.
   - For each Notion-archive issue (`#13`–`#31`): leave closed; never reopen.
4. **Reconcile project fields:**
   - Issues with no `area:*` or `type:*` label → flag for human triage.
   - Issues with `priority:p0` not in current iteration → flag.
   - Issues with `Status: In Progress` whose linked branch has no commits in 7 days → flag.
5. **Write the sync record** under `report/` and commit it.

## Migration Notes (2026-05-04)

- 19 historical Notion tasks migrated to closed Issues `#13`–`#31` with `Migrated from Notion: <url>` provenance lines in each body.
- 10 demo-friction improvement issues created as `#32`–`#41`, all assigned to Sprint 1.
- Old `docs/notion_dashboard_sync.md` is preserved for traceability; superseded by this document.
- The `/sync` command's `Phase 4: Notion Sync` section is replaced by `Phase 4: GitHub Project Sync`. See `.claude/commands/sync.md`.
