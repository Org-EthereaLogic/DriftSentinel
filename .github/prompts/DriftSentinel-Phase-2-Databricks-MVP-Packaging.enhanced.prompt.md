# Implement DriftSentinel Phase 2 Databricks MVP Packaging

**Date:** 2026-04-01
**Prompt Level:** Level 4 (Workflow Prompt)
**Prompt Type:** Feature
**Complexity Classification:** Complex — this task spans bundle configuration, seven Databricks notebook entry points, deployment documentation, benchmark-policy normalization, and repo-level verification against local plus workspace-facing acceptance criteria.
**Model Recommendation:** `claude-opus-4-20250514` — use the high-capability tier because the work combines multi-file implementation, Databricks bundle semantics, notebook activation, and evidence-safe validation.
**Assumption:** Interpret “repo deploys into a clean Databricks workspace from GitHub” as a minimal but real GitHub-backed Phase 2 path: the repository can be validated and deployed with Declarative Automation Bundles, the deployed jobs/pipeline reference workspace assets rather than bundle `git_source`, and the notebooks can install or resolve the `driftsentinel` package from GitHub-origin code without relying on local sibling repositories.
**Path Placeholders:** Resolve `${REPO_ROOT}` to the current DriftSentinel checkout before using referenced repository paths; command snippets use `git rev-parse --show-toplevel` to avoid machine-specific checkout locations.

## Inputs Consulted

| Source | Key Takeaways |
|--------|---------------|
| Source prompt | Phase 2 follows the Phase 1 consolidation milestone and has four explicit deliverables: operational `databricks.yml` plus `resources/*.yml`, operational notebooks, GitHub-to-Databricks deployment docs, and a clean-workspace deployment exit criterion. |
| `${REPO_ROOT}/AGENTS.md` | Use `Plan -> Act -> Verify -> Report`, preserve evidence traceability, keep changes minimal, and run the required local checks truthfully. |
| `${REPO_ROOT}/CLAUDE.md` | `specs/` is canonical, `src/driftsentinel/` already contains first-party product code, and the standard commands are `make lint`, `make typecheck`, `make test`, and `make bundle-validate`. |
| `${REPO_ROOT}/CONSTITUTION.md` | Safety, evidence traceability, security hygiene, simplicity, and reproducibility control all decisions, and packaging work is explicitly in scope. |
| `${REPO_ROOT}/DIRECTIVES.md` | Specs are canonical, quality-control surfaces must remain wired, and no claim can outrun evidence. |
| `${REPO_ROOT}/.github/instructions/codacy.instructions.md` | Codacy analysis should follow edits when the tool surface exists, but unavailable MCP tooling must be reported instead of fabricated. |
| `${REPO_ROOT}/README.md` | Phase 0/1 intentionally left bundle resources and notebooks as scaffolds, and Phase 2 is the point where runnable Databricks workflows arrive. |
| `${REPO_ROOT}/specs/DS-IP-001_Implementation_Plan.md` | Phase 2 requires bundle resources, notebooks, GitHub-to-Databricks install paths, and a clean-workspace deployment exit criterion. |
| `${REPO_ROOT}/specs/DS-SRS-001_Software_Requirements_Specification.md` | Bundle deployment, manual import, notebook execution, deterministic demo behavior, and truthful external interfaces are required product behaviors. |
| `${REPO_ROOT}/specs/DS-SDD-001_Architecture_Blueprint.md` | The control flow is already defined: register dataset, seed baseline, run intake, run drift gate, run benchmark, write evidence, review evidence. |
| `${REPO_ROOT}/specs/DS-TM-001_Traceability_Matrix.md` | Phase 2 traces directly to `databricks.yml`, `resources/`, `notebooks/`, `templates/`, config loaders, and workspace validation. |
| `${REPO_ROOT}/specs/DS-TP-001_Test_Plan.md` | Integration tests for bundle resources and notebook orchestration are required, not optional follow-up work. |
| `${REPO_ROOT}/databricks.yml` | The bundle currently only names `resources/*.yml`, `catalog`, and `schema`; it is structurally valid but operationally incomplete. |
| `${REPO_ROOT}/resources/intake_pipeline.yml`, `${REPO_ROOT}/resources/drift_gate_job.yml`, `${REPO_ROOT}/resources/benchmark_job.yml` | All three resource files are comment-only stubs with no deployable Databricks resources defined. |
| `${REPO_ROOT}/notebooks/00_quickstart_setup.py` through `${REPO_ROOT}/notebooks/06_review_evidence.py` | All seven notebooks still raise the same explicit DS-IP-001 Phase 2 runtime error and need real package-backed execution. |
| `${REPO_ROOT}/src/driftsentinel/orchestration/runner.py` | Drift demo thresholds are still embedded inline, which is acceptable for Phase 1 local execution but not sufficient for notebook-driven Databricks packaging. |
| `${REPO_ROOT}/src/driftsentinel/benchmark/orchestrator.py` | Benchmark execution still falls back to `_DEFAULT_GATES`, which conflicts with the intent to source policy from `templates/`. |
| `${REPO_ROOT}/src/driftsentinel/config/loader.py` | Benchmark policy loading validates the presence of `gates` but does not normalize the template into the gate schema expected by the evaluator. |
| `${REPO_ROOT}/templates/benchmark_policy.yml` | The benchmark template exposes high-level gate keys such as `min_recall` and `max_false_positive_rate`, not the explicit gate-dict structure used by the evaluator. |
| `${REPO_ROOT}/pyproject.toml` | The project is a real Python package with `hatchling`, `src/driftsentinel`, and an optional `databricks` dependency group, so GitHub-backed package installation is feasible. |
| `https://docs.databricks.com/aws/en/dev-tools/bundles/index.html` | Bundles are validated, deployed, and run through the Databricks CLI; workspace files must be enabled; bundle work should stay source-controlled and reproducible. |
| `https://docs.databricks.com/aws/en/dev-tools/bundles/resources.html` | Jobs and pipelines are first-class bundle resources; `databricks bundle validate` warns on unknown properties; jobs can point to notebook tasks and pipelines can point to workspace notebooks. |
| `https://docs.databricks.com/aws/en/dev-tools/bundles/job-task-types.html` | Bundle job `git_source` and task `source: GIT` are not recommended; workspace-backed notebook tasks are the preferred bundle path, and notebook paths are relative to the resource file when source is workspace-managed by the bundle. |

