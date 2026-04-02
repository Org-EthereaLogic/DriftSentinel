# git

Perform git operations safely. Treats main and develop as protected.

## Variables

operation: $ARGUMENTS

## Supported Operations

- `status`, `add`, `commit`, `push`, `pull`, `fetch`, `sync`
- `branch create | switch | list | delete`
- `merge`, `rebase` (with conflict guidance)
- `diff`, `log`

## Safety Rules

- Never skip pre-commit hooks (`--no-verify` is prohibited)
- Never force-push without explicit user confirmation
- Never perform destructive resets without confirmation
- Protected branches (`main`, `develop`): block direct commits, confirm before push

## Report

Structured summary: Operation, Outcome, Actions, Next steps.
