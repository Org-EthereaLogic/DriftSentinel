# DriftSentinel Repository Guidelines

Operational guardrails for AI coding agents working in DriftSentinel.

## Mission

Deliver a standalone Databricks application that unifies the Enterprise Data
Trust control patterns (intake certification, drift gating, control
benchmarking) with governance, traceability, and repository integrity preserved
from day one.

## Decision Order

When tradeoffs appear, resolve them in this order:

1. Correctness and safety of the change.
2. Evidence traceability for every claim.
3. Security and secret hygiene.
4. Simplicity and proportionality.
5. Reproducibility and operational reliability.

## Standard Workflow

Use `Plan -> Act -> Verify -> Report` for every substantive task.

### Plan

- Identify the task contract, scope boundaries, and acceptance criteria.
- Confirm whether the change belongs in this product repo or should remain in
  the planning scaffold or a sibling chapter.
- Read the governing docs and the relevant specs before editing.

### Act

- Implement the smallest change that satisfies the task.
- Preserve explicit failure behavior and evidence traceability.
- Keep sibling chapter logic as first-party code, not clone dependencies.

### Verify

- Run the required local quality checks.
- Confirm docs, configs, and reported behavior agree.
- Map each claimed acceptance criterion to explicit evidence.
- Mark unsupported claims as `unverified`, not `passed`.

### Report

- State changed files, outcome, and verification evidence.
- Separate measured facts from interpretation.
- Call out residual risks, blockers, or manual external steps explicitly.

## Required Pre-Read

Read these files before making policy, product, or reporting claims:

- `CLAUDE.md`
- `AGENTS.md`
- `CONSTITUTION.md`
- `DIRECTIVES.md`
- the relevant canonical `specs/*.md` files
- the `README.md` in the directory you are about to modify

## Source Precedence

Use sources in this order:

1. `specs/` in this repository
2. root governance docs in this repository
3. planning scaffold at `/Users/etherealogic-2/Dev/Databricks/specs/`
4. primary methodology references: FailLens_Core, E62, E63, ADWS_PRO
5. supporting examples: agentic_coding_template, themegpt-v2.0, chapter repos

## Non-Negotiable Constraints

- No fabricated test, benchmark, or integration claims.
- No secrets, credentials, or tokens in repository content.
- No placeholder markers in source, scripts, or canonical specs.
- No destructive modification of preserved evidence.
- No runtime dependency on sibling chapter repository clones.
- No speculative enterprise architecture without immediate need.
- Codacy, Codecov, and Snyk must be wired before substantive product code.

## Required Checks

- Placeholder scan across specs, .claude, CLAUDE.md, docs
- `uv run ruff check .`
- `uv run mypy src/driftsentinel tests`
- `uv run pytest`
- `databricks bundle validate` (when bundle surfaces exist)