## Mission Statement

Implement DriftSentinel Phase 2 by converting the Databricks bundle stubs into deployable resources, activating the seven notebook entry points so they call real `driftsentinel` package code, normalizing benchmark gates to load from template-backed policy instead of inline defaults, and documenting the GitHub-to-Databricks installation and deployment paths needed to deploy into a clean Databricks workspace.

## Behavioral Controls

<investigate_before_answering>
Read every file you plan to edit before describing its behavior. If a Databricks bundle field or task type is uncertain, verify it against the official Databricks bundle documentation before adding it.
</investigate_before_answering>

<default_to_action>
Implement the packaging work. Do not stop at a plan, review, or architecture summary.
</default_to_action>

<use_parallel_tool_calls>
Read bundle files, notebook files, and verification surfaces in parallel. After the first substantive edit in each slice, run the narrowest available validation before widening scope.
</use_parallel_tool_calls>

<format_control>
Write progress updates as concise prose. Use markdown headings, fenced code blocks with language identifiers, tables for structured comparisons, and italicized success signals after every action step.
</format_control>

## Technical Context

The repo already contains the product logic needed for Phase 2; the gap is packaging and execution wiring rather than missing domain code.

| Surface | Current State | Phase 2 Target |
|--------|---------------|----------------|
| `databricks.yml` | Includes `resources/*.yml` and `catalog`/`schema` variables only | Becomes the operational bundle root for deploy and run workflows |
| `resources/intake_pipeline.yml` | Comment-only stub | Defines a real Databricks pipeline resource for intake execution |
| `resources/drift_gate_job.yml` | Comment-only stub | Defines a real Databricks job resource that runs the drift notebook or script path |
| `resources/benchmark_job.yml` | Comment-only stub | Defines a real Databricks job resource that runs the benchmark notebook or script path |
| `notebooks/00` through `06` | Fail-closed runtime errors | Thin Databricks notebooks that gather parameters, install or resolve the package, and call first-party package code |
| `src/driftsentinel/config/loader.py` + `templates/benchmark_policy.yml` | Template shape and evaluator shape do not match | One source of truth for benchmark gates, loaded from `templates/` or explicit policy paths |
| `docs/deployment_guide.md` | Explains scaffold validation only | Documents real GitHub-to-Databricks deploy and install paths |

