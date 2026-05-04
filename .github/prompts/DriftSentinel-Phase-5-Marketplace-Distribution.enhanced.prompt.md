# Execute DriftSentinel Phase 5 Marketplace Distribution Preparation

**Date:** 2026-04-03
**Prompt Level:** Level 4 (Workflow Prompt)
**Prompt Type:** Feature
**Complexity Classification:** Complex — this work spans canonical specs, repo-backed commercialization artifacts, append-only evidence, progress tracking, Notion sprint coordination, and optional external Databricks Marketplace provider steps. It must stay disciplined because the task explicitly forbids changing the product core while still producing a distribution-ready packet.
**Model Recommendation:** `claude-opus-4-20250514` — use the high-capability tier because the work crosses repository governance, external coordination surfaces, artifact packaging, and evidence-safe completion logic.
**Assumption:** Interpret the source assessment as a request to begin Phase 5 execution in the current repository. Do not assume its stated blockers are still true. First reconcile the source assessment against current repo evidence, then create the missing Phase 5 marketplace-preparation artifacts and coordination updates without modifying DriftSentinel product behavior.
**Path Placeholders:** Resolve `${REPO_ROOT}` to the current DriftSentinel checkout and `${VSCODE_USER_PROMPTS_FOLDER}` to the local VS Code prompt folder before using referenced paths.

## Inputs Consulted

| Source | Key Takeaways |
|--------|---------------|
| Source prompt | Phase 5 is the next logical workstream, but the source prompt mixes a real sprint-tracking gap with a potentially stale bundle-validation blocker and expects a practical sequence rather than open-ended planning. |
| `${VSCODE_USER_PROMPTS_FOLDER}/Enhance Prompt workflow.prompt.md` | Enhanced prompts must be grounded, self-contained, phased, imperative, and include explicit verification, guardrails, and state tracking for complex tasks. |
| `${REPO_ROOT}/AGENTS.md` | Follow `Plan -> Act -> Verify -> Report`, read governing docs first, preserve evidence traceability, and run required quality checks when relevant. |
| `${REPO_ROOT}/CLAUDE.md` | `specs/` is canonical, bundle validation is a core workflow command, Notion is an external coordination surface, and Phase 5 follows the Databricks App milestone. |
| `${REPO_ROOT}/CONSTITUTION.md` | Safety, evidence traceability, secret hygiene, proportionality, and validation-before-commercialization govern Phase 5 decisions. |
| `${REPO_ROOT}/DIRECTIVES.md` | PASS claims require evidence, append-only reports must be preserved, and Notion sync must stay truthful. |
| `${REPO_ROOT}/.github/instructions/codacy.instructions.md` | Repo instructions apply when edits occur, but unavailable Codacy MCP tooling must not be fabricated. |
| `${REPO_ROOT}/specs/DS-IP-001_Implementation_Plan.md` | Phase 5 requires provider-profile and listing-material preparation, with the exit criterion “distribution channels in place without changing the product core.” |
| `${REPO_ROOT}/specs/DS-PRD-001_Product_Requirements_Document.md` | Marketplace provider operations are not a release blocker for Version 1, and commercialization claims still require repository-backed evidence. |
| `${REPO_ROOT}/specs/DS-SRS-001_Software_Requirements_Specification.md` | Marketplace provider operations require a paid workspace with Unity Catalog, and missing evidence must force blocked status rather than implied completion. |
| `${REPO_ROOT}/specs/DS-BI-001_Build_Instructions.md` | The canonical bundle proof path is catalog check plus bundle validate, with validation alone insufficient to prove catalog existence or deployment success. |
| `${REPO_ROOT}/README.md` | The repo already has proven Databricks deployment and app surfaces but does not yet present marketplace-preparation collateral. |
| `${REPO_ROOT}/docs/README.md` | `docs/` is the right home for explanatory commercialization and submission-prep material. |
| `${REPO_ROOT}/assets/README.md` | `assets/` is the correct home for auditable collateral and brand files, including any marketplace-specific asset inventory. |
| `${REPO_ROOT}/app/README.md` | The App is a read-only Premium-workspace surface, which matters for marketplace positioning and paid-workspace prerequisites. |
| `${REPO_ROOT}/progress.json` | If present locally, inspect whether it records `bundle_validate`, `bundle_deploy`, `benchmark_job_run`, and `bundle_destroy` status before making readiness claims. |
| `${REPO_ROOT}/progress.txt` | If present locally, inspect whether historical phase notes include catalog check, bundle validate, deploy, run, and destroy evidence before using them. |
| `${REPO_ROOT}/report/2026-04-02T07-36-36Z-bundle-proof-reconciliation.md` | The bundle-validation blocker from earlier work is closed for the `e62-trial` proof path, and validation alone does not prove catalog existence. |
| `${REPO_ROOT}/report/2026-04-02T23-23-notion-sync-record.md` | Phase 5 is still `Not Started`, there are no marketplace artifacts in the repo, and no sprint is currently marked `Current`. |
| `${REPO_ROOT}/report/2026-04-03T01-05-notion-sync-record.md` | The latest sync still shows no current sprint and Phase 5 unchanged, but its local “bundle validation not attempted” note is stale relative to repo proof artifacts. |

