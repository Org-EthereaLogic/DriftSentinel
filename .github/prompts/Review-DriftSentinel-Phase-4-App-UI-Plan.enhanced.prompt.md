# Review DriftSentinel Phase 4 App UI Plan Before Implementation

**Date:** 2026-04-02
**Prompt Level:** Level 3 (Task Execution Prompt)
**Prompt Type:** Research
**Complexity Classification:** Moderate — this review spans one new implementation-plan document, multiple canonical spec surfaces, and verification of named package/test anchors before any implementation begins. No product code changes are required, but the review must reconcile plan claims against specs, repository rules, and the current package boundaries.
**Model Recommendation:** `claude-sonnet-4-20250514` — use the balanced model tier because this is a cross-document, evidence-backed review that requires accurate comparison, scoped judgment, and grounded findings rather than broad implementation.
**Assumption:** Interpret “the plan is ready for your review before implementation begins” as a read-only readiness review of the Phase 4 plan in the current repository. Do not implement the app, edit the plan, or expand scope into Phase 4 execution unless the user explicitly asks for follow-on changes after the review.
**Path Placeholders:** Resolve `${REPO_ROOT}` to the current DriftSentinel checkout and `${VSCODE_USER_PROMPTS_FOLDER}` to the local VS Code prompt folder before using referenced paths.

## Inputs Consulted

| Source | Key Takeaways |
|--------|---------------|
| Source prompt | The task is to review `specs/DS-IP-001-P4_Phase_4_App_UI_Plan.md` before implementation begins, with key decisions already stated: Gradio, three read-only views, additive notebook path, bundle integration, and five implementation phases. |
| `${VSCODE_USER_PROMPTS_FOLDER}/Enhance Prompt workflow.prompt.md` | Enhanced prompts must be self-contained, phased, grounded, imperative, and include verification, guardrails, and explicit success signals. |
| `${REPO_ROOT}/AGENTS.md` | Use `Plan -> Act -> Verify -> Report`, preserve evidence traceability, and avoid unsupported claims. |
| `${REPO_ROOT}/CLAUDE.md` | `specs/` is canonical, Phase 4 is a Databricks App surface, and standard verification commands are `make lint`, `make typecheck`, `make test`, and bundle validation commands. |
| `${REPO_ROOT}/CONSTITUTION.md` | Safety, evidence traceability, security hygiene, simplicity, and reproducibility govern all decisions; missing evidence blocks completion claims. |
| `${REPO_ROOT}/DIRECTIVES.md` | Specs are canonical, evidence artifacts are append-only, PASS claims require explicit evidence, and quality-control surfaces must already exist. |
| `${REPO_ROOT}/.github/instructions/codacy.instructions.md` | Repository-level quality instructions apply when edits happen, but this task should remain read-only unless the user later requests changes. |
| `${REPO_ROOT}/README.md` | The repository already ships notebook and bundle deployment paths and frames DriftSentinel as a Databricks-deployable product with evidence-backed verification. |
| `${REPO_ROOT}/specs/DS-IP-001_Implementation_Plan.md` | Phase 4 is explicitly “Databricks App,” with the exit criterion “operators onboard and review without editing notebooks,” and it must not collapse into earlier phases. |
| `${REPO_ROOT}/specs/DS-IP-001-P4_Phase_4_App_UI_Plan.md` | The proposed plan introduces `app/`, a Databricks App resource, three operator-facing views, Gradio as the recommended framework, read-only boundaries, deploy proof, and tests/docs updates. |
| `${REPO_ROOT}/specs/DS-PRD-001_Product_Requirements_Document.md` | The product must preserve notebook-first evaluation, bundle deployment, explicit failure behavior, evidence traceability, and human-readable operator review surfaces. |
| `${REPO_ROOT}/specs/DS-SRS-001_Software_Requirements_Specification.md` | The repository must remain notebook-first for Free Edition, append-only for evidence, free of sibling runtime dependencies, and aligned with existing external interfaces. |
| `${REPO_ROOT}/specs/DS-TP-001_Test_Plan.md` | Phase completion requires tests aligned with canonical specs and replayable evidence, not only narrative justification. |
| `${REPO_ROOT}/specs/DS-TM-001_Traceability_Matrix.md` | Requirements must trace to concrete spec and verification surfaces; operator review surfaces and Free Edition compatibility are already governed. |
| `${REPO_ROOT}/src/driftsentinel/config/loader.py` | `DatasetRegistry.load()` and `check_policy_compatibility()` already exist as first-party config surfaces that the plan can legitimately reuse. |
| `${REPO_ROOT}/src/driftsentinel/evidence/writer.py` | `list_evidence()` and `load_evidence()` already exist for evidence browsing, including malformed-file handling and filterable metadata summaries. |
| `${REPO_ROOT}/src/driftsentinel/orchestration/runner.py` | `run_dataset_pipeline()` exists, which matters when judging whether the proposed app remains read-only and additive rather than becoming an execution surface. |
| `${REPO_ROOT}/tests/README.md` | The current test suite already includes packaging, registry, evidence lookup, and dataset orchestration tests that the plan’s verification section should account for. |