Keep notebook logic thin. The notebooks should orchestrate Databricks-specific concerns such as widgets, install path selection, and evidence output locations, while `src/driftsentinel/` remains the place where business logic executes.

The benchmark normalization issue is a real blocking mismatch and should be handled early. The evaluator currently expects gate dicts with this shape:

```python
{
    "name": "quality_recall",
    "type": "FAIL",
    "operator": ">=",
    "threshold": 0.80,
    "track": "quality",
    "description": "Challenger recall",
}
```

The shipped benchmark template currently exposes only summary keys such as `min_recall` and `max_false_positive_rate`. Phase 2 should normalize this into one supported policy contract and remove ambiguity about where benchmark thresholds originate.

Databricks bundle guidance matters here: use workspace-backed bundle assets for deployed jobs and pipelines, and do not rely on bundle `git_source` for job tasks. GitHub is still relevant for package installation and operator documentation, but the deployed bundle resources should point at workspace assets produced by the bundle itself.

## Problem-State Table

| Aspect | Current State | Target State |
|--------|---------------|--------------|
| Bundle deployability | Root bundle exists, but resources are empty comments | `databricks bundle validate` succeeds against real job and pipeline resources |
| Notebook execution | All seven notebooks raise the same DS-IP-001 Phase 2 runtime error | Each notebook runs real package code with deterministic defaults and explicit parameters |
| Benchmark policy source | `_DEFAULT_GATES` in code diverges from `templates/benchmark_policy.yml` | One normalized policy path drives benchmark threshold evaluation |
| Deployment docs | Guide documents scaffold validation and future-state commands only | Guide documents real GitHub-to-Databricks install and deploy paths |
| Exit evidence | No proof yet that the repo can deploy into a clean workspace from GitHub | Local validation plus bundle validation, and workspace deploy evidence when credentials are available |

## Pre-Flight Checks

1. **Confirm the local baseline is green before editing.**

   ```bash
   cd "$(git rev-parse --show-toplevel)" && make test
   ```

   Expected: command exits with status `0`.

2. **Confirm the current Phase 2 scaffolds are still present.**

   ```bash
   cd "$(git rev-parse --show-toplevel)" && rg -n "DS-IP-001 Phase 2|Current status|_DEFAULT_GATES|benchmark_policy:" notebooks resources src/driftsentinel docs/deployment_guide.md templates/benchmark_policy.yml
   ```

   Expected: matches in all seven notebooks, all three resource files, `src/driftsentinel/benchmark/orchestrator.py`, and `templates/benchmark_policy.yml`.

3. **Confirm the Databricks CLI is available before claiming bundle validation.**

   ```bash
   databricks --version
   ```

   Expected: Databricks CLI `v0.218.0` or newer.

4. **Confirm the progress files exist and can be reused for Phase 2 state tracking.**

   ```bash
   cd "$(git rev-parse --show-toplevel)" && test -f progress.json && test -f progress.txt && echo "progress files present"
   ```

   Expected: `progress files present`.

## Instructions

### Phase 1: Re-Baseline The Work And Fix The Benchmark Policy Mismatch First

1. **Update `progress.json` and `progress.txt` for Phase 2 instead of creating new tracking files.**

   Change the recorded phase to `Phase 2 - Databricks MVP Packaging`, add the four Phase 2 acceptance criteria, and record the benchmark-threshold normalization item as the first subtask.

   *Success: both progress files explicitly describe Phase 2 packaging and the benchmark policy normalization task.*

   **Rationale:** Complex packaging work is already being tracked in-repo; duplicating state would make verification less reliable.

2. **Read the exact edit surface in parallel before the first substantive edit.**

   Read `${REPO_ROOT}/databricks.yml`, all three files under `${REPO_ROOT}/resources/`, all seven files under `${REPO_ROOT}/notebooks/`, `${REPO_ROOT}/docs/deployment_guide.md`, `${REPO_ROOT}/src/driftsentinel/config/loader.py`, `${REPO_ROOT}/src/driftsentinel/benchmark/orchestrator.py`, `${REPO_ROOT}/src/driftsentinel/orchestration/runner.py`, and the packaging-related tests you will extend or create.

   *Success: you can restate the current stub behavior, the benchmark-gate mismatch, and the planned file list without guessing.*

