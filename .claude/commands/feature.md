# feature

Plan a new DriftSentinel feature: scope it, decide placement, produce a specs/
plan file.

## Variables

issue_or_description: $ARGUMENTS

## Instructions

- Parse `issue_or_description` for issue details or use as a plain description
- Research the codebase to understand existing patterns and architecture
- Create the plan in `specs/` with filename: `feature-{descriptive-name}.md`
- Use RELATIVE paths only

## Boundary Check

Before writing the plan, decide placement:

- This repo: intake controls, drift gates, benchmark evaluation, evidence
  surfaces, orchestration, notebooks, bundle configuration, dataset contracts
- Not this repo: sibling chapter internals, experiment-specific logic,
  FailLens runtime paths, UI/frontend scaffolding

If the feature belongs elsewhere, stop and explain why.

## Validation Commands

- placeholder scan
- `uv run ruff check .`
- `uv run pytest`
- `make bundle-validate CATALOG=<existing_uc_catalog> PROFILE=<profile>` (if
  bundle assets changed and Databricks auth plus catalog access are available)

## Report

Return exclusively the path to the plan file created.