## Mission Statement

Execute DriftSentinel Phase 5 by reconciling current readiness evidence, creating a repo-backed marketplace distribution packet, updating project tracking, and only attempting external marketplace or Notion mutations that are both supported by current permissions and safely evidenced, all without changing the product core.

## Behavioral Controls

<investigate_before_answering>
Read every repository file, evidence artifact, and external-coordination surface you rely on before making claims about Phase 5 readiness, bundle proof state, sprint state, or marketplace gaps. If the source prompt conflicts with current repo evidence, treat the repo evidence as authoritative and record the discrepancy explicitly.
</investigate_before_answering>

<default_to_action>
Perform the Phase 5 preparation work. Do not stop at commentary or a high-level plan. Produce the repo-backed artifacts, status updates, and evidence record unless an external permission boundary blocks a specific mutation.
</default_to_action>

<use_parallel_tool_calls>
Read specs, progress files, proof artifacts, and directory READMEs in parallel during the investigation phase. Group independent read-only diagnostics together whenever possible.
</use_parallel_tool_calls>

<format_control>
Write status notes in concise engineering prose. Use markdown headings, fenced code blocks with language identifiers, tables for structured comparisons, and italicized success signals after every action step.
</format_control>

<do_not_act_before_instructions>
Do not perform irreversible external publication actions such as creating a Databricks Marketplace provider, submitting a marketplace listing, or publishing a live marketplace asset without first presenting the exact action and receiving explicit confirmation. Local repository edits, evidence capture, and reversible status updates may proceed without additional confirmation.
</do_not_act_before_instructions>

## Technical Context

Phase 5 is not a product-code milestone. The current repository already has measured proof for the bundle and app foundation, and the implementation plan constrains this phase to provider-profile and listing-material preparation. The product core is already present; the gap is commercialization collateral, external readiness tracking, and truthful evidence-backed coordination.

The source assessment is partially stale. Repository proof now shows that the Databricks bundle path has already been validated, deployed, run, and destroyed successfully against a real catalog and workspace. That means the Phase 5 workflow must begin by reconciling current state instead of treating bundle validation as an unresolved blocker. The sprint gap, however, is still current: multiple recent Notion sync records confirm that no sprint is marked `Current`, and Phase 5 remains `Not Started`.

Keep the implementation proportional and repo-first.

| Surface | Current State | Phase 5 Target |
|--------|---------------|----------------|
| Bundle/deploy proof | May be evidenced in local progress trackers and bundle proof reports; verify before relying on it | Reused as marketplace readiness evidence, not re-litigated unless current work edits executable deploy surfaces |
| Marketplace collateral | No marketplace artifacts in repo | Repo-backed provider/listing packet exists under `docs/` and `assets/` |
| README discovery copy | Product and deployment focused | Includes a concise marketplace-prep section that points to the new collateral |
| Sprint/task coordination | Phase 5 `Not Started`; no sprint marked `Current` | Phase 5 tracking updated truthfully, with live Notion mutation only if available and evidenced |
| Commercialization claims | Easy to overstate from prior implementation success | Claims stay bounded: prepared, evidenced, blocked, or awaiting operator input |

