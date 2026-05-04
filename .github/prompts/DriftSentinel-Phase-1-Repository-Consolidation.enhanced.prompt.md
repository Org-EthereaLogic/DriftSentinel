# Implement DriftSentinel Phase 1 Repository Consolidation

**Date:** 2026-04-02
**Prompt Level:** Level 4 (Workflow Prompt)
**Prompt Type:** Feature
**Complexity Classification:** Complex — this task spans shared foundations plus three product domains, requires selective code extraction from three sibling repositories, adds deterministic tests, and must enforce a no-sibling-runtime-dependency boundary.
**Model Recommendation:** `claude-opus-4-20250514` — use the high-capability tier because the work combines multi-repository code reading, architectural restraint, staged implementation, and full quality-gate verification.
**Assumption:** Interpret “Chapter 1,” “Chapter 2,” and “Chapter 3” as the confirmed sibling repositories `/Users/etherealogic-2/Dev/Databricks/trusted-source-intake`, `/Users/etherealogic-2/Dev/Databricks/silent-failure-prevention`, and `/Users/etherealogic-2/Dev/Databricks/measurable-control-effectiveness`.

## Inputs Consulted

| Source | Key Takeaways |
|--------|---------------|
| Source prompt | Phase 1 Repository Consolidation is the only remaining not-started task and has four explicit acceptance criteria: port Chapter 1, 2, and 3 logic; normalize config and evidence; preserve deterministic behavior and tests; remove sibling-clone runtime dependencies. |
| `/Users/etherealogic-2/Dev/Databricks/DriftSentinel/AGENTS.md` | Use `Plan -> Act -> Verify -> Report`, keep sibling chapter logic as first-party code, and run the required validation suite truthfully. |
| `/Users/etherealogic-2/Dev/Databricks/DriftSentinel/CLAUDE.md` | `specs/` is canonical, product code belongs under `src/driftsentinel/`, and the standard repo commands are `make lint`, `make typecheck`, `make test`, and `make bundle-validate`. |
| `/Users/etherealogic-2/Dev/Databricks/DriftSentinel/CONSTITUTION.md` | Safety, evidence traceability, security hygiene, simplicity, and reproducibility control implementation decisions in that order. |
| `/Users/etherealogic-2/Dev/Databricks/DriftSentinel/DIRECTIVES.md` | No runtime dependency on sibling chapter clones is a critical directive, and specs remain canonical over any explanatory docs. |
| `/Users/etherealogic-2/Dev/Databricks/DriftSentinel/.github/instructions/codacy.instructions.md` | Codacy analysis should run after edits when the tool surface is available, and repository identifiers must remain `gh / Org-EthereaLogic / DriftSentinel`. |
| `/Users/etherealogic-2/Dev/Databricks/DriftSentinel/specs/DS-IP-001_Implementation_Plan.md` | Phase 1 is explicitly defined as repository consolidation with a no-sibling-dependency exit criterion. |
| `/Users/etherealogic-2/Dev/Databricks/DriftSentinel/specs/DS-SRS-001_Software_Requirements_Specification.md` | Phase 1 work traces directly to first-party intake, drift, benchmark, config, evidence, and deterministic demo requirements. |
| `/Users/etherealogic-2/Dev/Databricks/DriftSentinel/specs/DS-SDD-001_Architecture_Blueprint.md` | The architecture already reserves `config`, `evidence`, `intake`, `drift`, `benchmark`, and `orchestration` as the product-layer package boundaries. |
| `/Users/etherealogic-2/Dev/Databricks/DriftSentinel/specs/DS-TM-001_Traceability_Matrix.md` | Verification must cover local config loaders, evidence writers, intake, drift, benchmark, and deterministic validation paths. |
| `/Users/etherealogic-2/Dev/Databricks/DriftSentinel/specs/DS-WBS-001_Project_Plan_WBS.md` | The implementation WBS assigns Phase 1 deliverables directly to `src/driftsentinel/intake/`, `drift/`, `benchmark/`, `evidence/`, `orchestration/`, `config/`, and `tests/`. |
| `/Users/etherealogic-2/Dev/Databricks/DriftSentinel/Makefile` | The canonical validation commands are `make lint`, `make typecheck`, `make test`, and `make bundle-validate`. |
| `/Users/etherealogic-2/Dev/Databricks/DriftSentinel/pyproject.toml` | The product targets Python 3.11+, currently depends only on `pyyaml` and `pandas`, and should avoid unnecessary dependency growth. |
| `/Users/etherealogic-2/Dev/Databricks/DriftSentinel/tests/test_scaffold_layout.py` | The current tests only guard scaffold presence and package layout. |
| `/Users/etherealogic-2/Dev/Databricks/DriftSentinel/tests/test_governance_guards.py` | Placeholder markers are banned from executable surfaces and bundle wiring already has explicit tests. |
| `/Users/etherealogic-2/Dev/Databricks/DriftSentinel/src/driftsentinel/config/__init__.py` and sibling package `__init__.py` files | The target packages are still stub-only docstring surfaces with no substantive implementation modules. |
| `/Users/etherealogic-2/Dev/Databricks/trusted-source-intake/README.md` | Chapter 1 is the intake-control source repository covering contract validation, replay handling, quarantine routing, and downstream-safe ready outputs. |
| `/Users/etherealogic-2/Dev/Databricks/trusted-source-intake/src/intake/contracts.py` | Chapter 1 already exposes seven named contract checks plus batch evaluation helpers that are directly relevant to `src/driftsentinel/intake/`. |
| `/Users/etherealogic-2/Dev/Databricks/trusted-source-intake/src/intake/demo_metrics.py` | Chapter 1 already has deterministic offline demo summary logic and batch-registry behavior that can seed local product tests. |
| `/Users/etherealogic-2/Dev/Databricks/silent-failure-prevention/README.md` | Chapter 2 is the drift-gate source repository covering distribution-stability scoring, publication verdicts, and audit-style provenance. |
| `/Users/etherealogic-2/Dev/Databricks/silent-failure-prevention/src/stability/gates/evaluator.py` | Chapter 2 already has configurable gate loading and pass/warn/fail evaluation semantics worth porting or adapting. |
| `/Users/etherealogic-2/Dev/Databricks/silent-failure-prevention/src/stability/runners/local_demo.py` | Chapter 2 already has a deterministic local release-control execution path that combines baseline creation, drift detection, gate evaluation, and provenance output. |
| `/Users/etherealogic-2/Dev/Databricks/measurable-control-effectiveness/README.md` | Chapter 3 is the benchmark source repository covering deterministic fault injection, baseline-vs-challenger scoring, and evidence bundles. |
| `/Users/etherealogic-2/Dev/Databricks/measurable-control-effectiveness/src/benchmark/runners/orchestrator.py` | Chapter 3 already has a structured orchestration path for dataset generation, quality scoring, drift scoring, gate evaluation, and optional evidence output. |
| `/Users/etherealogic-2/Dev/Databricks/measurable-control-effectiveness/src/benchmark/evidence/writer.py` | Chapter 3 already has append-only structured evidence bundle writing that should inform the shared product evidence surface. |