## Mission Statement

Review `specs/DS-IP-001-P4_Phase_4_App_UI_Plan.md` against canonical DriftSentinel specs, repository directives, and current first-party package/test anchors, then produce a severity-ordered readiness assessment that identifies blocking gaps, contradictions, and missing verification before Phase 4 implementation starts.

## Behavioral Controls

<investigate_before_answering>
Read every document and code surface you rely on before making claims about it. If the plan references an existing package helper, test surface, or deployment behavior, verify that the named surface exists and supports the claimed role before accepting the plan.
</investigate_before_answering>

<default_to_action>
Perform the review. Do not stop at describing how a review could be done, and do not switch into implementation or speculative redesign.
</default_to_action>

<use_parallel_tool_calls>
Read the plan, canonical specs, and named code anchors in parallel whenever possible. Compare multiple sources directly instead of reviewing them one at a time and relying on memory.
</use_parallel_tool_calls>

<format_control>
Report findings first, ordered by severity. Use markdown headings, tables for comparisons, fenced code blocks with language identifiers, and concise prose. After every action step, include an italicized success signal. Use action verbs such as “evaluate,” “assess,” “consider,” or “determine.”
</format_control>

## Technical Context

Phase 4 is not a greenfield backend effort. The current repository already contains the package anchors that the proposed Databricks App would sit on top of.

| Surface | Current Repository Reality | Review Relevance |
|--------|----------------------------|------------------|
| `specs/DS-IP-001_Implementation_Plan.md` | Phase 4 is explicitly a Databricks App phase with an operator onboarding/review outcome. | The plan must align with this phase boundary and not pull execution concerns forward. |
| `specs/DS-IP-001-P4_Phase_4_App_UI_Plan.md` | Proposes Gradio, three views, read-only boundaries, app bundle resource wiring, and deploy proof. | This is the document under review. |
| `src/driftsentinel/config/loader.py` | Registry loading and policy compatibility checks already exist. | The plan should reuse these surfaces accurately and avoid inventing a parallel registry abstraction inside the app. |
| `src/driftsentinel/evidence/writer.py` | Evidence listing and single-artifact loading already exist with filter metadata and malformed-file handling. | The plan should rely on these read-only helpers instead of proposing new evidence parsing logic in the UI layer. |
| `src/driftsentinel/orchestration/runner.py` | Dataset-aware execution exists in package code. | The review must confirm the plan preserves the stated read-only boundary and does not drift toward control execution from the app. |
| `tests/README.md` | The suite already includes packaging, registry, evidence lookup, and dataset orchestration coverage. | The plan’s proposed tests should fit the real test inventory and avoid missing obvious verification anchors. |

Evaluate the plan on five axes:

| Axis | What To Check |
|------|---------------|
| Canonical alignment | Does the plan match Phase 4 intent in `specs/`, especially notebook-first Free Edition, append-only evidence, and bundle deployment surfaces? |
| Internal consistency | Do the plan’s own sections agree with each other on whether the app is read-only, whether dataset registration is in scope, and what the three views actually do? |
| Implementation realism | Are the proposed files, resource surfaces, package APIs, and runtime assumptions realistic for the current repository and Databricks Apps constraints? |
| Verification sufficiency | Are acceptance criteria and test/docs tasks specific enough to prove readiness without fabricated claims? |
| Scope control | Does the plan avoid turning the app into a new execution, write, or backend orchestration layer? |

