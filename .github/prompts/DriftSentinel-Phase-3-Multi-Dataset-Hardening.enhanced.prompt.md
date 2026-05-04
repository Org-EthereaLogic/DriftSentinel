# Implement DriftSentinel Phase 3 Multi-Dataset Hardening

**Date:** 2026-04-01
**Prompt Level:** Level 4 (Workflow Prompt)
**Prompt Type:** Feature
**Complexity Classification:** Complex — this task spans shared config contracts, append-only evidence metadata, dataset-aware orchestration, multiple Databricks notebooks, progress tracking, and focused plus full-suite verification across existing package and notebook surfaces.
**Model Recommendation:** `claude-opus-4-20250514` — use the high-capability tier because the work crosses multiple Python modules, notebook entry points, state-tracking surfaces, and acceptance criteria that must remain evidence-safe.
**Assumption:** Interpret “Phase 3: Multi-Dataset Hardening” as implementation work in the current repository, not a planning-only exercise. “One installation operates multiple datasets safely” means independent dataset registration, explicit policy-to-dataset version binding, and queryable historical run evidence without introducing a new external service, UI layer, or runtime dependency outside this repository.
**Path Placeholders:** Resolve `${REPO_ROOT}` to the current DriftSentinel checkout and `${VSCODE_USER_PROMPTS_FOLDER}` to the local VS Code prompt folder before using referenced paths.

## Inputs Consulted

| Source | Key Takeaways |
|--------|---------------|
| Source prompt | Phase 3 follows the Phase 2 packaging milestone, due 2026-04-25, and requires dataset registry patterns, policy versioning, run history, evidence lookup, and safe multi-dataset operation. |
| `${VSCODE_USER_PROMPTS_FOLDER}/Enhance Prompt workflow.prompt.md` | Enhanced prompts must be self-contained, phased, imperative, grounded, and include explicit verification, guardrails, and state tracking for complex tasks. |
| `${REPO_ROOT}/AGENTS.md` | Follow `Plan -> Act -> Verify -> Report`, preserve evidence traceability, avoid unsupported claims, and run the required local checks. |
| `${REPO_ROOT}/CLAUDE.md` | `specs/` is canonical, the repo already contains first-party package code, and the standard verification commands are `make lint`, `make typecheck`, `make test`, and `make bundle-validate`. |
| `${REPO_ROOT}/CONSTITUTION.md` | Safety, evidence traceability, security hygiene, simplicity, and reproducibility control implementation choices. |
| `${REPO_ROOT}/DIRECTIVES.md` | Specs are canonical, append-only evidence must be preserved, and PASS claims require explicit evidence. |
| `${REPO_ROOT}/.github/instructions/codacy.instructions.md` | Codacy analysis should run when the MCP surface exists; unavailable MCP tooling must be reported truthfully rather than fabricated. |
| `${REPO_ROOT}/README.md` | Phase 2 is implemented, notebooks and bundle assets exist, and the repo already presents a Databricks-deployable product surface. |
| `${REPO_ROOT}/specs/DS-IP-001_Implementation_Plan.md` | Phase 3 requires dataset registry patterns, policy versioning, run history, evidence lookup, and a multi-dataset-safe installation exit criterion. |
| `${REPO_ROOT}/specs/DS-SRS-001_Software_Requirements_Specification.md` | Declarative dataset registration, notebook-driven setup, deterministic demo behavior, and append-only evidence remain required product behaviors. |
| `${REPO_ROOT}/specs/DS-SDD-001_Architecture_Blueprint.md` | The canonical control flow is register dataset and policy, seed baseline, run intake, run drift, run benchmark, write evidence, and review outcomes through notebooks. |
| `${REPO_ROOT}/specs/DS-TP-001_Test_Plan.md` | Configuration tests, append-only evidence tests, and integration tests for notebook orchestration are mandatory verification surfaces. |
| `${REPO_ROOT}/specs/DS-TM-001_Traceability_Matrix.md` | Dataset registration traces to `templates/`, config loaders, and the registration notebook; deterministic evidence traces to the evidence writer and integration tests. |
| `${REPO_ROOT}/src/driftsentinel/README.md` | The package already separates config, evidence, orchestration, intake, drift, and benchmark concerns cleanly. |
| `${REPO_ROOT}/src/driftsentinel/config/README.md` | The config surface already owns dataset and policy loading and explicitly calls out per-dataset policy overrides. |
| `${REPO_ROOT}/src/driftsentinel/config/loader.py` | The loader validates one dataset contract, one drift policy, and one benchmark policy at a time, but it does not model a registry, explicit version linkage, or policy compatibility checks. |
| `${REPO_ROOT}/src/driftsentinel/evidence/README.md` | The README promises lookup by run ID, dataset, and date range, but this capability must be verified against the implementation rather than assumed. |
| `${REPO_ROOT}/src/driftsentinel/evidence/writer.py` | The writer produces append-only JSON envelopes and benchmark bundles, but it does not yet encode dataset identity, policy versions, or lookup helpers. |
| `${REPO_ROOT}/src/driftsentinel/orchestration/runner.py` | The orchestration layer remains demo-oriented with `run_intake_demo`, `run_drift_demo`, and `run_local_pipeline`, all without dataset selectors or registry-backed execution. |
| `${REPO_ROOT}/notebooks/README.md` | Notebook logic should stay thin and delegate business logic to `src/driftsentinel/`. |
| `${REPO_ROOT}/notebooks/01_register_dataset.py` | Dataset registration currently validates and prints one contract, but it does not persist or query a dataset registry. |
| `${REPO_ROOT}/notebooks/03_run_intake_controls.py`, `${REPO_ROOT}/notebooks/04_run_drift_gate.py`, `${REPO_ROOT}/notebooks/05_run_control_benchmark.py` | Run notebooks are operational, but they still execute demo or single-policy flows without a dataset selector or registry-backed policy resolution. |
| `${REPO_ROOT}/notebooks/06_review_evidence.py` | Evidence review currently lists and prints every JSON file in a directory rather than supporting dataset, date, or run-ID filters. |
| `${REPO_ROOT}/templates/dataset_contract.yml`, `${REPO_ROOT}/templates/drift_policy.yml`, `${REPO_ROOT}/templates/benchmark_policy.yml` | Templates are still single-dataset oriented and do not yet expose explicit registry or version metadata. |
| `${REPO_ROOT}/tests/test_config_loading.py`, `${REPO_ROOT}/tests/test_evidence_writer.py`, `${REPO_ROOT}/tests/test_orchestration.py`, `${REPO_ROOT}/tests/test_packaging.py` | Current tests validate single-config loading, append-only writing, demo orchestration, and notebook packaging, but they do not yet cover multi-dataset registry behavior or historical evidence lookup. |
| `${REPO_ROOT}/progress.json`, `${REPO_ROOT}/progress.txt` | Phase tracking already exists in-repo and should be reused rather than replaced for this complex implementation. |