## Mission Statement

Implement DriftSentinel Phase 1 by porting Chapter 1, Chapter 2, and Chapter 3 logic into first-party modules under `src/driftsentinel/`, unifying config loading and append-only evidence writing, preserving deterministic local behavior and tests, and proving that no runtime dependency on sibling chapter repositories remains.

## Behavioral Controls

<investigate_before_answering>
Read every target file you plan to edit and every source file you plan to port before describing behavior or implementation details. If a required capability is missing from the chapter repositories, report the exact file gap before creating substitute logic.
</investigate_before_answering>

<default_to_action>
Implement the consolidation. Do not stop at a proposal, summary, or architecture note.
</default_to_action>

<use_parallel_tool_calls>
Read target files in parallel, read source modules in parallel, and run focused validation immediately after each edited slice before widening scope.
</use_parallel_tool_calls>

<format_control>
Write progress updates as short prose plus small tables when helpful. Use markdown headings, fenced code blocks with language identifiers, and italicized success signals after every action step.
</format_control>

## Technical Context

DriftSentinel is a scaffold with the correct package boundaries but no substantive product code yet. The six package stubs under `src/driftsentinel/` already define where the implementation belongs:

| Product Surface | Current State | Required Phase 1 Role |
|-----------------|---------------|------------------------|
| `src/driftsentinel/config/` | Docstring-only stub | Shared loader for dataset contracts, drift policies, and benchmark policies sourced from `templates/` or explicit paths |
| `src/driftsentinel/evidence/` | Docstring-only stub | Shared append-only evidence writing and provenance helpers |
| `src/driftsentinel/intake/` | Docstring-only stub | Chapter 1 contract checks, replay detection, quarantine routing, and deterministic demo metrics |
| `src/driftsentinel/drift/` | Docstring-only stub | Chapter 2 baseline creation, drift detection, gate evaluation, and publication verdict logic |
| `src/driftsentinel/benchmark/` | Docstring-only stub | Chapter 3 dataset generation, quality scoring, drift scoring, gate evaluation, and evidence bundle logic |
| `src/driftsentinel/orchestration/` | Docstring-only stub | Minimal local orchestration needed to exercise Phase 1 deterministically inside DriftSentinel |

