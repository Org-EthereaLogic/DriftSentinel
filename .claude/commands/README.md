# .claude/commands/

Slash commands for the DriftSentinel product repository.

Each `.md` file is a reusable prompt intended to operationalize the canonical
`specs/` suite during implementation and maintenance.

## Available Commands

### Core Workflow

| Command | Purpose |
| --- | --- |
| `/prime` | Orient to the repository before acting |
| `/start` | Set up the local development environment and verify functionality |
| `/plan` | Create a structured implementation or design plan in `specs/` |
| `/implement` | Implement scoped work under the DriftSentinel spec contract |
| `/review` | Review changes against requirements, architecture, and acceptance criteria |
| `/verify` | Independently verify claims, code, configuration, or evidence surfaces |
| `/test` | Run the DriftSentinel validation suite and return structured results |
| `/audit` | Full governance, quality-control, and canonical docs audit |

### Issue and Branch Workflow

| Command | Purpose |
| --- | --- |
| `/feature` | Plan a new feature: scope it, decide placement, produce a specs/ plan |
| `/bug` | Plan a focused bug fix with root cause analysis and regression test |
| `/patch` | Create a focused patch plan with minimal, targeted changes |
| `/chore` | Execute low-risk maintenance under governance |
| `/classify_issue` | Classify a GitHub issue as `/chore`, `/bug`, or `/feature` |
| `/generate_branch_name` | Generate a valid git branch name from an issue number and title |

### Git and Release

| Command | Purpose |
| --- | --- |
| `/commit` | Generate and execute a scoped conventional commit |
| `/pull-request` | Create a GitHub PR after verifying all checks pass |
| `/git` | Perform git operations safely with protected-branch enforcement |

### Documentation and Maintenance

| Command | Purpose |
| --- | --- |
| `/doc-maintain` | Audit and update documentation for drift |
| `/document` | Generate implementation documentation in `specs/` |
| `/cleanup_workspace` | Safely clean generated local artifacts in dry-run or execute mode |
| `/sync` | Audit docs, validate, review git readiness, and handle Notion sync |

## Notes

- `specs/` is canonical.
- `CLAUDE.md` is the quick-reference starting point.
- Command surface aligned to the FailLens_Core primary reference pattern (21 commands).
- `/sync` follows the newer-repo Notion pattern: direct mutation only with
  exact targets, otherwise write a repo-backed sync payload.