Create a fully featured but scope-bounded Phase 5 preparation packet. Handle missing operator-owned inputs such as legal contacts, billing model, marketplace categories, and final submission approvals by marking them `operator input required` rather than inventing values. Reuse existing repo proof and collateral where possible. Do not turn this phase into product refactoring, pricing strategy invention, or unverified publication claims.

## Problem-State Table

| Aspect | Current State | Target State |
|--------|---------------|--------------|
| Source prompt accuracy | Mixes a true sprint gap with a stale bundle-validation blocker | Current blockers are reconciled against repo evidence before any work proceeds |
| Phase 5 task status | `Not Started` in recent Notion sync records | Phase 5 tracking reflects active work or explicit blocked status with evidence |
| Sprint container | No sprint currently marked `Current` | A current sprint is created or the missing-sprint condition is captured as an explicit coordination blocker |
| Marketplace artifacts | No repo-backed marketplace packet exists | Provider-profile draft, listing material, asset inventory, and submission checklist exist in-repo |
| README discovery support | No marketplace-specific guidance | README links to Phase 5 collateral and summarizes commercialization readiness accurately |
| External publication state | Easy to overclaim based on internal proof only | External provider/listing mutations are either performed with evidence or left clearly blocked |

## Pre-Flight Checks

1. **Verify the core Phase 5 input set exists before you start.**

   ```bash
   cd "$(git rev-parse --show-toplevel)" && test -f specs/DS-IP-001_Implementation_Plan.md && test -f specs/DS-PRD-001_Product_Requirements_Document.md && test -f specs/DS-SRS-001_Software_Requirements_Specification.md && test -f specs/DS-BI-001_Build_Instructions.md && if test -f progress.json && test -f progress.txt; then echo "phase5 inputs present with local progress trackers"; else echo "phase5 canonical inputs present; local progress trackers absent"; fi
   ```

   Expected: canonical inputs are present, and the output truthfully states whether local progress trackers exist.

   *Success: the canonical Phase 5 sources and current progress files are present.*

2. **Verify the current repo still records bundle proof before treating it as blocked.**

   ```bash
   cd "$(git rev-parse --show-toplevel)" && FILES="report/2026-04-02T07-36-36Z-bundle-proof-reconciliation.md" && test -f progress.json && FILES="$FILES progress.json"; test -f progress.txt && FILES="$FILES progress.txt"; rg -n '"bundle_validate": "passed"|bundle-validate: PASS|Deployment complete!|TERMINATED SUCCESS' $FILES
   ```

   Expected: matches in all three files.

   *Success: you have direct evidence for whether the bundle-proof blocker is open or closed.*

3. **Verify the sprint gap and current Phase 5 status from the latest sync evidence.**

   ```bash
   cd "$(git rev-parse --show-toplevel)" && rg -n 'Phase 5: Marketplace Distribution|No sprint currently marked "Current"' report/2026-04-02T23-23-notion-sync-record.md report/2026-04-03T01-05-notion-sync-record.md
   ```

   Expected: matches showing Phase 5 `Not Started` and no current sprint.

   *Success: you have current evidence for the coordination gap instead of inferring it.*

4. **Verify there is no existing marketplace-preparation packet in the repo.**

   ```bash
   cd "$(git rev-parse --show-toplevel)" && find docs assets -maxdepth 3 \( -iname '*marketplace*' -o -path '*/marketplace/*' \) | sort
   ```

   Expected: either no output or only legacy/non-authoritative paths that do not already satisfy Phase 5.

   *Success: you know whether you are creating new Phase 5 collateral or updating an existing packet.*

## Instructions

### Phase 1: Reconcile Current Readiness And Lock Scope

1. **Read the Phase 5 comparison set in parallel before editing anything.**

   Read `specs/DS-IP-001_Implementation_Plan.md`, `specs/DS-PRD-001_Product_Requirements_Document.md`, `specs/DS-SRS-001_Software_Requirements_Specification.md`, `specs/DS-BI-001_Build_Instructions.md`, `README.md`, `docs/README.md`, `assets/README.md`, `app/README.md`, `report/2026-04-02T07-36-36Z-bundle-proof-reconciliation.md`, `report/2026-04-02T23-23-notion-sync-record.md`, and `report/2026-04-03T01-05-notion-sync-record.md`. Also read `progress.json` and `progress.txt` if they exist locally.

   *Success: you can restate the Phase 5 exit criterion, the commercialization boundaries, the current bundle-proof state, and the current sprint/task state without guessing.*