The verified source material is already partitioned by domain:

| Domain | Confirmed Source Files | Product Destination |
|--------|------------------------|---------------------|
| Intake | `/Users/etherealogic-2/Dev/Databricks/trusted-source-intake/src/intake/contracts.py`, `/Users/etherealogic-2/Dev/Databricks/trusted-source-intake/src/intake/demo_metrics.py`, plus sibling Chapter 1 sample-data and tests files discovered from `src/` and `tests/` inventory | `src/driftsentinel/intake/` and `tests/test_intake.py` |
| Drift | `/Users/etherealogic-2/Dev/Databricks/silent-failure-prevention/src/stability/detection/*.py`, `/Users/etherealogic-2/Dev/Databricks/silent-failure-prevention/src/stability/gates/evaluator.py`, `/Users/etherealogic-2/Dev/Databricks/silent-failure-prevention/src/stability/provenance/builder.py`, `/Users/etherealogic-2/Dev/Databricks/silent-failure-prevention/src/stability/runners/local_demo.py`, plus sibling Chapter 2 tests | `src/driftsentinel/drift/`, `src/driftsentinel/evidence/`, and `tests/test_drift.py` |
| Benchmark | `/Users/etherealogic-2/Dev/Databricks/measurable-control-effectiveness/src/benchmark/datasets/synthetic.py`, `drift/detectors.py`, `quality/detectors.py`, `gates/evaluator.py`, `scoring/ground_truth.py`, `evidence/writer.py`, `runners/orchestrator.py`, plus sibling Chapter 3 tests | `src/driftsentinel/benchmark/`, `src/driftsentinel/evidence/`, and `tests/test_benchmark.py` |

Current DriftSentinel tests verify only scaffold integrity and governance guards. That means Phase 1 must add deterministic behavior tests in this repository rather than inheriting PASS claims from the sibling repos. Implement a fully-featured consolidation that handles config validation, missing required fields, append-only evidence guarantees, and deterministic seeds instead of stopping at stub replacement.

## Problem-State Table

| Aspect | Current State | Target State |
|--------|---------------|--------------|
| Product code | `src/driftsentinel/` contains only package docstrings. | `src/driftsentinel/` contains real first-party Python modules with stable local APIs. |
| Logic location | Intake, drift, and benchmark behavior still lives in sibling chapter repositories. | Equivalent behavior runs locally from DriftSentinel with no sibling runtime imports. |
| Shared foundations | No normalized config loader or shared evidence writer exists. | Config and evidence are centralized under `config/` and `evidence/` and reused across all domains. |
| Deterministic proof | Tests only cover scaffold and governance surfaces. | Deterministic unit and integration-style tests verify Phase 1 behavior from this repository. |
| Boundary enforcement | Phase 1 could regress by keeping sibling file paths or imports in executable code. | Executable surfaces are free of sibling chapter runtime dependencies. |

## Pre-Flight Checks

1. **Verify the target repo, the three source repos, and the current stub-only target surface.**

   ```bash
   cd "/Users/etherealogic-2/Dev/Databricks/DriftSentinel" && test -d ../trusted-source-intake && test -d ../silent-failure-prevention && test -d ../measurable-control-effectiveness && find src/driftsentinel -type f -name '*.py' | sort
   ```

   Expected: only `__init__.py` files under `src/driftsentinel/` are listed.

2. **Confirm the current repo baseline is green before implementation.**

   ```bash
   cd "/Users/etherealogic-2/Dev/Databricks/DriftSentinel" && make test
   ```

   Expected: command exits with status `0`.

