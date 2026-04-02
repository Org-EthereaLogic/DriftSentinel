# chore

Execute low-risk maintenance under DriftSentinel governance.

## Variables

task: $ARGUMENTS

## Workflow

1. Read `CLAUDE.md`, `AGENTS.md`, and the files you will modify.
2. Confirm the task is low-risk — no product module changes, no `specs/` edits,
   no `report/` evidence artifacts touched.
   - If the task would modify `specs/`, `report/`, or product control logic,
     stop and use `/plan` + `/implement` instead.
3. Apply the smallest possible change.
4. Run placeholder scan, `uv run ruff check .`, and `uv run pytest`.

## Report

Return changed files and verification status for each check.
