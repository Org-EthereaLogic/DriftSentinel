# DriftSentinel Notion Dashboard Sync Policy

## Verified Target

| Field | Value |
| --- | --- |
| Dashboard URL | [DriftSentinel UMIF Entropy Gradient Drift Monitor](https://www.notion.so/DriftSentinel-UMIF-Entropy-Gradient-Drift-Monitor-4d85af16161b42ed92071933bc90fb10?source=copy_link) |
| Page ID | `4d85af16161b42ed92071933bc90fb10` |

## Governance Rules

- Treat the Notion page as an external project dashboard, not a runtime
  dependency.
- Direct updates are allowed only when the exact page URL or page ID is in
  current tool context or documented in the repository.
- Do not invent additional Notion database IDs, view IDs, task IDs, or page
  relationships.
- Every sync attempt writes a new timestamped record under `report/`. Never
  rewrite an existing sync artifact.
- Every status update pushed to Notion must be backed by repository evidence.
- Each Notion claim must carry one evidence class:
  - `repo-verified` for repository facts and direct tool output
  - `public-page-observed` for evidence gathered from the public page URL
  - `operator-reported` for external actions that were reported by an operator
    but not independently re-verified in the current session
- Public page reachability can confirm that the page URL resolves, but it does
  not prove task-level mutation history.
- If direct Notion mutation is unavailable, the sync record becomes the
  repo-backed fallback payload and must explicitly state that no live mutation
  was verified in the current session.
- Notion sync is non-blocking. A failed sync must not be reported as a
  successful live dashboard update.

## Sync Record

Create a timestamped record for every sync attempt:

`report/YYYY-MM-DDTHH-MM-SS-notion-sync-record.md`

Include:

- target page URL and page ID
- local branch, commit, and validation results
- intended or applied Notion mutations
- evidence references for each claim
- explicit evidence class for each external observation
- blockers, unknowns, and whether live mutation was verified
