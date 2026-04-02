# review

Review DriftSentinel changes against the canonical spec set.

## Variables

spec_or_scope: $ARGUMENTS

## Instructions

1. Read the relevant `specs/DS-*.md` files for the requested scope.
2. Review changed files against requirements, architecture, test-plan
   expectations, and traceability obligations.
3. Check for placeholder markers, unverifiable claims, drift between `docs/`
   and `specs/`, and broken repository taxonomy.
4. Run the applicable validation commands listed in `CLAUDE.md`.

## Report

Return a concise JSON report with `success`, `review_summary`, and
`review_issues`.
