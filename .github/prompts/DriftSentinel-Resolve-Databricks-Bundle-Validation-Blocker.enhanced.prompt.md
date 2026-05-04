# Resolve Databricks Bundle Validation Blocker Before Phase 4

**Date:** 2026-04-02
**Prompt Level:** Level 3 (Troubleshooting Execution Prompt)
**Prompt Type:** Troubleshoot
**Complexity:** Moderate
Justification: This task spans existing deployment docs, bundle configuration, progress state, and external Databricks workspace validation, but it should not require product-code changes or new architecture.
**Model:** claude-sonnet-4-20250514
**Model Rationale:** The task requires multi-surface investigation, authenticated CLI diagnosis, evidence capture, and disciplined scope control, but not a large multi-file implementation.
**Assumption:** The immediate goal is to resolve the Databricks CLI authentication blocker and produce evidence-backed bundle validation status before starting Phase 4 Databricks App UI work.
**Path Placeholders:** Resolve `${REPO_ROOT}` to the current DriftSentinel checkout before using referenced repository paths; command snippets use `git rev-parse --show-toplevel` where they need the active checkout.

## Inputs Consulted

| Source | Key Takeaways |
| --- | --- |
| `${REPO_ROOT}/AGENTS.md` | Follow Plan -> Act -> Verify -> Report, read governing docs first, and treat bundle validation as a required check when bundle surfaces exist. |
| `${REPO_ROOT}/CLAUDE.md` | `make bundle-validate` is part of the core workflow and Phase 4 is the next implementation milestone after Phase 3. |
| `${REPO_ROOT}/CONSTITUTION.md` | Completion claims require evidence, secrets must remain outside repository content, and missing evidence blocks completion claims. |
| `${REPO_ROOT}/DIRECTIVES.md` | Specs are canonical, PASS claims must be evidence-backed, and report surfaces must remain truthful about unverified checks. |
| `${REPO_ROOT}/specs/DS-IP-001_Implementation_Plan.md` | Phase 4 is the Databricks App milestone and delivery rules explicitly forbid skipping evidence and verification gates. |
| `${REPO_ROOT}/specs/DS-BI-001_Build_Instructions.md` | Bundle validation must run with authenticated Databricks CLI and an explicit existing Unity Catalog catalog via `--target dev --var="catalog=..."`. |
| `${REPO_ROOT}/docs/deployment_guide.md` | The recommended deploy path is bundle validate -> deploy -> run, all parameterized by catalog and optional schema. |
| `${REPO_ROOT}/databricks.yml` | The bundle includes `resources/*.yml`, defines `catalog` and `schema` variables, and exposes `dev` and `prod` targets. |
| `${REPO_ROOT}/progress.json` | Phase 3 currently marks `bundle_validate` as `unverified` while lint, typecheck, tests, placeholder scan, and Snyk passed. |
| `${REPO_ROOT}/progress.txt` | The unresolved Databricks auth blocker has carried across prior phases and now affects confidence in bundle-facing notebook and resource changes. |
| `${REPO_ROOT}/Makefile` | `make bundle-validate` currently runs bare `databricks bundle validate`, which is less specific than the documented target-and-catalog flow. |

## Mission Statement

Resolve the Databricks CLI authentication blocker and produce evidence-backed validation status for `databricks bundle validate --target dev --var="catalog=<existing_uc_catalog>"` against a real workspace before any Phase 4 Databricks App UI implementation begins.

## Behavioral Controls

<investigate_before_answering>
Read every referenced file before making claims about bundle behavior, authentication setup, progress status, or milestone readiness. Do not infer Databricks configuration, workspace readiness, or CLI state without direct inspection.
</investigate_before_answering>

<default_to_action>
Execute the troubleshooting workflow, attempt the authenticated validation run, capture results, and update the evidence surfaces. Do not stop at advice unless an external credential or workspace permission blocker makes execution impossible.
</default_to_action>

<use_parallel_tool_calls>
Read repository instructions, progress files, and bundle configuration files in parallel during the investigation phase. Group independent diagnostics together when they can run safely in parallel.
</use_parallel_tool_calls>

<format_control>
Write all status reporting in concise engineering prose. Use tables for diagnostics and evidence only where they improve scanability. After each numbered instruction, include an italicized success signal.
</format_control>

## Technical Context

DriftSentinel has completed Phase 3 product work, including dataset-aware notebooks and Databricks bundle resources, but the project still lacks verified evidence that the Databricks Asset Bundle validates against a real workspace. This is the longest-running unverified item in `progress.json`, and the implementation plan explicitly forbids skipping verification gates before advancing to the next milestone.