## Mission Statement

Implement DriftSentinel Phase 3 by adding a first-party multi-dataset registry pattern, explicit dataset-bound policy versioning, queryable run history and evidence lookup, and dataset-aware notebook and orchestration paths so one installation can manage multiple datasets safely without breaking deterministic demo behavior or append-only evidence guarantees.

## Behavioral Controls

<investigate_before_answering>
Read every file you plan to modify before describing its behavior. If a current surface appears to promise a capability that the implementation does not yet provide, verify that mismatch directly in code or tests before you rely on it.
</investigate_before_answering>

<default_to_action>
Implement the Phase 3 work. Do not stop at planning, architecture commentary, or a partial scaffold.
</default_to_action>

<use_parallel_tool_calls>
Read config, evidence, orchestration, notebook, template, and test surfaces in parallel. After the first substantive edit in each slice, run the narrowest available validation before widening scope.
</use_parallel_tool_calls>

<format_control>
Write progress updates as concise prose. Use markdown headings, fenced code blocks with language identifiers, tables for structured comparisons, and italicized success signals after every action step.
</format_control>

## Technical Context

The current repository is not missing the core control logic. The gap is that the product still treats dataset registration, policy loading, orchestration, and evidence review as largely single-dataset flows.

| Surface | Current State | Phase 3 Target |
|--------|---------------|----------------|
| `src/driftsentinel/config/loader.py` | Loads one contract or policy at a time | Supports registry-backed multi-dataset loading and explicit version compatibility checks |
| `templates/*.yml` | Single-dataset examples with no explicit version contract | Multi-dataset-safe contract and policy metadata that can be loaded independently and validated together |
| `src/driftsentinel/orchestration/runner.py` | Demo-oriented execution with no dataset selector | Dataset-aware execution paths that preserve deterministic demo defaults but support N independent datasets |
| `src/driftsentinel/evidence/writer.py` | Append-only writes with timestamps only | Append-only writes plus dataset identity, run ID, version metadata, and local lookup helpers |
| `notebooks/01_register_dataset.py` | Validates and prints one dataset contract | Registers one dataset at a time into a serializable first-party registry pattern |
| `notebooks/03` / `04` / `05` | Execute intake, drift, and benchmark without a dataset registry selector | Resolve a selected dataset and versioned policy set before execution |
| `notebooks/06_review_evidence.py` | Dumps every JSON artifact in the evidence directory | Filters and inspects historical runs by dataset, date range, or run ID |
| `tests/` | Covers single-dataset config, append-only writes, and demo orchestration | Covers multi-dataset collisions, version mismatches, dataset-aware runs, and historical lookup |