3. **Inventory the source modules you will port.**

   ```bash
   cd "/Users/etherealogic-2/Dev/Databricks/DriftSentinel" && find ../trusted-source-intake/src ../silent-failure-prevention/src ../measurable-control-effectiveness/src -type f -name '*.py' | sort
   ```

   Expected: the output includes Chapter 1 intake modules, Chapter 2 stability modules, and Chapter 3 benchmark modules.

4. **Check for existing sibling-repository references in executable surfaces.**

   ```bash
   cd "/Users/etherealogic-2/Dev/Databricks/DriftSentinel" && grep -RIn "trusted-source-intake\|silent-failure-prevention\|measurable-control-effectiveness" src tests notebooks resources templates || true
   ```

   Expected: no runtime references, or only clearly non-executable comments that you can remove or justify.

## Instructions

### Phase 1: Investigation And Port Map

1. **Create `progress.json` and `progress.txt` at the repository root before editing product code.**

   Initialize `progress.json` with this structure:

   ```json
   {
     "phase": "Phase 1 - Repository Consolidation",
     "source_repos": {},
     "port_map": [],
     "tests_added": [],
     "validation": [],
     "open_questions": []
   }
   ```

   Initialize `progress.txt` with the date, the four acceptance criteria, and a one-line note that Phase 1 must end with no sibling runtime dependencies.

   *Success: Both files exist and explicitly name all three source repos plus the six target packages.*

   **Rationale:** Complex multi-package extraction work needs structured state so no domain is left half-ported or half-verified.

2. **Read the exact target and source files in parallel before the first substantive edit.**

   Read `AGENTS.md`, `CLAUDE.md`, `CONSTITUTION.md`, `DIRECTIVES.md`, `specs/DS-IP-001_Implementation_Plan.md`, `specs/DS-SRS-001_Software_Requirements_Specification.md`, `specs/DS-SDD-001_Architecture_Blueprint.md`, `specs/DS-TM-001_Traceability_Matrix.md`, `specs/DS-WBS-001_Project_Plan_WBS.md`, `Makefile`, `pyproject.toml`, `tests/test_scaffold_layout.py`, `tests/test_governance_guards.py`, the package `__init__.py` files under `src/driftsentinel/`, and the confirmed source modules you plan to extract first.

   *Success: You can restate the acceptance criteria, required validation commands, and the initial source-to-target extraction path without guessing.*

3. **Write a concrete source-to-target port map into `progress.txt` and `progress.json`.**

   At minimum, map Chapter 1 contract checks and demo metrics into `src/driftsentinel/intake/`; Chapter 2 detection, gate, and provenance logic into `src/driftsentinel/drift/` and `src/driftsentinel/evidence/`; and Chapter 3 dataset, scoring, gate, and evidence logic into `src/driftsentinel/benchmark/` and `src/driftsentinel/evidence/`.

   *Success: Every target package has an explicit planned implementation file and no entry preserves a sibling runtime import.*

4. **Create the deterministic test file plan before implementation.**

   Plan to add `tests/test_config_loading.py`, `tests/test_evidence_writer.py`, `tests/test_intake.py`, `tests/test_drift.py`, `tests/test_benchmark.py`, and `tests/test_orchestration.py`, adjusting names only if an existing local naming pattern requires it.

   *Success: The test plan exists in `progress.json` and covers shared foundations plus all three domains.*

   **Rationale:** Deterministic verification is an acceptance criterion, not optional follow-up work.

### Phase 2: Shared Foundations

5. **Implement the shared config layer under `src/driftsentinel/config/` first.**

   Create local configuration modules that load dataset contracts, drift policies, and benchmark policies from `templates/` or explicit file paths, validate required fields, and expose typed return values suitable for all three domains.

   *Success: Intake, drift, and benchmark code can import a single local config surface without reading sibling-repo paths.*

   **Rationale:** Config normalization is named explicitly in DS-IP-001 and must be stable before domain ports rely on it.

6. **Implement the shared evidence layer under `src/driftsentinel/evidence/` second.**

   Create append-only evidence-writing helpers that preserve explicit field completeness, deterministic metadata where supported, and repository-local output paths. Adapt Chapter 2 provenance behavior and Chapter 3 structured evidence-bundle behavior into this shared surface where practical.

   *Success: A single local evidence API exists for intake, drift, and benchmark outputs, and it never mutates prior artifacts in place.*

   **Rationale:** Evidence writing is the second cross-domain acceptance criterion and should not be duplicated independently in each domain package.