## Problem-State Table

| Aspect | Current State | Target State |
|--------|---------------|--------------|
| Review request | High-level instruction to “review the plan before implementation begins” | Self-contained review workflow with explicit sources, checks, and deliverables |
| Canonical grounding | Plan decisions are summarized, but review criteria are not yet spelled out | Reviewer compares the plan against specs, directives, and current code anchors directly |
| Output shape | No required structure for findings, questions, or verdict | Findings-first report with severity, evidence, and readiness recommendation |
| Verification | No explicit pre-flight or audit commands | Copy-pasteable commands and source checks confirm the review is grounded |
| Scope boundary | Easy to drift into implementation commentary or redesign | Read-only assessment focused on readiness, contradictions, missing details, and traceability |

## Research Criteria

| Criterion | Weight | Scoring Method |
|-----------|--------|----------------|
| Canonical spec alignment | High | Confirm each major plan decision agrees with `specs/` or flag the mismatch explicitly |
| Internal consistency | High | Identify contradictions inside the plan itself, especially around read-only scope and dataset registration responsibilities |
| Reuse of first-party surfaces | High | Verify named package helpers and test anchors exist and are used appropriately by the plan |
| Verification completeness | High | Determine whether acceptance criteria and test tasks can produce replayable evidence rather than narrative-only confidence |
| Databricks deployment realism | Medium | Assess Premium workspace assumptions, app container constraints, bundle resource wiring, and any SQL warehouse/resource binding claims |
| Scope proportionality | Medium | Determine whether the plan stays additive and avoids speculative architecture or UI-first overreach |

## Decision Matrix Template

| Outcome | Criteria |
|---------|----------|
| Ready | No blocking contradictions or missing prerequisites; only minor clarifications remain |
| Ready With Changes | Implementation can start after specific non-blocking edits or clarifications are made to the plan |
| Not Ready | One or more blocking issues would make implementation ambiguous, misleading, or non-compliant with canonical specs |

## Pre-Flight Checks

1. **Verify that the plan and canonical review inputs exist before you start.**

   ```bash
   cd "$(git rev-parse --show-toplevel)" && test -f specs/DS-IP-001-P4_Phase_4_App_UI_Plan.md && test -f specs/DS-IP-001_Implementation_Plan.md && test -f specs/DS-PRD-001_Product_Requirements_Document.md && test -f specs/DS-SRS-001_Software_Requirements_Specification.md && test -f specs/DS-TP-001_Test_Plan.md && test -f specs/DS-TM-001_Traceability_Matrix.md && echo "phase4 review inputs present"
   ```

   Expected: `phase4 review inputs present`.

   *Success: the canonical review set exists and the task can proceed without guessing missing sources.*

2. **Verify that the plan’s named package anchors exist in the current codebase.**

   ```bash
   cd "$(git rev-parse --show-toplevel)" && rg -n "class DatasetRegistry|def load\(cls, path: str \| Path\) -> DatasetRegistry|def check_policy_compatibility|def list_evidence|def load_evidence|def run_dataset_pipeline" src/driftsentinel
   ```

   Expected: matches in `src/driftsentinel/config/loader.py`, `src/driftsentinel/evidence/writer.py`, and `src/driftsentinel/orchestration/runner.py`.

   *Success: the review is grounded in real implementation anchors rather than hypothetical surfaces.*

3. **Verify that the current test inventory already contains the obvious neighboring verification surfaces.**

   ```bash
   cd "$(git rev-parse --show-toplevel)" && rg -n "test_scaffold_layout|test_packaging|test_registry|test_evidence_lookup|test_dataset_orchestration" tests
   ```

   Expected: matches in the test suite or `tests/README.md`.

   *Success: you can judge the plan’s proposed verification tasks against the actual repository test surface.*

## Instructions

### Phase 1: Establish The Review Baseline

