---
description: Audit docs, validate, commit & push, and sync with Notion using append-only evidence.
---

# sync

Audit documentation, update for drift, commit changes, push to GitHub, and sync
project state with Notion.

## Variables

scope: $ARGUMENTS

## Workflow

### Phase 1: Documentation Audit & Update

- Run the `/doc-maintain` workflow internally
- Check for cross-reference leaks (stale project names, outdated URLs,
  references to other projects)
- Update living artifacts (`docs/` numbered documents)
- Specs in `specs/` are versioned — never modify existing decisions without a
  version bump

### Phase 2: Validate

- Run `git diff --check` to verify no whitespace errors
- Run `make lint` to ensure linting passes
- Run `make typecheck` to ensure type-checking passes
- Run `make test` to ensure tests pass
- Run `make bundle-catalog-check CATALOG=<existing_uc_catalog> PROFILE=<profile>`
  and `make bundle-validate CATALOG=<existing_uc_catalog> PROFILE=<profile>`
  when Databricks CLI authentication is configured and a real catalog is
  available. If authentication or catalog access is unavailable, record the
  blocker explicitly instead of claiming bundle validation passed. Do not treat
  `bundle validate` alone as deployment proof.

### Phase 3: Commit & Push

- Clean up any remaining untracked files, then push or sync them to the GitHub
  remote following industry standards and best practices for commit conventions.
  Ensure full compliance with these standards to maintain the stability and
  integrity of the codebase.
- Safety: Never force push. Never skip hooks.

### Phase 4: Notion Sync

Sync project state between the local codebase and the Notion project dashboard.

**Evidence record:**

1. Create a new timestamped record under `report/` before finalizing the sync:
   `report/YYYY-MM-DDTHH-MM-SS-notion-sync-record.md`
2. Never rewrite an earlier sync artifact
3. Classify every external claim as `repo-verified`, `public-page-observed`,
   or `operator-reported`
4. If live Notion mutation cannot be verified in the current session, say so
   explicitly in the new record

**Pre-flight:**

1. Verify Notion MCP connectivity by fetching the project page
2. Read local project state: `git log --oneline -10`, open issues, current
   branch, test status

**Push to Notion (update project page):**

1. Fetch the DriftSentinel project page to read current state
2. Update the project page summary if implementation has progressed beyond
   what's documented
3. Create new tasks in the Tasks data source for any work items identified
   during the doc audit
4. Update task statuses (Not Started -> In Progress -> Done) based on git
   history and test results

**Pull from Notion (read-only):**

1. Query active tasks from the Tasks data source filtered to the DriftSentinel
   project
2. Query the current sprint from the Sprints data source
3. Report any Notion tasks that don't have corresponding local work (potential
   missed items)

**Notion Reference IDs:**

```text
Project Page:     https://www.notion.so/4d85af16161b42ed92071933bc90fb10
Tasks Source:     collection://1ec30351-c321-81ea-af83-000be461e73d
Sprints Source:   collection://1ec30351-c321-8178-b023-000b45e241f2
Projects Source:  collection://1ec30351-c321-815e-8107-000b9c5b09d6
Assignee:         user://1ebd872b-594c-81df-8377-0002fac140f6
```

**Task Schema (for creating/updating tasks):**

- `Task name` (title) — brief description
- `Status` — one of: `Not Started`, `In Progress`, `Done`, `Archived`
- `Assign` — array of user IDs (use Assignee above)
- `Due` — ISO-8601 date
- `Project` — relation to DriftSentinel project page URL
- `Sprint` — relation to current sprint (query Sprints Source for
  `Sprint status = "Current"`)

### Phase 5: Report

```text
=== Sync Report ===

### Documentation
- Files audited: N
- Files updated: N
- Drift issues found: N
- Drift issues fixed: N

### Validation
- Lint: pass/fail
- Typecheck: pass/fail
- Tests: pass/fail

### Git
- Commit: {hash} {message}
- Push: success/failure
- Sync record: {report path}

### Notion
- Project page: updated/unchanged
- Tasks created: N
- Tasks updated: N
- Active tasks pulled: N
- Current sprint: {sprint name} ({start} — {end})
- Unmatched Notion tasks: [list or "none"]
- Evidence classes: repo-verified/public-page-observed/operator-reported
```