7. **Add deterministic tests for the shared foundations before porting domain code.**

   Implement `tests/test_config_loading.py` and `tests/test_evidence_writer.py` to cover successful loads, missing required fields, append-only writes, and deterministic metadata behavior.

   *Success: The shared-layer tests fail before the implementation and pass after it.*

8. **Run the first focused validation immediately after the first substantive edit.**

   ```bash
   cd "/Users/etherealogic-2/Dev/Databricks/DriftSentinel" && uv run pytest tests/test_config_loading.py tests/test_evidence_writer.py
   ```

   *Success: The command exits with status `0` before you widen scope to intake, drift, or benchmark code.*

9. **Record a non-destructive checkpoint after the shared-foundation slice.**

   Append the output of `git status --short` and `git diff --stat` to `progress.txt`.

   *Success: `progress.txt` contains a dated checkpoint for the shared config and evidence phase.*

### Phase 3: Domain Ports

10. **Port Chapter 1 logic into `src/driftsentinel/intake/` using local imports only.**

   Start from `/Users/etherealogic-2/Dev/Databricks/trusted-source-intake/src/intake/contracts.py` and `/Users/etherealogic-2/Dev/Databricks/trusted-source-intake/src/intake/demo_metrics.py`. Bring over the seven named contract checks, row and batch evaluation behavior, replay-aware batch summary logic, and deterministic demo support. Adapt any sample-data dependency into local test fixtures or local deterministic support code rather than reading sibling assets at runtime.

   *Success: `src/driftsentinel/intake/` contains executable first-party modules and `tests/test_intake.py` proves deterministic contract and summary behavior.*

11. **Run the intake-focused validation and record the checkpoint before starting drift work.**

   ```bash
   cd "/Users/etherealogic-2/Dev/Databricks/DriftSentinel" && uv run pytest tests/test_intake.py
   ```

   *Success: The intake-only test command exits with status `0`, and `progress.txt` records the intake checkpoint.*

12. **Port Chapter 2 logic into `src/driftsentinel/drift/` and shared evidence modules.**

   Start from `/Users/etherealogic-2/Dev/Databricks/silent-failure-prevention/src/stability/detection/`, `/Users/etherealogic-2/Dev/Databricks/silent-failure-prevention/src/stability/gates/evaluator.py`, `/Users/etherealogic-2/Dev/Databricks/silent-failure-prevention/src/stability/provenance/builder.py`, and `/Users/etherealogic-2/Dev/Databricks/silent-failure-prevention/src/stability/runners/local_demo.py`. Preserve baseline creation, drift detection, pass/warn/fail gate semantics, and publication-verdict behavior while routing config and evidence through the new DriftSentinel shared layers.

   *Success: `src/driftsentinel/drift/` contains executable first-party modules and `tests/test_drift.py` proves deterministic verdict behavior.*

13. **Run the drift-focused validation and record the checkpoint before starting benchmark work.**

   ```bash
   cd "/Users/etherealogic-2/Dev/Databricks/DriftSentinel" && uv run pytest tests/test_drift.py
   ```

   *Success: The drift-only test command exits with status `0`, and `progress.txt` records the drift checkpoint.*

14. **Port Chapter 3 logic into `src/driftsentinel/benchmark/` and shared evidence modules.**

   Start from `/Users/etherealogic-2/Dev/Databricks/measurable-control-effectiveness/src/benchmark/datasets/synthetic.py`, `quality/detectors.py`, `drift/detectors.py`, `gates/evaluator.py`, `scoring/ground_truth.py`, `evidence/writer.py`, and `runners/orchestrator.py`. Preserve deterministic seed-based dataset generation, baseline-vs-challenger scoring, gate evaluation, and structured evidence output while keeping all runtime paths local to DriftSentinel.

   *Success: `src/driftsentinel/benchmark/` contains executable first-party modules and `tests/test_benchmark.py` proves deterministic benchmark behavior.*

15. **Run the benchmark-focused validation and record the checkpoint before adding orchestration.**

   ```bash
   cd "/Users/etherealogic-2/Dev/Databricks/DriftSentinel" && uv run pytest tests/test_benchmark.py
   ```

   *Success: The benchmark-only test command exits with status `0`, and `progress.txt` records the benchmark checkpoint.*

