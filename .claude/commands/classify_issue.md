# classify_issue

Classify a GitHub issue as /chore, /bug, or /feature.

## Variables

issue_context: $ARGUMENTS

## Instructions

- Parse `issue_context` — issue number, title, and body excerpt
- `/chore` — maintenance, dependency updates, CI, refactoring, docs, config
- `/bug` — defects, incorrect behavior, failures, regressions
- `/feature` — new capabilities, modules, enhancements
- When ambiguous, prefer `/feature`

## Report

Return ONLY one of: `/chore`, `/bug`, `/feature`
