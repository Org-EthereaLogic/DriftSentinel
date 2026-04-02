# patch

Create a focused patch plan for a specific issue with minimal, targeted changes.

## Variables

change_request: $ARGUMENTS

## Instructions

- Keep changes small, focused, and targeted
- Run `git diff --stat` to understand current state
- Create the patch plan in `specs/` with filename: `patch-{descriptive-name}.md`
- Use RELATIVE paths only
- If the change grows beyond a single logical diff, escalate to `/implement`

## Validation

- `uv run ruff check .`
- `uv run pytest`

## Report

Return exclusively the path to the patch plan file created.