The bundle surface is small and already defined: `databricks.yml` includes `resources/*.yml`, the `dev` target is the default validation target, and `catalog` is a required variable. The build instructions and deployment guide both specify the correct validation shape: authenticate the Databricks CLI through `.databrickscfg`, `DATABRICKS_CONFIG_PROFILE`, or `DATABRICKS_*` environment variables, then run `databricks bundle validate --target dev --var="catalog=<existing_uc_catalog>"`.

This task is a troubleshooting and verification milestone, not a product implementation milestone. The primary output is measured evidence that either:
1. The bundle validates successfully against a real workspace, or
2. It fails for a concrete, reproducible reason that is documented with the next required remediation.

## Problem-State Table

| Aspect | Current State | Target State |
| --- | --- | --- |
| Bundle validation status | `unverified` in `progress.json` | `passed` or explicitly documented failure with replayable evidence |
| Databricks CLI readiness | Local auth not configured or not confirmed | Authentication method verified and safe to use |
| Validation command fidelity | `make bundle-validate` runs generic command | Real validation executed with `--target dev --var="catalog=..."` |
| Phase 4 readiness | Databricks-facing UI planned on unverified foundation | Databricks deployment path verified or blocked by explicit evidence |
| Reporting integrity | Prior phases truthfully note the gap | Gap is closed or carried forward with concrete failure evidence |

## Hypothesis Table

| Hypothesis | Likelihood | Investigation Command | Expected if True |
| --- | --- | --- | --- |
| Databricks CLI is installed but not authenticated | High | `databricks auth profiles` or `databricks auth env` | CLI responds, but no usable profile or auth context is available |
| A valid auth profile exists, but `catalog` input has not been supplied | Medium | `DATABRICKS_CONFIG_PROFILE=<profile> databricks bundle validate --target dev --var="catalog=<catalog>"` | Validation proceeds past auth and fails only if the catalog is missing or invalid |
| Bundle configuration has a real defect unrelated to auth | Medium | `databricks bundle validate --target dev --var="catalog=<catalog>"` after auth is confirmed | Validation returns a parse, resource, or workspace error tied to bundle content |
| Local shell environment is masking a valid configuration | Low | `env | rg '^DATABRICKS_'` and `databricks auth env` | Missing or conflicting environment variables explain the failure |

## Pre-Flight Checks

1. **Confirm the workspace root and required files exist.**

   ```bash
   cd "$(git rev-parse --show-toplevel)" && test -f databricks.yml && test -f specs/DS-BI-001_Build_Instructions.md && test -f progress.json && echo "OK: bundle surfaces present"
   ```

   *Success: The command prints `OK: bundle surfaces present`.*

2. **Confirm the Databricks CLI is installed and reachable.**

   ```bash
   cd "$(git rev-parse --show-toplevel)" && databricks --version
   ```

   *Success: The command prints a Databricks CLI version string.*

3. **Inspect current Databricks environment variables without printing secrets.**

   ```bash
   cd "$(git rev-parse --show-toplevel)" && env | rg '^DATABRICKS_' | sed -E 's/(TOKEN|CLIENT_SECRET|PASSWORD)=.*/\1=REDACTED/'
   ```

   *Success: The command returns either a sanitized variable list or no output.*

4. **Determine available authentication contexts.**

   ```bash
   cd "$(git rev-parse --show-toplevel)" && databricks auth profiles
   ```

   *Success: The command lists zero or more profiles without exposing secret values.*

## Instructions

### Phase 1: Investigation and Authentication Diagnosis

1. **Read the current progress state before changing anything.**

   Review `${REPO_ROOT}/progress.json` and `${REPO_ROOT}/progress.txt` to confirm the current `bundle_validate` status and any prior explanation.

   *Success: You can quote the current status and the last recorded reason for the gap.*

2. **Inspect the bundle contract and documented validation path.**

   Read `${REPO_ROOT}/databricks.yml`, `${REPO_ROOT}/specs/DS-BI-001_Build_Instructions.md`, and `${REPO_ROOT}/docs/deployment_guide.md`.

   *Success: You can state the required target, required variable, and supported authentication mechanisms.*

3. **Diagnose the active CLI authentication method.**

   Run the pre-flight commands plus the strongest non-destructive auth diagnostic supported by the installed CLI, such as:

   ```bash
   cd "$(git rev-parse --show-toplevel)" && databricks auth env
   ```

   If `databricks auth env` is unavailable in the installed version, use the closest non-destructive auth inspection command provided by the CLI help output.

   *Success: You can identify whether auth is coming from a profile, environment variables, or is absent.*

   **Rationale:** The root blocker may be configuration rather than bundle content, so determine the active auth source before attempting remediation.

