# commit

Generate and execute a scoped conventional commit for the current diff.

## Variables

message_hint: $ARGUMENTS

## Instructions

- Run `git diff HEAD` to understand the current changes
- Generate a conventional commit: `<type>(<scope>): <description>`
- Scopes: `scaffold`, `specs`, `docs`, `claude`, `bundle`, `notebooks`,
  `config`, `intake`, `drift`, `benchmark`, `evidence`, `workspace`
- Present tense, 50 characters or less, no trailing period
- Stage only relevant files
- Never use `--no-verify`
- Never amend a prior commit

## Report

Return only the commit message used.