3. **Normalize benchmark gate sourcing before working on bundle resources or notebooks.**

   Make `${REPO_ROOT}/templates/benchmark_policy.yml`, `${REPO_ROOT}/src/driftsentinel/config/loader.py`, and `${REPO_ROOT}/src/driftsentinel/benchmark/orchestrator.py` agree on one policy contract. Prefer explicit gate definitions or a deterministic normalization helper, but remove the split-brain state where template keys and evaluator keys diverge.

   *Success: benchmark execution can consume template-backed policy thresholds without falling back to ambiguous inline defaults.*

   **Rationale:** This mismatch is already identified as a residual Phase 1 defect and will contaminate notebook and Databricks behavior if left unresolved.

4. **Run the narrow validation for the benchmark-policy slice immediately after the first substantive edit.**

   ```bash
   cd "$(git rev-parse --show-toplevel)" && uv run pytest tests/test_config_loading.py tests/test_benchmark.py tests/test_orchestration.py
   ```

   *Success: the command exits with status `0` before you widen scope to Databricks resources and notebooks.*

### Phase 2: Create The Minimal Operational Databricks Packaging Surface

5. **Make `databricks.yml` operational, but only add variables and settings that the resource files truly consume.**

   Keep the bundle root simple. Preserve the existing `catalog` and `schema` variables, add only the additional variables required for resource naming, notebook parameters, or workspace destinations, and keep authentication external to the repo.

   *Success: the bundle root remains concise, references only real resource files, and introduces no secrets or dead variables.*

   **Rationale:** Phase 2 is packaging, not speculative platform design; every new variable must earn its place.

6. **Replace the three comment-only resource stubs with real Databricks resources under `resources/`.**

   Implement `${REPO_ROOT}/resources/intake_pipeline.yml` as a real pipeline resource and implement `${REPO_ROOT}/resources/drift_gate_job.yml` plus `${REPO_ROOT}/resources/benchmark_job.yml` as real job resources. Use workspace-backed assets created by the bundle, not bundle `git_source`, and point notebook tasks at the deployed notebook files.

   *Success: each resource file contains a valid Databricks `resources:` mapping with deployable job or pipeline definitions rather than comments only.*

   **Rationale:** Databricks bundle guidance explicitly discourages bundle job `git_source`; deployed workspace assets are the stable source of truth.

7. **Add only the minimal package-facing orchestration helper needed to keep notebooks thin.**

   If the existing orchestration layer is too Phase-1-local, add a small helper module under `${REPO_ROOT}/src/driftsentinel/orchestration/` that handles policy loading, deterministic defaults, Databricks-friendly parameter mapping, and evidence output routing. Do not duplicate domain logic inside notebook files.

   *Success: notebook code becomes a thin wrapper over first-party package APIs rather than a second implementation of intake, drift, or benchmark logic.*

### Phase 3: Activate The Notebook Entry Points

8. **Replace the fail-closed `RuntimeError` stubs in all seven notebooks with real Databricks notebook flows.**

   Update `${REPO_ROOT}/notebooks/00_quickstart_setup.py`, `${REPO_ROOT}/notebooks/01_register_dataset.py`, `${REPO_ROOT}/notebooks/02_seed_or_import_baseline.py`, `${REPO_ROOT}/notebooks/03_run_intake_controls.py`, `${REPO_ROOT}/notebooks/04_run_drift_gate.py`, `${REPO_ROOT}/notebooks/05_run_control_benchmark.py`, and `${REPO_ROOT}/notebooks/06_review_evidence.py` so they gather parameters, resolve or install the package, call the local `driftsentinel` code paths, and print or persist structured results.

   *Success: no notebook raises the DS-IP-001 Phase 2 runtime error, and each notebook reaches real package code.*

9. **Use Databricks notebook source features deliberately instead of inventing a second runtime contract.**

   Use notebook widgets for operator parameters, and if package installation is necessary, add a Databricks-compatible install cell in notebook-source format such as `# MAGIC %pip ...` plus Python restart guidance where required. Keep the install choice explicit and reproducible.

   *Success: notebook parameters are visible, deterministic defaults exist, and package resolution does not depend on local machine paths.*

   **Rationale:** The exit criterion is deployment from GitHub into a clean workspace, so notebook startup cannot assume a preloaded local repo clone.