4. **Identify the profile and catalog inputs needed for a real validation run.**

   Determine the exact `DATABRICKS_CONFIG_PROFILE` to use, or confirm that direct environment-variable auth is active. Determine an existing Unity Catalog catalog name from the operator's configured environment, shell variables, or documented local setup. Do not invent a catalog name.

   *Success: You have a concrete auth context and a real catalog value, or you can state precisely which input is missing.*

   **Rationale:** `catalog` is required by the bundle contract, and fabricated inputs would create false evidence.

### Phase 2: Execute Bundle Validation

5. **Run the real bundle validation command with explicit target and catalog.**

   Use the documented command shape. Prefer the profile-qualified form when a profile is available:

   ```bash
   cd "$(git rev-parse --show-toplevel)" && DATABRICKS_CONFIG_PROFILE=<profile> databricks bundle validate --target dev --var="catalog=<existing_uc_catalog>"
   ```

   If environment-variable auth is active instead of a profile, omit `DATABRICKS_CONFIG_PROFILE` and use:

   ```bash
   cd "$(git rev-parse --show-toplevel)" && databricks bundle validate --target dev --var="catalog=<existing_uc_catalog>"
   ```

   Replace `<profile>` and `<existing_uc_catalog>` with real values discovered in Phase 1.

   *Success: The command returns either a successful validation result or a concrete, reproducible failure message.*

6. **If validation fails, classify the failure before making any edits.**

   Categorize the failure as one of: authentication, authorization, missing catalog, workspace permissions, bundle configuration defect, or CLI/version mismatch. Capture the exact failing command, the sanitized error output, and the one next action most likely to resolve it.

   *Success: The failure has a single primary classification and a replayable reproduction command.*

   **Rationale:** This is a troubleshooting prompt. The first obligation is to turn ambiguity into a precise blocker, not to widen scope into speculative fixes.

### Phase 3: Minimal Remediation If the Failure Is Local and In-Scope

7. **Apply only the smallest in-scope remediation that the evidence supports.**

   Allowed in-scope actions:
   - Export or switch to the correct local Databricks profile
   - Re-run the validation command with the correct `catalog` value
   - Update verification-oriented repo surfaces if the only defect is stale operator guidance

   Forbidden out-of-scope actions:
   - Product refactors under `src/driftsentinel/`
   - Feature work for Phase 4
   - Secret creation, secret rotation, or workspace-admin operations you cannot perform safely
   - Speculative changes to `databricks.yml` without validation evidence

   *Success: Any remediation stays tightly coupled to the observed failure and does not broaden into unrelated product work.*

8. **Re-run the same validation command after any remediation.**

   Use the identical command form from Step 5 so the before/after comparison remains valid.

   *Success: You obtain either a passing result or a narrower failure than before.*

### Phase 4: Evidence and Reporting Updates

9. **Update progress tracking to reflect measured reality.**

   If validation passes, update `${REPO_ROOT}/progress.json` so `bundle_validate` becomes `passed` and add a validation record with the exact command and outcome. If validation still fails, keep `bundle_validate` as `unverified` or change it to a clearer blocked state only if that state already exists in the project's progress vocabulary. Update `${REPO_ROOT}/progress.txt` with a concise factual note.

   *Success: Progress surfaces match the actual validation result and no claim exceeds the evidence.*

   **Rationale:** The standing problem is an evidence gap, so the fix is incomplete until the status surfaces reflect the measured outcome.

10. **Create or append an evidence artifact under `${REPO_ROOT}/report/`.**

   Record the date, command executed, auth method used at a high level, catalog value used, sanitized output summary, and final conclusion. Preserve append-only behavior; do not overwrite existing report files.

   *Success: A new or appended report artifact exists with enough detail for another operator to replay or understand the result.*

11. **Update documentation only if the evidence shows documentation drift.**

   If the validation succeeds only after using a command shape or prerequisite that the current docs do not state, update the minimal relevant documentation surface, most likely `${REPO_ROOT}/specs/DS-BI-001_Build_Instructions.md`, `${REPO_ROOT}/docs/deployment_guide.md`, or `${REPO_ROOT}/README.md`.

   *Success: Documentation changes, if any, are narrow, evidence-backed, and limited to operator guidance.*

### Phase 5: Verification and Quality Control

12. **Run focused verification for every repo file you edit.**

   At minimum, run the narrowest applicable validation for the touched surfaces. For progress or Markdown evidence/doc files, use a diff check plus any existing targeted tests if a change affects executable guidance. If you edit bundle-related docs or status files only, re-run the validated bundle command once more to confirm the recorded state remains current.

   *Success: Every edited file is covered by an executable or directly relevant verification action.*