Anchor the implementation in the existing package boundaries.

- Keep registry and policy-loading responsibilities in `src/driftsentinel/config/` unless a nearby existing abstraction proves insufficient.
- Keep historical evidence lookup in `src/driftsentinel/evidence/` so notebooks remain thin and reusable.
- Keep execution routing in `src/driftsentinel/orchestration/` so notebooks do not become a second orchestration layer.
- Keep deterministic demo behavior available for tests and local proof; dataset-aware execution should extend the current behavior, not replace the only reproducible validation path.

Implement a fully featured but scope-bounded Phase 3 solution. Handle version mismatch failures, duplicate registration attempts, missing lookup filters, and empty-evidence directories explicitly, but do not expand into a Databricks app UI, external metadata store, or marketplace work.

## Problem-State Table

| Aspect | Current State | Target State |
|--------|---------------|--------------|
| Dataset registry | One contract can be loaded, printed, and used ad hoc | Multiple datasets can be registered and resolved independently within one installation |
| Policy binding | Drift and benchmark policies refer to a dataset name only | Policies bind to a dataset plus explicit version metadata and fail fast on mismatch |
| Orchestration | Demo-only helpers have no dataset identity input | Execution paths accept selected dataset metadata and route evidence accordingly |
| Evidence metadata | JSON artifacts are append-only but minimally indexed | Every run records dataset identity, run kind, run ID, timestamps, and version linkage |
| Evidence review | Notebook prints all files in a directory | Operators can filter historical artifacts by dataset, date, or run ID |
| Safety boundary | Multiple datasets could collide logically because identity is weak | One installation operates multiple datasets safely with explicit separation and failure behavior |

## Pre-Flight Checks

1. **Confirm the current repository baseline is green before Phase 3 edits.**

   ```bash
   cd "$(git rev-parse --show-toplevel)" && make test
   ```

   Expected: command exits with status `0`.

2. **Confirm the existing progress files are present and reusable for Phase 3 state tracking.**

   ```bash
   cd "$(git rev-parse --show-toplevel)" && test -f progress.json && test -f progress.txt && echo "progress files present"
   ```

   Expected: `progress files present`.

3. **Confirm the current single-dataset execution anchors before editing.**

   ```bash
   cd "$(git rev-parse --show-toplevel)" && rg -n "load_dataset_contract|load_packaged_dataset_contract|run_intake_demo|run_drift_demo|run_local_pipeline|contract_path|policy_path|evidence_dir" src/driftsentinel notebooks tests
   ```

   Expected: matches in the config loader, orchestration runner, notebooks, and current tests.

4. **Confirm that Phase 3 version metadata is not already fully modeled in the current templates and core package surfaces.**

   ```bash
   cd "$(git rev-parse --show-toplevel)" && rg -n "dataset_version|contract_version|policy_version|run_id|lookup" templates src/driftsentinel/config src/driftsentinel/evidence src/driftsentinel/orchestration tests
   ```

   Expected: limited or missing matches for a full Phase 3 contract, confirming the implementation gap is real.

