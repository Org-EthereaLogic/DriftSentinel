---
description: Audit docs, validate, commit & push, and reconcile open GitHub Issues against the DriftSentinel Roadmap project.
---

# sync

Audit documentation, update for drift, commit changes, push to GitHub, and
reconcile project state with the GitHub Project (`DriftSentinel Roadmap`,
project #8).

## Variables

scope: $ARGUMENTS

## Workflow

### Phase 1: Documentation Audit & Update

- Run the `/doc-maintain` workflow internally
- Check for cross-reference leaks (stale project names, outdated URLs,
  references to other projects, references to the deprecated Notion dashboard)
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

### Phase 4: GitHub Project Sync

Reconcile open Issues against the `DriftSentinel Roadmap` Project (#8) and the
current iteration. See `docs/github_project_sync.md` for full policy.

**Evidence record:**

1. Create a new timestamped record under `report/` before finalizing the sync:
   `report/YYYY-MM-DDTHH-MM-SS-github-project-sync-record.md`
2. Never rewrite an earlier sync artifact
3. Each closure claim must cite the merging commit SHA or PR number
4. If GitHub read access or Project reachability cannot be verified, record the
   blocker explicitly instead of claiming sync succeeded

**Pre-flight:**

1. Verify GitHub read access with the integrated GitHub tool surface when
   available. Fallback: `gh auth status` with `repo` and `project` scopes only
   when the tool surface cannot answer the question.
2. Verify the Project is reachable with integrated GitHub project or repository
   tools when available. Fallback: `gh project view 8 --owner Org-EthereaLogic`
3. Read local project state: `git log --oneline -10`, current branch, test
   status, open PRs

**Reconcile Issues against the Project:**

1. **Close completed work.** For each merged PR since the last sync, close any
   linked Issues with the merge commit SHA in the close comment. Use
   `gh issue close <num> -R Org-EthereaLogic/DriftSentinel --reason completed
   -c "Closed by <pr-url> (commit <sha>)"`.
2. **Re-label drifting work.** For each open Issue:
   - Confirm one `area:*`, one `type:*`, and one `priority:p*` label exist;
     flag missing labels.
   - Confirm `Iteration` field is set; flag missing.
   - Confirm `Status` field reflects reality (`Todo` if no branch, `In Progress`
     if branch + commits exist, `Done` only after merge).
3. **Carry over unfinished iteration items.** Any Issue still open in the
   ending iteration should be moved to next iteration with a one-line carry-over
   note.
4. **Triage flags.** Surface any Issue with `priority:p0` not in the current
   iteration as a blocker for the operator to resolve manually.

**Push (write actions):**

Mutations are limited to:

- Issue close (with merging-commit citation)
- Issue label add/remove (only when audit found a clear discrepancy)
- Project field updates: `Status`, `Iteration`, `Priority`
- Iteration carry-over (move open Issues to next iteration)

Mutations NOT allowed in `/sync`:

- Creating new Issues (use `/feature`, `/bug`, `/chore`, `/patch` instead)
- Deleting Issues or Project items
- Changing labels on closed Issues
- Reopening any Issue (operator decision)

**Pull (read-only):**

1. List open Issues in the current iteration with integrated GitHub issue or
    repository tools when available. Fallback:
    `gh issue list -R Org-EthereaLogic/DriftSentinel --state open --json
    number,title,labels,projectItems`
2. List Issues with no `area:*` or `type:*` label (triage queue)
3. Report any open `priority:p0` Issues outside the current iteration

**GitHub access rule:**

- Use integrated GitHub tools for read-only inspection of Issues, PRs, labels,
   and Project items. Do not use `gh` only to inspect metadata.
- Reserve `gh` for mutations such as closing an Issue or for fallback cases
   where the GitHub tool surface cannot perform the required action.
- Do not retry unsandboxed for inspection-only steps. If a mutation requires
   `gh` and sandboxed auth fails because the home-directory config is
   unavailable, retry only that specific mutation unsandboxed and record it.

**Reference IDs:**

```text
Project URL:    https://github.com/orgs/Org-EthereaLogic/projects/8
Project ID:     PVT_kwDODUNeJc4BWsb9
Project number: 8
Owner:          Org-EthereaLogic
Repo:           Org-EthereaLogic/DriftSentinel
Sprint cadence: 1 week (Iteration field; Sprint 1 = 2026-05-04)
Field IDs:      Status=PVTSSF_lADODUNeJc4BWsb9zhR-gHc
                Iteration=PVTIF_lADODUNeJc4BWsb9zhR-gtA
                Priority=PVTSSF_lADODUNeJc4BWsb9zhR-g1o
```

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

### GitHub Project
- Open Issues in current iteration: N
- Issues closed this sync: N (with PR/commit citations)
- Issues moved to next iteration: N
- Issues with missing labels (triage): [list or "none"]
- Open priority:p0 outside current iteration (blocker): [list or "none"]
- Sprint window: {start} — {end}
```