13. **Run the required repository quality checks only if code or canonical docs changed.**

   If you modify canonical docs or bundle-facing repo guidance, run:

   ```bash
   cd "$(git rev-parse --show-toplevel)" && PATTERN='TO''DO|FIX''ME|TB''D|PLACE''HOLDER'; rg -n "$PATTERN" specs .claude CLAUDE.md docs
   ```

   If you modify executable bundle surfaces, also run:

   ```bash
   cd "$(git rev-parse --show-toplevel)" && uv run pytest tests/test_governance_guards.py -q
   ```

   *Success: The relevant follow-on checks pass or any failure is recorded with evidence.*

### Phase 6: Phase-Readiness Conclusion

14. **State whether the Phase 4 prerequisite is now resolved.**

   Conclude with one of the following evidence-backed outcomes:
   - `Resolved`: bundle validation passed against a real workspace
   - `Partially Resolved`: auth works but workspace/catalog permissions still block validation
   - `Unresolved`: auth or workspace access remains blocked and Phase 4 should not start

   *Success: The conclusion is binary enough to guide planning and is directly justified by the recorded evidence.*

## Guardrails

<guardrails>
- Do not claim bundle validation passed unless the authenticated `databricks bundle validate --target dev --var="catalog=..."` command actually succeeded.
- Do not print secrets, tokens, client secrets, or raw credentials into the terminal transcript, repository files, or report artifacts.
- Do not modify `src/driftsentinel/` or notebook logic unless the validation evidence proves a real bundle defect in those surfaces and the defect is required to complete this task.
- Do not start Phase 4 implementation work in this prompt.
- Do not overwrite files under `${REPO_ROOT}/report/`; preserve append-only evidence handling.
- Keep remediation proportional. Prefer environment correction, evidence capture, and narrow guidance fixes over speculative product changes.
</guardrails>

## Verification Checklist

- [ ] Databricks CLI presence was verified locally
- [ ] Authentication context was diagnosed without exposing secrets
- [ ] A real `catalog` value was identified or the missing input was explicitly documented
- [ ] `databricks bundle validate --target dev --var="catalog=..."` was executed against a real workspace
- [ ] The result was classified as pass or a concrete blocker with replayable evidence
- [ ] `progress.json` and `progress.txt` were updated if their recorded status changed or needed clarification
- [ ] An append-only evidence artifact was created or updated under `${REPO_ROOT}/report/`
- [ ] Any documentation change was minimal and evidence-backed
- [ ] The final report states whether Phase 4 is blocked, partially resolved, or unblocked

## Error Handling

| Error Condition | Resolution |
| --- | --- |
| `databricks: command not found` | Stop and report that the Databricks CLI is missing locally. Do not fabricate bundle validation status. |
| CLI installed but no auth context available | Record the missing auth blocker, identify the supported auth methods from docs, and stop short of false validation claims. |
| Auth works but the catalog is unknown | Determine whether a safe local source for the catalog exists. If not, report the exact missing operator input and keep the status unresolved. |
| Validation fails with permission or workspace access error | Record the exact permission blocker and preserve Phase 4 as blocked pending workspace access. |
| Validation fails with bundle configuration error | Capture the error, determine the smallest local fix surface, and repair only if the defect is directly evidenced and in scope. |
| Validation passes but progress/docs still say `unverified` | Update status and docs immediately so reporting matches measured evidence. |

## Out of Scope

- Implementing the Phase 4 Databricks App UI
- New product capabilities under `src/driftsentinel/`
- Broad refactors of notebooks, orchestration, or evidence subsystems
- Workspace-administrator changes outside the local operator's control
- Deploying or running jobs beyond what is required to prove bundle validation readiness

## Report Format

Provide the completion report in this order:

1. **Validation Outcome:** `Resolved`, `Partially Resolved`, or `Unresolved`
2. **Command Executed:** The exact validation command used, with secrets omitted
3. **Authentication Context:** Profile-based, environment-based, or missing
4. **Catalog Input:** The real catalog used, or the exact missing input
5. **Observed Result:** Pass or the primary failure classification with the key sanitized error text
6. **Files Updated:** Progress, report, docs, or `none`
7. **Verification Evidence:** The checks you ran after any edits
8. **Phase 4 Recommendation:** Start, defer pending one blocker, or remain blocked

## Alternative Solutions

1. **Profile-first remediation:** If multiple profiles exist, re-run validation under the intended development profile before changing any repo files. Pros: minimal change surface. Cons: depends on correct local profile setup.
2. **Environment-variable remediation:** If profile discovery is unreliable but `DATABRICKS_*` variables are already configured safely, validate with environment auth and document that context. Pros: avoids profile ambiguity. Cons: easier to misread shell state.
3. **Documentation-only closure:** If the only blocker is absent operator guidance and a successful validation is already reproducible locally, update build/deployment docs and progress evidence without touching product code. Pros: smallest repo change. Cons: only valid after a real successful run.