## Instructions

### Phase 1: Re-Baseline The Work And Lock The Shared Phase 3 Contract

1. **Update `progress.json` and `progress.txt` for Phase 3 before you edit product code.**

   Record the phase name as `Phase 3 - Multi-Dataset Hardening`, list the four Phase 3 deliverables from the source prompt, and convert them into explicit checklists or statuses that can be updated as work lands.

   *Success: both progress files state the active phase, the four Phase 3 goals, and at least one concrete subtask for registry, versioning, and evidence lookup.*

   **Rationale:** Complex work is already tracked in-repo, so reusing the existing state files keeps verification auditable and avoids duplicate task ledgers.

2. **Read the Phase 3 edit surface in parallel before the first substantive implementation edit.**

   Read `src/driftsentinel/config/loader.py`, `src/driftsentinel/evidence/writer.py`, `src/driftsentinel/orchestration/runner.py`, `notebooks/01_register_dataset.py`, `notebooks/03_run_intake_controls.py`, `notebooks/04_run_drift_gate.py`, `notebooks/05_run_control_benchmark.py`, `notebooks/06_review_evidence.py`, all three template files under `templates/`, and every test file you plan to extend.

   *Success: you can restate the current registry gap, the current evidence gap, and the exact files you will touch without guessing.*

3. **Define one canonical Phase 3 identity model before you spread edits across modules.**

   Require a stable dataset identifier and explicit version fields for the dataset contract and the policies that govern it. Determine how run identity will be recorded so evidence lookup can filter reliably by dataset, date, and run ID.

   *Success: one shared metadata contract exists that config loading, orchestration, evidence writing, and notebooks can all use consistently.*

   **Rationale:** Multi-dataset safety depends on identity clarity first; if the dataset and policy version contract diverges across modules, every later surface becomes harder to validate.

4. **Record a Phase 1 checkpoint in the progress files immediately after the identity contract is settled.**

   Append the output of `git status --short` and `git diff --stat` to `progress.txt`, and update the Phase 3 checklist or status fields in `progress.json` to reflect the locked contract.

   *Success: the progress files capture a replayable checkpoint of the first implementation boundary without requiring a commit.*

### Phase 2: Implement Dataset Registry Patterns And Policy Versioning

5. **Extend the template and config surfaces so dataset registration becomes explicit and version-aware.**

   Update `templates/dataset_contract.yml`, `templates/drift_policy.yml`, `templates/benchmark_policy.yml`, and `src/driftsentinel/config/loader.py` so each dataset contract and policy can be loaded as an independent, versioned record and validated against the shared identity model you defined in Phase 1.

   *Success: config loading can validate multiple independent dataset definitions and reject missing or malformed version metadata explicitly.*

6. **Add the minimal first-party registry pattern needed for safe multi-dataset operation.**

   Implement the registry inside the existing first-party package boundaries, favoring a serializable local representation that notebooks and orchestration helpers can consume without an external service. Prevent duplicate registration collisions and fail clearly when a caller requests an unknown dataset or incompatible policy version.

   *Success: one installation can hold more than one dataset definition without cross-talk, and invalid dataset or version references fail deterministically.*

   **Rationale:** Phase 3 requires N-dataset operation, but the repository’s governing principle is proportionality; a small first-party registry is sufficient and safer than introducing a new persistence platform.

7. **Route drift and benchmark policies through explicit dataset-version compatibility checks.**

   Bind policies to the dataset identity model, not just a free-form dataset name string. Validate the binding when loading policies and again when resolving a dataset for execution so invalid combinations are blocked before a run starts.

   *Success: dataset-policy mismatches fail before control execution, and successful loads carry explicit compatibility metadata forward into orchestration.*

8. **Add focused tests for registry behavior and version mismatch failures before widening scope.**

   Extend the current config and orchestration tests to cover multi-dataset registration, duplicate IDs or versions, unknown dataset lookups, and incompatible policy bindings.

   *Success: the new tests prove the registry and versioning contract rather than relying on notebook output alone.*

9. **Run the narrow validation for the registry and versioning slice immediately after the first substantive edit lands.**

   ```bash
   cd "$(git rev-parse --show-toplevel)" && uv run pytest tests/test_config_loading.py tests/test_orchestration.py
   ```

   *Success: the command exits with status `0` before you continue into evidence history and notebook updates.*

