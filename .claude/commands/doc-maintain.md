# doc-maintain

Audit and update DriftSentinel documentation for drift.

## Variables

scope: $ARGUMENTS

## Instructions

1. Inventory documentation in `specs/`, `docs/`, `CLAUDE.md`, `.claude/commands/`,
   `.claude/agents/`.
2. Treat `specs/` as canonical.
3. Check for stale paths, inconsistent terminology, missing traceability
   updates, and unverifiable claims.
4. Apply targeted fixes without rewriting accurate sections.
5. Re-run validation commands from `CLAUDE.md`.

## Report

Return a short JSON summary: audited files, updated files, deferred drift issues.