2. **Determine which source-prompt assertions still hold and record the delta explicitly.**

   Create a short comparison table in `progress.txt` or your working notes that marks each source assertion as `still true`, `stale`, or `partially true`. At minimum classify the bundle-validation blocker, the no-current-sprint claim, and the “next logical step is Phase 5” claim.

   *Success: you have a factual reconciliation record that prevents Phase 5 work from starting on a false premise.*

   **Rationale:** The source prompt is an assessment, not an authoritative repository state snapshot.

3. **Activate Phase 5 in the in-repo state trackers before creating artifacts.**

   Create or update `${REPO_ROOT}/progress.json` and `${REPO_ROOT}/progress.txt` to represent `Phase 5 - Marketplace Distribution`, with explicit checklist entries for: source-state reconciliation, provider-profile draft, listing-material draft, asset inventory, README discovery update, sprint coordination, external mutation status, and verification.

   *Success: the progress files name Phase 5 directly and separate completed repo work from blocked external actions.*

4. **Record a checkpoint after the scope is locked.**

   Append the output of `git status --short` and `git diff --stat` to `progress.txt` after the progress-file update.

   *Success: the progress log captures the initial Phase 5 file inventory and working-set size.*

### Phase 2: Build The Repo-Backed Marketplace Packet

5. **Create one canonical marketplace-preparation document under `docs/`.**

   Create `${REPO_ROOT}/docs/marketplace_distribution.md` with these sections:

   - `## Phase 5 Scope`
   - `## Provider Profile Draft`
   - `## Listing Material Draft`
   - `## Prerequisites And Workspace Requirements`
   - `## Asset Inventory`
   - `## Submission Checklist`
   - `## Operator Input Required`
   - `## Evidence References`

   Populate every field only from repo-backed facts, current app/deployment behavior, and measured evidence. For unknown business-owned fields such as final pricing, legal contact, or marketplace category selection, write `operator input required` and explain why the repo cannot supply the value.

   *Success: `docs/marketplace_distribution.md` exists and contains a truthful, submission-oriented packet with no fabricated values.*

   **Rationale:** Phase 5 requires provider-profile and listing-material preparation, but the repo must not invent non-technical commercialization data.

6. **Create a marketplace asset manifest under `assets/`.**

   Create `${REPO_ROOT}/assets/driftsentinel-brand-system/marketplace/README.md` that lists reusable brand assets, app screenshots or evidence visuals already available in-repo, missing assets that still need capture, and the exact source path for each asset or evidence image you reference.

   *Success: the asset manifest distinguishes `available now` from `missing` and every referenced asset maps to an existing repo path.*

   **Rationale:** `assets/` is the canonical collateral surface, and a manifest is safer than copying or renaming assets blindly.

7. **Update the root README with a minimal marketplace-preparation section.**

   Add a concise section to `${REPO_ROOT}/README.md` that explains the current commercialization state, links to `docs/marketplace_distribution.md`, and clarifies that marketplace preparation does not change the product core or supersede the existing GitHub and bundle deployment path.

   *Success: the README improves discoverability without overstating marketplace readiness.*

8. **Create an append-only evidence artifact for the Phase 5 packet.**

   Write a new timestamped report at `${REPO_ROOT}/report/YYYY-MM-DDTHH-MM-SS-phase5-marketplace-prep.md` that records: current branch and commit, the reconciled blocker status, the files created or updated for Phase 5, any external mutations attempted, and which completion claims remain blocked by operator input or external permissions.

   *Success: there is a replayable evidence artifact describing exactly what Phase 5 preparation accomplished in this session.*

9. **Record a Phase 2 checkpoint after the packet is assembled.**

   Append `git status --short` and `git diff --stat` to `progress.txt`, and update `progress.json` to mark the packet-creation items accurately.

   *Success: the state files show which repo-backed Phase 5 deliverables are now complete.*