10. **Implement the GitHub-backed package path and the workspace-backed bundle path as the two documented install modes.**

   Support a direct GitHub package install path appropriate for notebook setup, and support the workspace-backed bundle deployment path for Databricks jobs and pipelines. Do not add bundle job `git_source` merely to reference notebooks from GitHub.

   *Success: the notebooks and docs support both a GitHub-origin package-install mode and a bundle-workspace execution mode without conflicting source rules.*

### Phase 4: Document The Deployment Paths And Add Packaging Tests

11. **Rewrite `${REPO_ROOT}/docs/deployment_guide.md` from scaffold language to Phase 2 operational guidance.**

   Document the real GitHub-to-Databricks paths, including at minimum: local clone plus bundle validate/deploy/run, and direct notebook package installation from GitHub for workspace onboarding. Preserve truthfulness about any steps that still depend on Databricks credentials, workspace files, or Unity Catalog setup.

   *Success: the deployment guide contains concrete commands for real Phase 2 usage and no longer describes the notebooks as expected failures.*

12. **Add focused packaging tests instead of relying on manual inspection.**

   Add or extend tests so they verify at minimum: the benchmark policy normalization path, the absence of the Phase 2 runtime error text in notebook sources, the presence of real Databricks `resources:` mappings in the three bundle files, and the existence of referenced notebook paths or orchestration entry points.

   *Success: packaging regressions are checked by pytest instead of being left to manual review.*

   **Rationale:** DS-TP-001 explicitly requires integration-style checks for bundle resources and notebook orchestration.

13. **Run the focused packaging validation before the full suite.**

   ```bash
   cd "$(git rev-parse --show-toplevel)" && uv run pytest tests/test_config_loading.py tests/test_benchmark.py tests/test_orchestration.py tests/test_scaffold_layout.py tests/test_governance_guards.py
   ```

   If you add a dedicated packaging test file, include it in this command.

   *Success: the touched slices pass before you spend time on the broader verification run.*

### Phase 5: Verify Against The Real Exit Criterion

14. **Run the full local verification suite required by repository policy.**

   ```bash
   cd "$(git rev-parse --show-toplevel)" && make lint && make typecheck && make test
   ```

   *Success: lint, typecheck, and tests all exit with status `0`.*

15. **Run the placeholder scan explicitly because notebook and docs rewrites are susceptible to regressions.**

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

16. **Run bundle validation locally and treat failures as real defects, not postscript notes.**

   ```bash
   cd "$(git rev-parse --show-toplevel)" && databricks bundle validate
   ```

   *Success: bundle validation exits with status `0` and reports no unknown resource-property warnings caused by your edits.*

17. **Attempt the clean-workspace deployment proof if Databricks authentication and target access are available.**

   ```bash
   cd "$(git rev-parse --show-toplevel)" && databricks bundle deploy --target dev
   ```

   Then run the deployed workflow surface that best proves the packaging path, using the real resource key you created.

   *Success: deployment into the target workspace completes, and at least one deployed resource runs from the bundle-managed workspace assets.*

   **Rationale:** The Phase 2 exit criterion is deployment into a clean Databricks workspace from GitHub, so local-only proof is necessary but not sufficient when credentials are available.

18. **If workspace deploy cannot be executed because credentials, profile, or workspace access are unavailable, mark the exit criterion as `unverified` instead of `passed`.**

   Record exactly which external prerequisite blocked the deploy run and keep the local evidence separate from the missing external proof.

   *Success: the final report distinguishes verified local packaging facts from blocked external deployment proof.*

### Phase 6: Security And Quality Gates

19. **Run Snyk code analysis on the repository root after the first-party code and notebook changes land.**

   Execute `snyk_code_scan` against `${REPO_ROOT}`.

   *Success: no new high-severity code issues are introduced, or any findings are explicitly resolved before completion.*

20. **Run Snyk IaC analysis on the bundle surfaces after the resource files are operational.**

   Execute `snyk_iac_scan` against `${REPO_ROOT}/resources` or the repo root if the scan needs the full bundle context.

   *Success: the Databricks YAML surfaces pass IaC review or any findings are resolved before completion.*

## Guardrails

