# bug

Plan a focused bug fix: reproduce, isolate root cause, propose minimal fix, add
regression test. Creates a spec file.

## Variables

issue_or_description: $ARGUMENTS

## Instructions

- Parse `issue_or_description` for issue details or use as a plain description
- Research the codebase to understand the bug's context and root cause
- Be surgical: solve the bug at hand, minimal changes only
- Create the plan in `specs/` with filename: `bug-{descriptive-name}.md`
- Use RELATIVE paths only

## Validation Commands

- `uv run ruff check .`
- `uv run pytest`

## Report

Return exclusively the path to the plan file created.