### Phase 3: Coordinate Sprint And External Publication Readiness

10. **Handle the sprint gap truthfully.**

   If Notion mutation tools are available and the DriftSentinel dashboard context is present, create or update the current sprint container and move `Phase 5: Marketplace Distribution` to `In Progress` only when the packet from Phase 2 exists. If live mutation is unavailable, create a repo-backed fallback note in the Phase 5 report describing the intended sprint mutation and the reason it could not be verified live.

   *Success: sprint coordination is either applied and evidenced or explicitly blocked with a repo-backed fallback record.*

   **Rationale:** The sprint gap is real, but Notion remains an external coordination surface and must not be misreported.

11. **Assess Databricks Marketplace provider readiness before any live publication mutation.**

   Determine whether the current environment has safe, authenticated access to the provider-facing Marketplace APIs or CLI/SDK surfaces needed to inspect provider/listing readiness. Use read-only inspection first. If the environment lacks permissions, account context, or required operator-owned metadata, document the exact blocker in the Phase 5 evidence artifact instead of improvising values or forcing a live publish.

   *Success: you know whether live marketplace mutation is feasible, and any infeasibility is recorded precisely.*

12. **Stop for confirmation before any irreversible marketplace create or publish action.**

   If provider creation, listing creation, asset upload, or submission is actually feasible, present the exact action, required inputs, and expected effect, then wait for explicit user confirmation before proceeding.

   *Success: irreversible external publication actions do not occur silently or on ambiguous authority.*

### Phase 4: Verification And Quality Control

13. **Run focused validation for each file class you changed.**

   At minimum run:

   ```bash
   cd "$(git rev-parse --show-toplevel)" && uv run python -m json.tool progress.json >/dev/null
   ```

   ```bash
   cd "$(git rev-parse --show-toplevel)" && test -f docs/marketplace_distribution.md && rg -n '^## Phase 5 Scope|^## Provider Profile Draft|^## Listing Material Draft|^## Submission Checklist|^## Evidence References' docs/marketplace_distribution.md
   ```

   ```bash
   cd "$(git rev-parse --show-toplevel)" && test -f assets/driftsentinel-brand-system/marketplace/README.md && rg -n '^## Available Assets|^## Missing Assets|^## Source Paths' assets/driftsentinel-brand-system/marketplace/README.md
   ```

   ```bash
   cd "$(git rev-parse --show-toplevel)" && rg -n 'Marketplace|marketplace_distribution.md' README.md
   ```

   *Success: structured files validate, required sections exist, and README links the new collateral.*

14. **Run the canonical placeholder scan because docs changed.**

   ```bash
   cd "$(git rev-parse --show-toplevel)" && PATTERN='TO''DO|FIX''ME|TB''D|PLACE''HOLDER'; rg -n "$PATTERN" specs .claude CLAUDE.md docs
   ```

   *Success: the command returns no matches.*

15. **Re-run executable Databricks proof only if you changed deploy-relevant surfaces.**

   If you edited only `README.md`, docs, assets manifests, reports, or progress files, do not re-run bundle or app deployment commands. If you touched `databricks.yml`, `resources/`, `app/`, `notebooks/`, `scripts/`, or other executable deployment surfaces, re-run the narrowest relevant proof command from `specs/DS-BI-001_Build_Instructions.md` and record the result.

   *Success: verification effort matches the actual change surface and does not waste time re-proving untouched product behavior.*

### Phase 5: Report And Readiness Conclusion

16. **Issue a readiness conclusion using evidence-backed labels only.**

   End with one of these outcomes:

   - `Prepared`: repo-backed Phase 5 packet exists, sprint coordination is handled truthfully, and only explicit operator-owned publication inputs remain.
   - `Prepared With External Blockers`: packet exists, but live sprint or marketplace mutations remain blocked by permissions, missing operator data, or confirmation requirements.
   - `Not Prepared`: required packet artifacts or truthful evidence are still missing.

   *Success: the conclusion is actionable, bounded, and justified directly by the evidence artifact and progress files.*

## Guardrails

