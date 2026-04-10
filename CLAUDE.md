# CLAUDE.md — DriftSentinel Product Repository Quick Reference

DriftSentinel is the Chapter 4 productization of the Enterprise Data Trust
portfolio. This repository contains the standalone application that unifies
intake certification, drift gating, and control benchmarking into a single
Databricks-deployable product.

## Methodology Precedence

When prior repository patterns conflict, use this precedence:

1. `FailLens_Core`
2. `E62_Live_Databricks_Bronze_execution`
3. `E63_Natural-fault_Bronze_validation`
4. `ADWS_PRO`
5. supporting examples from `agentic_coding_template`, `themegpt-v2.0`, and
   the older Databricks chapter repositories

## Command Shortlist

| Command | Use |
| --- | --- |
| `make sync` | Install runtime and development dependencies |
| `make lint` | Lint the repository with Ruff |
| `make typecheck` | Type-check with mypy |
| `make test` | Run the pytest suite |
| `make coverage` | Run tests with coverage reporting |
| `make bundle-catalog-check CATALOG=<catalog> [PROFILE=<profile>]` | Prove the selected Unity Catalog catalog exists for the current Databricks auth context |
| `make bundle-validate CATALOG=<catalog> [PROFILE=<profile>]` | Validate the Databricks Asset Bundle against an explicit catalog input |

### Core Workflow Commands (21 total)

| Command | Use |
| --- | --- |
| `/prime` | Orient to the repository before acting |
| `/start` | Set up local environment and verify project is functional |
| `/plan` | Create or update structured plans in `specs/` |
| `/implement` | Execute scoped work under the canonical contract |
| `/review` | Review work against requirements and architecture |
| `/verify` | Independently verify claims with evidence |
| `/test` | Run the full validation suite |
| `/audit` | Full governance and canonical docs audit |
| `/feature` | Plan a new feature with scope and placement check |
| `/bug` | Plan a focused bug fix with root cause analysis |
| `/patch` | Create a minimal targeted patch plan |
| `/chore` | Execute low-risk maintenance under governance |
| `/classify_issue` | Classify a GitHub issue as chore, bug, or feature |
| `/generate_branch_name` | Generate a valid branch name from an issue |
| `/commit` | Produce a scoped conventional commit |
| `/pull-request` | Create a GitHub PR after all checks pass |
| `/git` | Safe git operations with protected-branch enforcement |
| `/doc-maintain` | Audit and repair documentation drift |
| `/document` | Generate implementation documentation in `specs/` |
| `/cleanup_workspace` | Dry-run or execute safe workspace cleanup |
| `/sync` | Audit docs, validate, and handle Notion dashboard sync |

## Agent Surface

| Agent | Role |
| --- | --- |
| `lead-software-engineer` | Production implementation and spec-to-code translation |
| `sdlc-technical-writer` | Canonical SDLC documentation and traceability |
| `test-automator` | Test strategy, validation, and evidence QA |
| `python-pro` | Typed Python, packaging, uv workflows, PySpark integration |
| `ux-delight-specialist` | Gradio dashboard UI polish, layout, data presentation, empty states |

## External Coordination

| Surface | Target |
| --- | --- |
| Notion dashboard | [DriftSentinel Project Dashboard](https://www.notion.so/4d85af16161b42ed92071933bc90fb10) |
| Page ID | `4d85af16161b42ed92071933bc90fb10` |
| Sync policy | `docs/notion_dashboard_sync.md` |

## File Map

Every directory contains a `README.md` describing its contents.

| Path | Purpose |
| --- | --- |
| `specs/` | Canonical SDLC documents |
| `docs/` | Explanatory docs, deployment guide, Notion sync policy |
| `.claude/` | Claude Code configuration root |
| `.claude/commands/` | 21 reusable command prompts |
| `.claude/agents/` | 5 specialized subagent definitions |
| `.claude/hooks/` | Claude Code hook handlers and session logging |
| `.claude/settings.json` | Claude Code plugin configuration |
| `src/` | Top-level source directory (src-layout) |
| `src/driftsentinel/` | First-party product code |
| `src/driftsentinel/intake/` | Schema drift detection, contract validation (Chapter 1) |
| `src/driftsentinel/drift/` | Distribution drift detection and gate logic (Chapter 2) |
| `src/driftsentinel/benchmark/` | Control effectiveness benchmarking (Chapter 3) |
| `src/driftsentinel/evidence/` | Append-only evidence artifact writing |
| `src/driftsentinel/orchestration/` | Workflow sequencing for the control pipeline |
| `src/driftsentinel/config/` | Dataset contract and policy configuration |
| `src/driftsentinel/cli.py` | CLI entry point — `driftsentinel databricks {connect,run,status,sync,doctor}` |
| `src/driftsentinel/databricks/` | Databricks integration — workspace client, bundle ops, file sync, job execution |
| `app/` | Databricks App UI (Gradio) — operator dashboard for registry, run status, evidence |
| `assets/` | Project brand assets — source SVGs, favicons, icons, and social previews |
| `notebooks/` | Databricks onboarding, execution, and review notebooks |
| `resources/` | Databricks Asset Bundle pipeline and job definitions |
| `templates/` | Dataset contract, drift policy, and benchmark policy templates |
| `scripts/` | Operational helper scripts, including Databricks App deployment |
| `tests/` | Product test suite |
| `adws/` | Reserved for AI Developer Workflows |
| `report/` | Append-only evidence artifacts |

## Working Rules

- `specs/` is canonical over `docs/` when they diverge.
- `report/` is append-only — never overwrite or delete evidence.
- No runtime dependency on sibling chapter repository clones.
- Codacy, Codecov, and Snyk are pre-implementation gates.
- Notion is an external coordination surface only, never a runtime dependency.
- Separate measured facts from interpretation.
- No PASS claims without replayable evidence.
