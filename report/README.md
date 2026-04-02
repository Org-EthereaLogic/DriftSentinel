# report

Append-only evidence artifacts from verification, sync, and control runs.

## Rules

- Evidence artifacts are append-only once generated.
- Do not overwrite or delete preserved evidence.
- Corrections, reruns, and reconciliations must use a new timestamped filename
  such as `report/YYYY-MM-DDTHH-MM-SS-notion-sync-record.md`.
- Notion sync records classify each claim as `repo-verified`,
  `public-page-observed`, or `operator-reported`.
- PASS claims require both machine-readable and human-readable evidence.
- Write a sync record for every Notion sync attempt. When no live dashboard
  mutation occurs, that record also serves as the repo-backed fallback payload.