10. **Record a Phase 2 checkpoint in the progress files after the narrow validation passes.**

    Append `git status --short` and `git diff --stat` to `progress.txt`, and update `progress.json` so registry and versioning are marked with accurate pass, fail, or in-progress state.

    *Success: the progress files show the exact file inventory and validation state for the registry slice.*

### Phase 3: Implement Run History And Evidence Lookup

11. **Extend `src/driftsentinel/evidence/writer.py` so every control artifact carries queryable run metadata.**

    Include dataset identity, run kind, generated timestamp, run ID, and the relevant version metadata in the written JSON envelope. Preserve append-only writes, collision-safe filenames, and deterministic timestamp injection for tests.

    *Success: each written artifact contains enough metadata to support historical lookup without inspecting ad hoc file naming conventions alone.*

12. **Implement local evidence lookup helpers in the existing evidence surface instead of pushing lookup logic into notebooks.**

    Provide first-party helpers that list or filter prior runs by dataset, date range, and run ID using the JSON artifacts already written by the package. Handle empty directories, malformed files, and missing filters explicitly.

    *Success: notebooks and orchestration callers can request structured history results from package code rather than hand-rolling file-system scans inline.*

    **Rationale:** The evidence README already treats lookup as part of the evidence surface, and keeping that responsibility in package code preserves notebook thinness and replayability.

13. **Extend orchestration so dataset-aware execution routes evidence through the new metadata contract.**

    Preserve the deterministic demo helpers where they are useful for tests, but add the smallest adjacent orchestration path required to execute intake, drift, and benchmark for a selected dataset and to write evidence that reflects that selection.

    *Success: dataset-aware runs emit consistent metadata and do not require notebooks to invent their own evidence schema.*

14. **Add focused tests for evidence lookup, run history filtering, and dataset-aware evidence metadata.**

    Extend `tests/test_evidence_writer.py` and any nearby orchestration tests so they cover at minimum dataset filtering, run-ID filtering, date-range filtering, append-only guarantees, and malformed-artifact handling.

    *Success: historical lookup and evidence metadata are verified by pytest rather than manual inspection.*

15. **Run the narrow validation for the evidence-history slice immediately after the first substantive edit lands.**

    ```bash
    cd "$(git rev-parse --show-toplevel)" && uv run pytest tests/test_evidence_writer.py tests/test_orchestration.py
    ```

    *Success: the command exits with status `0` before you widen scope to notebooks and operator surfaces.*

16. **Record a Phase 3 checkpoint in the progress files after the evidence slice stabilizes.**

    Append `git status --short` and `git diff --stat` to `progress.txt`, and update `progress.json` with the evidence-history status and the latest validation command result.

    *Success: the progress files preserve a replayable checkpoint for the evidence-history implementation slice.*

### Phase 4: Update Notebook And Operator Surfaces Without Re-Implementing Business Logic

17. **Update `notebooks/01_register_dataset.py` so registration produces or persists a structured registry-backed result.**

    Add the minimal notebook parameters needed to register one dataset contract and its version metadata, then delegate the actual loading and registration behavior to first-party package code.

    *Success: the registration notebook can register one dataset record at a time and print a structured confirmation tied to the shared identity model.*

18. **Update `notebooks/03_run_intake_controls.py`, `notebooks/04_run_drift_gate.py`, and `notebooks/05_run_control_benchmark.py` to accept dataset selection and version-aware policy resolution.**

    Add only the widgets needed to select a dataset and optional override paths where appropriate, then route execution through dataset-aware orchestration helpers rather than the demo-only path when a selected dataset is provided.

    *Success: each run notebook can execute against a chosen dataset without duplicating registry, policy-resolution, or evidence-writing logic inline.*

19. **Update `notebooks/06_review_evidence.py` to filter historical evidence by dataset, date range, or run ID.**

    Keep the notebook focused on operator interaction and output formatting while delegating file discovery and filtering to first-party lookup helpers in the package.

    *Success: the evidence-review notebook no longer prints every artifact indiscriminately and can return targeted historical runs.*