16. **Implement only the minimal orchestration needed for a deterministic local Phase 1 execution path.**

   Add `src/driftsentinel/orchestration/` modules only where they connect local config loading, domain execution, and evidence writing. Do not widen scope into Databricks bundle orchestration unless a direct Phase 1 integration need forces a small repair.

   *Success: `tests/test_orchestration.py` proves a deterministic local happy path across the shared layers and ported domain code.*

   **Rationale:** Phase 1 is repository consolidation, not Phase 2 platform packaging.

17. **Run the orchestration-focused validation and record the checkpoint.**

   ```bash
   cd "/Users/etherealogic-2/Dev/Databricks/DriftSentinel" && uv run pytest tests/test_orchestration.py
   ```

   *Success: The orchestration test command exits with status `0`, and `progress.txt` contains a dated orchestration checkpoint.*

### Phase 4: Full Verification And Boundary Enforcement

18. **Run the sibling-dependency boundary scan across executable surfaces.**

   ```bash
   cd "/Users/etherealogic-2/Dev/Databricks/DriftSentinel" && grep -RIn "trusted-source-intake\|silent-failure-prevention\|measurable-control-effectiveness" src tests notebooks resources templates || true
   ```

   *Success: The scan returns no runtime dependency matches in executable surfaces.*

19. **Run the required repo quality gates from the repository root.**

   ```bash
   cd "/Users/etherealogic-2/Dev/Databricks/DriftSentinel" && make lint && make typecheck && make test
   ```

   *Success: Ruff, mypy, and pytest all exit with status `0`.*

20. **Run bundle validation only if you edited bundle-linked surfaces.**

   ```bash
   cd "/Users/etherealogic-2/Dev/Databricks/DriftSentinel" && make bundle-validate
   ```

   *Success: The command exits with status `0`, or you document that notebooks, `databricks.yml`, and `resources/` were not changed and the check was not required.*

   **Rationale:** `AGENTS.md` requires bundle validation when the implementation touches bundle surfaces, but Phase 1 should avoid broad Phase 2 packaging work.

21. **Run the placeholder scan over the required repository surfaces.**

   ```bash
   cd "/Users/etherealogic-2/Dev/Databricks/DriftSentinel" && grep -RInE "\b(todo|fixme|tbd|placeholder)\b" specs .claude CLAUDE.md docs src tests notebooks resources templates || true
   ```

   *Success: No banned placeholder markers are found in the required surfaces.*

22. **Run available security analysis and record tool-surface limitations honestly.**

   Run Codacy local analysis for each edited file if the Codacy MCP surface is available. Run Snyk code scan for edited first-party Python files if the Snyk surface is available. If one or both tools are unavailable, record the exact limitation and do not claim a clean result that you did not measure.

   *Success: Security results or explicit tool limitations are recorded with no fabricated PASS claim.*

### Phase 5: Final Report

23. **Update `progress.json` and `progress.txt` with the final implementation state before reporting.**

   Record the final source-to-target port map, files changed, tests added, validation commands and outcomes, whether bundle validation ran, and whether Codacy or Snyk analysis was executed or blocked by tool availability.

   *Success: Another agent can resume or audit the work directly from the two progress files.*

24. **Report completion against the four Phase 1 acceptance criteria with explicit evidence.**

   Map each criterion to changed files and validation evidence from DriftSentinel: Chapter 1, 2, and 3 logic ported into first-party packages; config and evidence normalized; deterministic behavior and tests preserved; no sibling runtime dependencies remaining.

   *Success: The final report is evidence-backed, acceptance-criterion-based, and fully grounded in this repository.*

## Guardrails

<guardrails>
- Do not preserve runtime imports or runtime file reads that point to `/Users/etherealogic-2/Dev/Databricks/trusted-source-intake`, `/Users/etherealogic-2/Dev/Databricks/silent-failure-prevention`, or `/Users/etherealogic-2/Dev/Databricks/measurable-control-effectiveness`.
- Do not widen scope into Phase 2 Databricks MVP packaging, Phase 3 multi-dataset hardening, Phase 4 app UI work, Phase 5 marketplace work, or Notion synchronization changes.
- Do not overwrite or delete anything under `report/`; evidence artifacts are append-only.
- Do not add new dependencies unless the port is blocked without them and you record the justification plus the resulting security checks.
- Do not create generic abstractions, base classes, or utility modules unless the extracted behavior is used immediately by more than one Phase 1 domain slice.
- Do not use uncontrolled timestamps, random seeds, or environment-specific paths in deterministic tests.
- Do not commit, amend, or create branches unless the user explicitly asks.
- Do not claim PASS based on chapter-repo behavior alone; replay validation locally inside DriftSentinel.
</guardrails>

