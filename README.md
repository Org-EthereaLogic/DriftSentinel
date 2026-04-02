# DriftSentinel

**Enterprise Data Trust — Chapter 4: Unified Drift Monitoring Application**

Built by Anthony Johnson | EthereaLogic LLC

---

DriftSentinel establishes the standalone repository, governance layer, and
Databricks delivery surfaces that unify the three Enterprise Data Trust
control patterns into one application. DS-IP-001 Phase 4 is implemented: the
repo ships a multi-dataset registry, version-aware policy binding, queryable
evidence lookup, dataset-aware orchestration, Databricks bundle resources with
notebook entry points, and a Gradio-based Databricks App for read-only
operator review.

## What this repository contains

| Surface | Purpose |
| ------- | ------- |
| `src/driftsentinel/` | First-party product code for intake, drift, benchmark, evidence, and orchestration |
| `app/` | Databricks App UI (Gradio) for operator dashboard — registry, run status, evidence explorer |
| `assets/` | Project brand assets — SVG sources, exported icons, favicons, and social preview images |
| `notebooks/` | Onboarding, execution, and evidence-review notebooks for Databricks |
| `resources/` | Databricks Asset Bundle pipeline, job, and app definitions |
| `templates/` | Dataset contract, drift policy, and benchmark policy templates |
| `specs/` | Canonical SDLC documents governing the product |
| `docs/` | Explanatory docs, deployment guide, and Notion sync policy |
| `scripts/` | Operational helper scripts, including the Databricks App deploy helper |
| `tests/` | Product test suite for domain logic, packaging, and governance |
| `.claude/` | Agent, command, hook, and configuration surfaces for agentic development |
| `report/` | Append-only evidence artifacts from verification and control runs |
| `adws/` | Reserved for AI Developer Workflows |

Every directory listed above contains a `README.md` describing its contents,
including each submodule under `src/driftsentinel/`.

## Quickstart

```bash
git clone https://github.com/Org-EthereaLogic/DriftSentinel.git
cd DriftSentinel

make sync   # installs runtime + dev dependencies via uv
make test   # runs the pytest suite
```

### Databricks Catalog And Bundle Validation

```bash
# First prove the catalog exists for the profile you will use.
make bundle-catalog-check CATALOG=my_catalog PROFILE=<profile>

# Then validate bundle wiring against that catalog.
make bundle-validate CATALOG=my_catalog PROFILE=<profile>

# Deploy and run the Databricks App from the repo root.
make app-deploy CATALOG=my_catalog PROFILE=<profile>
```

Direct CLI equivalents:

```bash
databricks catalogs get my_catalog -p <profile>
databricks bundle validate -p <profile> --target dev --var="catalog=my_catalog"
databricks bundle deploy -p <profile> --target dev --var="catalog=my_catalog"
databricks apps start driftsentinel -p <profile>
databricks apps deploy -p <profile> --target dev --var="catalog=my_catalog"
databricks apps get driftsentinel -p <profile> -o json
```

`bundle validate` proves bundle/auth/resource resolution. It does not by itself
prove the catalog exists or that deploy/run succeeded. `bundle deploy` creates
the app resource, but the Databricks App source is deployed and started through
`make app-deploy`. The raw CLI path is a sequence, not a single command, and
`databricks apps get` is the proof surface for `SUCCEEDED` plus `RUNNING`.

Deploy and run with the same catalog selection to prove the deployment path:

```bash
databricks bundle deploy -p <profile> --target dev --var="catalog=my_catalog"

databricks bundle run benchmark_job -p <profile> --target dev --var="catalog=my_catalog"
```

### Manual workspace import

Import the `notebooks/` directory into your Databricks workspace to run the
package either from the deployed bundle files or, when run standalone, from
GitHub. The notebooks ship with bundled example templates, and
`01_register_dataset.py` plus `05_run_control_benchmark.py` also accept
optional workspace YAML paths if you import customized files from `templates/`.

## Part of a series

This is **Chapter 4** of the *Enterprise Data Trust* portfolio.

| Chapter | Focus | Repository |
|---------|-------|------------|
| 1. Trusted Source Intake | Validate and certify data before downstream consumption | [trusted-source-intake](https://github.com/Org-EthereaLogic/trusted-source-intake) |
| 2. Silent Failure Prevention | Detect distribution drift before it reaches executive dashboards | [silent-failure-prevention](https://github.com/Org-EthereaLogic/silent-failure-prevention) |
| 3. Measurable Control Effectiveness | Prove that your data controls work against known failure scenarios | [measurable-control-effectiveness](https://github.com/Org-EthereaLogic/measurable-control-effectiveness) |
| **4. DriftSentinel** | Unified application combining all three control patterns | ← You are here |

---

<p align="left">
  <a href="https://github.com/Org-EthereaLogic/DriftSentinel/actions/workflows/ci.yml"><img src="https://github.com/Org-EthereaLogic/DriftSentinel/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://app.codacy.com/gh/Org-EthereaLogic/DriftSentinel/dashboard"><img src="https://img.shields.io/badge/codacy-dashboard-blue" alt="Codacy dashboard"></a>
  <a href="https://codecov.io/gh/Org-EthereaLogic/DriftSentinel"><img src="https://codecov.io/gh/Org-EthereaLogic/DriftSentinel/graph/badge.svg" alt="Codecov coverage"></a>
</p>

MIT License. See [LICENSE](LICENSE) for details.