20. **Extend packaging and notebook tests to cover the new widgets and notebook thinness expectations.**

    Extend `tests/test_packaging.py` or an adjacent focused test file so it verifies dataset-selection widgets, evidence-query widgets, and the absence of notebook-local re-implementations of registry or lookup behavior.

    *Success: notebook-facing Phase 3 behaviors are covered by automated tests instead of manual notebook inspection alone.*

21. **Run the focused notebook and packaging validation before you move to the full suite.**

    ```bash
    cd "$(git rev-parse --show-toplevel)" && uv run pytest tests/test_packaging.py tests/test_config_loading.py tests/test_evidence_writer.py tests/test_orchestration.py
    ```

    *Success: the touched notebook and package surfaces pass together before broad repo verification begins.*

22. **Record a Phase 4 checkpoint in the progress files after the notebook slice passes.**

    Append `git status --short` and `git diff --stat` to `progress.txt`, and update `progress.json` so the notebook and evidence-review work reflects actual validation status.

    *Success: the progress files contain a clear checkpoint for the final implementation slice before repo-wide verification.*

### Phase 5: Verify The Full Phase 3 Exit Criterion And Security Gates

23. **Run the full local verification suite required by repository policy.**

    ```bash
    cd "$(git rev-parse --show-toplevel)" && make lint && make typecheck && make test
    ```

    *Success: lint, typecheck, and tests all exit with status `0`.*

24. **Run the placeholder scan explicitly after notebook and docs-facing changes.**

    ```bash
    cd "$(git rev-parse --show-toplevel)" && uv run python - <<'PY'
    import re
    from pathlib import Path

    root = Path('.')
    banned = re.compile(r"\b(?:to" r"do|fix" r"me|tb" r"d|place" r"holder)\b", re.IGNORECASE)
    surfaces = [root / 'specs', root / '.claude', root / 'CLAUDE.md', root / 'docs']
    violations = []
    for surface in surfaces:
        paths = [surface] if surface.is_file() else list(surface.rglob('*'))
        for path in paths:
            if not path.is_file():
                continue
            text = path.read_text(encoding='utf-8')
            for lineno, line in enumerate(text.splitlines(), start=1):
                if banned.search(line):
                    violations.append(f"{path}:{lineno}:{line.strip()}")
    if violations:
        raise SystemExit("\n".join(violations))
    print('placeholder scan passed')
    PY
    ```

    *Success: the scan prints `placeholder scan passed`.*

25. **Run bundle validation because bundle surfaces remain part of the supported product even if Phase 3 edits stay package-heavy.**

    ```bash
    cd "$(git rev-parse --show-toplevel)" && make bundle-validate
    ```

    *Success: bundle validation exits with status `0` or a clearly documented external-environment blocker is recorded as `unverified` rather than `passed`.*

    **Rationale:** The repository’s required checks include bundle validation when bundle surfaces exist, and Phase 3 notebook changes still interact with Databricks execution paths.

26. **Run Snyk code analysis on the repository root after first-party Phase 3 code lands.**

    Execute `snyk_code_scan` against `${REPO_ROOT}`.

    *Success: no new high-severity first-party code issues are introduced, or any findings are resolved before completion.*

27. **Mark the Phase 3 exit criterion truthfully.**

    Declare the phase `passed` only if the repository can register, execute, and review multiple datasets safely with explicit version binding and replayable evidence under automated verification. If any external prerequisite blocks the final proof, mark that slice `unverified` and separate it from the verified local evidence.

    *Success: the final report distinguishes verified facts, blocked external proof, and interpretation cleanly.*

## Guardrails

<guardrails>
- **Forbidden:** Introducing a new external database, service, API, or UI layer to store the registry or run history.
- **Forbidden:** Adding runtime dependencies on sibling chapter repositories or non-repo local paths.
- **Forbidden:** Re-implementing config loading, registry logic, orchestration, or evidence lookup directly inside notebook files.
- **Forbidden:** Overwriting or deleting existing evidence under `report/`.
- **Forbidden:** Declaring the multi-dataset exit criterion `passed` without replayable verification evidence.
- **Required:** Keep notebooks thin and route business logic through `src/driftsentinel/`.
- **Required:** Preserve deterministic demo behavior for local and test validation even as dataset-aware execution is added.
- **Required:** Fail explicitly on unknown dataset identifiers, duplicate registry collisions, and policy version mismatches.
- **Required:** Reuse `progress.json` and `progress.txt` instead of creating new state files.
- **Required:** Keep new first-party modules proportional in size and purpose; prefer direct extensions of existing package boundaries over speculative abstractions.
- **Budget:** Do not introduce new dependencies unless the existing standard library and current dependency set cannot satisfy the requirement.
- **Budget:** Keep individual source files under the repository’s recommended 500-line ceiling when practical.
</guardrails>

