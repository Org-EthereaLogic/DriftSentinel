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
- Every status update pushed to Notion must be backed by repository evidence.
- If direct Notion mutation is unavailable, create a repo-backed sync payload
  under `report/` instead of fabricating an external write.
- Notion sync is non-blocking. A failed sync must not be reported as a
  successful live dashboard update.

## Fallback Payload

When direct update is unavailable, write a dated payload:

`report/YYYY-MM-DD-notion-sync-payload.md`

Include: target page URL, page ID, intended summary, evidence references,
current blockers, and explicit statement that the live dashboard was not
updated.