1. **Read the full plan and its governing comparison set in parallel.**

   Read `specs/DS-IP-001-P4_Phase_4_App_UI_Plan.md`, `specs/DS-IP-001_Implementation_Plan.md`, `specs/DS-PRD-001_Product_Requirements_Document.md`, `specs/DS-SRS-001_Software_Requirements_Specification.md`, `specs/DS-TP-001_Test_Plan.md`, `specs/DS-TM-001_Traceability_Matrix.md`, `AGENTS.md`, `CLAUDE.md`, `CONSTITUTION.md`, and `DIRECTIVES.md` before issuing findings.

   *Success: you can restate the authoritative Phase 4 goal, the relevant non-functional constraints, and the review standard without relying on the plan alone.*

2. **Read the named implementation anchors and nearby verification surfaces before accepting plan reuse claims.**

   Inspect `src/driftsentinel/config/loader.py`, `src/driftsentinel/evidence/writer.py`, `src/driftsentinel/orchestration/runner.py`, and `tests/README.md`.

   *Success: you can verify whether the plan’s proposed app views and tests actually line up with the existing first-party code and test boundaries.*

3. **Build a simple traceability map from plan sections to canonical requirements and verification surfaces.**

   Create a table that links each major plan decision or acceptance criterion to the governing spec line or package/test surface that supports it.

   *Success: every accepted claim in the plan has an explicit source, and unsupported claims are easy to spot.*

   **Rationale:** DriftSentinel requires evidence-backed claims; a plan review is not complete if it only sounds plausible.

### Phase 2: Evaluate Plan Quality And Readiness

4. **Assess internal consistency inside the plan before you compare it to external sources.**

   Check whether the plan uses consistent scope language across the exit criterion, the three-view description, the “App Does NOT Do” section, implementation phases, acceptance criteria, and out-of-scope list.

   *Success: you can state clearly whether the plan is internally coherent or contains contradictory direction that would confuse implementation.*

5. **Assess canonical alignment against repository rules and product constraints.**

   Evaluate whether the plan preserves notebook-first Free Edition support, append-only evidence handling, no sibling runtime dependency, bundle deployment surfaces, and truthful evidence-backed verification.

   *Success: you can identify which parts of the plan align cleanly with canonical rules and which parts drift from them.*

6. **Assess whether the proposed app surface remains additive and read-only in practice, not only in wording.**

   Compare the plan’s view design and implementation phases against the existing execution and evidence-writing package surfaces. Treat any drift toward control execution, registry mutation, or evidence writes from the app as a scope or architecture finding.

   *Success: you can state whether the app plan truly stays on the operator-review side of the boundary.*

   **Rationale:** Phase 4 is intentionally an additive operator surface; if the app becomes an execution surface, the plan collapses the phase boundary and changes product risk.

7. **Assess implementation realism for Databricks Apps and bundle integration.**

   Determine whether the proposed `app/` surface, `app.yaml`, `resources/driftsentinel_app.yml`, `databricks.yml` wiring, Premium-workspace dependency, managed-container constraints, and optional SQL warehouse/resource binding are specific enough to implement safely.

   *Success: you can distinguish realistic deployment assumptions from underspecified or misleading ones.*

8. **Assess the verification plan for replayable evidence, not narrative confidence.**

   Review the acceptance criteria and the “Tests and Documentation” phase. Determine whether the planned checks are concrete, whether they map to existing test patterns, and whether screenshot or deploy-proof claims would have durable evidence surfaces.

   *Success: you can identify any missing tests, weak acceptance criteria, or unverifiable PASS conditions before implementation starts.*

9. **Assess whether the plan omits implementation-blocking details that should be resolved before coding.**

   Look for missing configuration-path decisions, ambiguous local test strategy, unclear app-to-data access mechanics, uncertain resource binding details, or unassigned proof obligations that would force implementers to invent requirements mid-flight.

   *Success: you can separate “nice to clarify later” notes from true blockers that should stop implementation kickoff.*

### Phase 3: Produce The Review Output

10. **Report findings first, ordered by severity.**

    For each finding, include: severity, exact plan section or file path, the issue, why it matters, and the smallest correction needed before implementation.

    *Success: a reader can act on the review immediately without reverse-engineering what is broken or why it matters.*

11. **List open questions and assumptions separately from findings.**

    Only include items here if they are not yet defects. If an item would block safe implementation, keep it in findings instead.

    *Success: the review clearly distinguishes confirmed issues from unresolved but non-blocking questions.*

