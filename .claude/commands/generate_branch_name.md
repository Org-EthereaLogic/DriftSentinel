# generate_branch_name

Generate a valid git branch name from a GitHub issue number and title.

## Variables

issue_context: $ARGUMENTS

## Instructions

- Format: `<type>/<issue-number>-<slug>`
- `<type>`: `feat`, `fix`, or `chore` — infer from the title
- `<slug>`: lowercase, hyphens only, max 40 characters
- Only lowercase letters, digits, hyphens, and forward slashes

## Examples

- Issue 1 "Add intake control module" → `feat/1-add-intake-control-module`
- Issue 7 "Fix drift gate threshold" → `fix/7-fix-drift-gate-threshold`
- Issue 12 "Update CI pipeline" → `chore/12-update-ci-pipeline`

## Report

Return ONLY the branch name as a plain string.