<guardrails>
- Keep Phase 2 focused on packaging and execution wiring. Do not begin Phase 3 multi-dataset hardening, Phase 4 app work, or marketplace work.
- Do not use Databricks bundle `git_source` or task `source: GIT` for the bundle jobs unless you can prove a repo-specific need that outweighs the Databricks guidance against it.
- Do not leave business logic duplicated inside notebook files; call `src/driftsentinel/` code instead.
- Do not add secrets, workspace hostnames, tokens, or profile-specific credentials to repository files.
- Do not preserve the benchmark `_DEFAULT_GATES` fallback in a way that still overrides template-backed policy silently.
- Do not claim clean-workspace deployment success without a real `databricks bundle deploy` result or equivalent measured evidence.
- Keep new dependencies to the minimum. Prefer the existing package plus Databricks runtime primitives unless a dependency is strictly required.
- Preserve append-only evidence behavior and explicit failure behavior; missing prerequisites must fail clearly rather than silently degrading.
</guardrails>

## Verification Checklist

- [ ] `progress.json` and `progress.txt` are updated to Phase 2 state
- [ ] Benchmark policy loading and benchmark gate evaluation use one normalized contract
- [ ] `databricks.yml` remains concise and operational
- [ ] `resources/intake_pipeline.yml` defines a real pipeline resource
- [ ] `resources/drift_gate_job.yml` defines a real job resource
- [ ] `resources/benchmark_job.yml` defines a real job resource
- [ ] All seven notebooks execute real package code and no longer raise the DS-IP-001 Phase 2 runtime error
- [ ] `docs/deployment_guide.md` documents real GitHub-to-Databricks install and deploy paths
- [ ] Packaging-focused pytest coverage exists for bundle resources and notebook activation
- [ ] `make lint` passes
- [ ] `make typecheck` passes
- [ ] `make test` passes
- [ ] Placeholder scan passes
- [ ] `databricks bundle validate` passes
- [ ] Snyk code scan is run and addressed
- [ ] Snyk IaC scan is run and addressed
- [ ] Clean-workspace deploy proof is recorded as verified or explicitly `unverified` with the blocker named

## Error Handling

| Error Condition | Resolution |
|-----------------|------------|
| Benchmark template keys still do not map to evaluator gate dicts | Add a deterministic normalization helper or revise the template schema so the loader returns the evaluator’s expected gate definitions directly. |
| `databricks bundle validate` fails on unknown keys | Remove the unsupported fields and re-check the resource definition against the official Databricks bundle docs before retrying. |
| Notebook imports fail in Databricks because the package is unavailable | Add or repair the explicit GitHub-backed install cell or workspace-backed resolution path, then rerun the notebook-oriented verification. |
| Bundle jobs reference notebook paths incorrectly | Convert the task paths to the correct bundle-workspace-relative or workspace-absolute form supported by the chosen resource pattern, then rerun bundle validation. |
| Databricks CLI is unavailable or too old | Upgrade or install the Databricks CLI first, then rerun bundle validation and deployment steps. |
| Databricks authentication or target workspace access is unavailable | Complete all local verification, mark the deploy exit criterion `unverified`, and report the exact missing credential or profile prerequisite. |
| Snyk tooling is unavailable in the environment | Record the security step as blocked by tool availability rather than claiming a pass. |

## Out Of Scope

- Phase 3 multi-dataset hardening, registry expansion, or policy versioning
- Phase 4 Databricks App UI work
- Marketplace listing or provider-profile work
- Broad refactors of already-passing Phase 1 domain code unrelated to packaging
- New external integrations beyond the Databricks and documentation surfaces required for Phase 2

## Report Format

1. **Outcome:** State whether Phase 2 packaging is locally verified, workspace verified, or partially verified.
2. **Files changed:** List the edited bundle, notebook, source, test, and docs files.
3. **Benchmark policy normalization:** Describe the final benchmark gate contract and where it is loaded.
4. **Databricks packaging:** State which resources were created and which notebook or package entry points they call.
5. **Verification evidence:** Report the exact results of `make lint`, `make typecheck`, `make test`, placeholder scan, `databricks bundle validate`, and any deploy/run commands attempted.
6. **Security evidence:** Report Snyk code and IaC results, or the blocking reason if they could not run.
7. **Exit criterion status:** State whether “repo deploys into a clean Databricks workspace from GitHub” is verified or `unverified`, and cite the evidence or blocker.
8. **Residual risks:** List only the concrete risks or manual prerequisites that remain after the implementation.