12. **Issue a readiness verdict using the decision matrix.**

    End with `Ready`, `Ready With Changes`, or `Not Ready`, followed by a short rationale tied directly to the findings.

    *Success: the user receives a clear go/no-go recommendation anchored in evidence rather than tone.*

13. **Keep the task read-only unless the user explicitly asks for a follow-up edit pass.**

    Do not patch the plan, add code, or propose implementation diffs in place of the review. If you believe a correction is obvious, describe it in the finding instead of applying it.

    *Success: the review remains a pre-implementation decision artifact, not an unrequested edit session.*

## Guardrails

<guardrails>
- **Forbidden:** Editing `specs/DS-IP-001-P4_Phase_4_App_UI_Plan.md` during this review.
- **Forbidden:** Implementing `app/`, `app.yaml`, `resources/driftsentinel_app.yml`, or any Databricks App code.
- **Forbidden:** Accepting a plan claim solely because it appears in the draft; verify it against canonical specs or current package/test anchors.
- **Forbidden:** Treating unresolved contradictions as “minor” when they would change implementation scope or operator safety.
- **Required:** Use `specs/` as the canonical source whenever `docs/` or the draft plan diverge.
- **Required:** Call out any plan section that would weaken notebook-first Free Edition support, append-only evidence behavior, or the read-only app boundary.
- **Required:** Distinguish measured facts from interpretation in the final review.
- **Budget:** Keep the review proportional; identify actual blockers and material risks, not speculative future enhancements.
</guardrails>

## Verification Checklist

- [ ] The full plan and canonical comparison set were read before findings were issued.
- [ ] Named package anchors were verified in current source files.
- [ ] The review checked both internal consistency and external spec alignment.
- [ ] Findings are ordered by severity and include impact plus corrective action.
- [ ] Open questions are separated from confirmed defects.
- [ ] The review explicitly assessed notebook-first Free Edition support.
- [ ] The review explicitly assessed append-only and read-only boundaries.
- [ ] The review explicitly assessed bundle/deploy realism and proof obligations.
- [ ] The final verdict is `Ready`, `Ready With Changes`, or `Not Ready` with evidence-backed rationale.
- [ ] No code or plan edits were made during the review.

## Error Handling

| Error Condition | Resolution |
|-----------------|------------|
| A plan claim conflicts with `specs/` | Treat `specs/` as authoritative, log a finding against the plan, and cite the exact canonical surface that wins. |
| The plan references a package helper that does not exist | Record a blocking finding; do not assume the helper can be added later without changing scope. |
| The plan is internally contradictory | Record the contradiction as a finding and explain how it would confuse implementation or verification. |
| A Databricks runtime assumption cannot be verified from current sources | Mark the claim as `unverified`, explain the missing proof, and state what evidence would be needed before implementation. |
| The current test suite lacks a proposed verification anchor | Record a finding or gap note depending on severity, and specify the concrete missing test surface. |
| The review discovers likely implementation work | Do not implement it; convert it into a finding, question, or follow-up recommendation only. |

## Out Of Scope

- Implementing any part of the Databricks App
- Editing the plan directly
- Designing Phase 4.1 follow-on work
- Rewriting the repository architecture beyond what is needed to judge the draft plan
- Running Databricks deployment commands unless the user later requests validation beyond document review

## Deliverable Format

Your output must include:

1. **Findings** — severity-ordered, actionable, evidence-backed
2. **Traceability Summary** — short table mapping key plan areas to canonical sources
3. **Open Questions / Assumptions** — only for non-defect items
4. **Readiness Verdict** — `Ready`, `Ready With Changes`, or `Not Ready`
5. **Next-Step Recommendation** — the smallest follow-up action set needed before implementation begins

## Report Format

Use this structure exactly:

```markdown
## Findings
[Severity] [Location] Issue
- Why it matters: ...
- Required correction: ...

## Traceability Summary
| Plan Area | Canonical Source | Status | Notes |
|-----------|------------------|--------|-------|

## Open Questions / Assumptions
- ...

## Readiness Verdict
Ready | Ready With Changes | Not Ready

Short rationale tied to the findings.

## Next Steps
1. ...
2. ...
```