## Verification Checklist

- [ ] `progress.json` and `progress.txt` are updated for Phase 3 and reused throughout the implementation
- [ ] A canonical dataset identity and version model exists across config, orchestration, evidence, and notebooks
- [ ] Multiple datasets can be registered and resolved independently inside one installation
- [ ] Drift and benchmark policies fail fast when dataset or version linkage is invalid
- [ ] Dataset-aware runs emit append-only evidence with dataset identity, run ID, and version metadata
- [ ] Historical evidence lookup works by dataset, date range, and run ID
- [ ] Notebook surfaces expose dataset selection or evidence-query controls where required
- [ ] Notebooks stay thin and delegate registry, orchestration, and lookup work to first-party package code
- [ ] Focused tests cover registry collisions, version mismatches, dataset-aware runs, and evidence lookup
- [ ] `make lint`, `make typecheck`, and `make test` pass
- [ ] Placeholder scan passes
- [ ] `make bundle-validate` passes or is marked `unverified` with a concrete blocker
- [ ] Snyk code analysis is run and any material findings are resolved or reported truthfully

## Error Handling

| Error Condition | Resolution |
|-----------------|------------|
| Template schema and loader schema drift apart during Phase 3 edits | Make the template contract authoritative for the new metadata fields, then update loader validation and tests together before widening scope. |
| Duplicate dataset registration collides with an existing identifier or version | Fail explicitly and require either a new version or an intentional replacement path with clear operator-facing messaging. |
| A drift or benchmark policy references a dataset or version that is not registered | Block execution before the run starts and surface a precise mismatch error in package code and notebook output. |
| Historical evidence lookup encounters malformed or partial JSON | Skip or quarantine the malformed artifact in the lookup result and record the parse failure explicitly rather than crashing the entire query silently. |
| The evidence directory is empty or missing | Return an empty or blocked result with a clear message and keep the review notebook usable. |
| Notebook widgets or dataset selectors become inconsistent across notebooks | Normalize the widget names and update the packaging tests so the inconsistency cannot recur unnoticed. |
| Focused pytest validation fails after a slice edit | Repair that same slice immediately and rerun the same narrow validation before opening another edit slice. |
| `make bundle-validate` cannot run because the Databricks CLI or profile is unavailable | Record the exact missing prerequisite and mark the bundle-validation proof as `unverified`, not `passed`. |
| Snyk MCP tools are unavailable in the current environment | State that the security scan could not be executed in-session and do not fabricate a pass result. |

## Out Of Scope

- Building the Databricks App UI from Phase 4
- Marketplace distribution or provider-profile work from Phase 5
- Replacing the file-backed evidence model with a database or service-backed index
- Creating a general-purpose metadata platform beyond the registry and lookup needed for Phase 3
- Refactoring unrelated domain logic in intake, drift, or benchmark modules that is not required for multi-dataset support

## Report Format

When the implementation is complete, report results in this structure:

1. **Task outcome:** state whether Phase 3 is `passed`, `partially verified`, or `unverified`.
2. **Files changed:** list every modified file and group them by config, evidence, orchestration, notebooks, templates, and tests.
3. **Dataset identity contract:** summarize the final dataset and version metadata model and where it is enforced.
4. **Registry behavior:** summarize how multiple datasets are registered, resolved, and protected from collision.
5. **Evidence history behavior:** summarize how run history and lookup now work by dataset, date range, and run ID.
6. **Verification evidence:** list each command or MCP scan you ran and its real result.
7. **Blocked or unverified items:** list any external blockers or incomplete proof separately from verified facts.
8. **Residual risks:** note any remaining limitations that should shape Phase 4 work but were intentionally left out of scope here.