<guardrails>
- Do not change `src/driftsentinel/`, `app/`, `resources/`, `notebooks/`, or Databricks bundle logic unless a directly evidenced Phase 5 blocker proves that a minimal non-core change is required.
- Do not claim that bundle validation is blocked unless current repo evidence shows it is blocked on the present worktree.
- Do not fabricate provider profile fields, legal text, pricing tiers, categories, screenshots, customer logos, or publication approvals.
- Do not publish or submit a live marketplace listing without explicit user confirmation.
- Do not treat Notion mutation failure as task completion; create a repo-backed fallback record instead.
- Do not overwrite existing files in `report/`; Phase 5 evidence must remain append-only.
- Do not introduce new dependencies for documentation-only commercialization work.
- Keep the implementation proportional: prefer docs, manifests, evidence, and small README updates over speculative architecture or product changes.
- If Codacy MCP analysis tools are unavailable, record that limitation truthfully rather than claiming the analysis ran.
</guardrails>

## Verification Checklist

- [ ] Source-prompt assertions were reconciled against current repo evidence before Phase 5 execution began
- [ ] `progress.json` and `progress.txt` now track `Phase 5 - Marketplace Distribution`
- [ ] `docs/marketplace_distribution.md` exists with provider, listing, checklist, and evidence sections
- [ ] `assets/driftsentinel-brand-system/marketplace/README.md` exists with an asset inventory and source paths
- [ ] `README.md` includes a truthful marketplace-preparation section or link
- [ ] A new append-only Phase 5 evidence artifact exists under `report/`
- [ ] Sprint coordination was either applied live or documented as blocked with fallback evidence
- [ ] Any feasible marketplace provider inspection was completed read-only first
- [ ] No irreversible marketplace publication action occurred without explicit confirmation
- [ ] `progress.json` remains valid JSON
- [ ] Placeholder scan passes for `docs/`
- [ ] No completion claim exceeds repo-backed or live-mutation evidence

## Error Handling

| Error Condition | Resolution |
|-----------------|------------|
| Source prompt says bundle validation is blocked, but repo evidence shows it passed | Record the source prompt as stale, treat the blocker as closed for current planning, and only reopen it if current work touches executable deploy surfaces and introduces a new failure. |
| No sprint is marked `Current`, and Notion mutation is unavailable | Keep the repo packet work moving, write the intended sprint mutation into the Phase 5 evidence record, and report `Prepared With External Blockers`. |
| Marketplace provider APIs are unavailable or permissions are insufficient | Stop at the repo-backed submission packet, document the precise missing permission or account dependency, and do not improvise external completion. |
| Required commercialization metadata is business-owned and missing | Mark the field `operator input required`, explain why the repository cannot supply it, and continue with the rest of the packet. |
| Existing screenshots or brand assets are missing or unsuitable | Record the gap in the asset manifest, list the exact missing asset type, and avoid fabricating visuals. |
| README or docs drift into unsupported commercialization claims | Rewrite the copy to a claim-safe form tied to existing proof or explicit blocked status. |
| A proposed fix requires product-core changes | Stop, document why the requirement exceeds Phase 5 scope, and request direction before changing executable product surfaces. |
| Codacy MCP analysis tooling is unavailable | State that the tooling was unavailable and proceed with the other required verifications. |

## Out Of Scope

- Refactoring or extending the DriftSentinel product core
- New Databricks jobs, bundle resources, notebooks, or app features for marketplace positioning
- Final pricing strategy, legal terms, customer contracts, or billing implementation
- Publishing a live Databricks Marketplace listing without confirmation
- Inventing commercialization metrics, adoption claims, or customer references
- Treating marketplace readiness as a Version 1 release blocker contrary to the PRD

## Report Format

1. **Current-state reconciliation:** which source-prompt claims were still true, stale, or partially true
2. **Files created or updated:** repo-backed Phase 5 packet, asset manifest, README, progress files, and evidence artifact
3. **Sprint coordination:** live mutation applied, repo-backed fallback only, or blocked
4. **Marketplace external readiness:** read-only inspection result, missing permissions, or confirmation gate status
5. **Verification evidence:** commands run and outcomes
6. **Remaining operator inputs:** exact fields or approvals still required
7. **Final readiness label:** `Prepared`, `Prepared With External Blockers`, or `Not Prepared`