## Verification Checklist

- [ ] `src/driftsentinel/config/` contains the shared local config API.
- [ ] `src/driftsentinel/evidence/` contains the shared append-only evidence API.
- [ ] `src/driftsentinel/intake/` contains first-party intake logic derived from Chapter 1.
- [ ] `src/driftsentinel/drift/` contains first-party drift-gate logic derived from Chapter 2.
- [ ] `src/driftsentinel/benchmark/` contains first-party benchmark logic derived from Chapter 3.
- [ ] `src/driftsentinel/orchestration/` contains only the minimal local orchestration required for Phase 1.
- [ ] `tests/test_config_loading.py`, `tests/test_evidence_writer.py`, `tests/test_intake.py`, `tests/test_drift.py`, `tests/test_benchmark.py`, and `tests/test_orchestration.py` exist or equivalent deterministic replacements exist.
- [ ] `make lint` exits with status `0`.
- [ ] `make typecheck` exits with status `0`.
- [ ] `make test` exits with status `0`.
- [ ] `make bundle-validate` exits with status `0`, or its omission is justified because no bundle-linked surfaces changed.
- [ ] The sibling-dependency boundary scan returns no runtime dependency matches.
- [ ] The placeholder scan returns no banned markers in required surfaces.
- [ ] Codacy and Snyk analysis outcomes, or exact tool-surface limitations, are reported truthfully.
- [ ] The final report maps each Phase 1 acceptance criterion to concrete evidence from DriftSentinel.

## Error Handling

| Error Condition | Resolution |
|-----------------|------------|
| One or more sibling chapter repositories is missing | Stop immediately, report the missing absolute path, and request the corrected source location before continuing. |
| Source logic depends on chapter-specific paths or assets that should not live in DriftSentinel runtime | Copy only the first-party logic, move reusable fixtures into DriftSentinel-local tests, and replace path assumptions with local config abstractions. |
| A ported module still imports or reads from a sibling repository | Replace the dependency with a local DriftSentinel module or copied deterministic fixture, then rerun the boundary scan before proceeding. |
| Deterministic tests fail because of timestamps, random seeds, or filesystem assumptions | Inject fixed clocks, fixed seeds, or temporary-path fixtures and rerun the same focused tests before expanding scope. |
| Ruff, mypy, or pytest fails after a domain slice | Repair that same slice immediately and rerun the same focused validation command before moving to the next slice. |
| Bundle validation fails after a required bundle-surface edit | Repair the bundle-linked change locally, or narrow the change if the bundle edit was not required for Phase 1 acceptance. |
| Codacy or Snyk tools are unavailable | Record the exact tool limitation, do not fabricate a clean result, and complete the rest of the local validation record. |

## Out Of Scope

- Phase 2 Databricks MVP packaging except for narrow fixes forced by Phase 1 integration
- Phase 3 multi-dataset hardening
- Phase 4 Databricks App UI work
- Phase 5 marketplace distribution work
- Notion dashboard synchronization changes
- Broad documentation rewrites unrelated to the Phase 1 implementation contract

## Report Format

Provide the completion report in this structure:

1. **Outcome:** One paragraph stating whether Phase 1 repository consolidation is complete.
2. **Files Changed:** Flat list of DriftSentinel files added or modified.
3. **Source-To-Target Port Map:** Table mapping each source repository file or module family to its DriftSentinel destination.
4. **Acceptance Criteria Evidence:** One flat bullet per acceptance criterion, each citing changed files and validation evidence.
5. **Validation:** Flat list of every command or tool run and whether it passed.
6. **Security And Boundary Status:** State the sibling-dependency scan result plus Codacy and Snyk outcomes or tooling gaps.
7. **Residual Risks:** Flat list of any intentionally deferred parity gaps or follow-up tasks.
