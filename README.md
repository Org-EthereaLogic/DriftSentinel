# DriftSentinel

**Enterprise Data Trust — Chapter 4: Unified Drift Monitoring Application**

Built by Anthony Johnson | EthereaLogic LLC

---

DriftSentinel establishes the standalone repository, governance layer, and
Databricks delivery surfaces that unify the three Enterprise Data Trust
control patterns into one application. DS-IP-001 Phase 2 is implemented:
the repo ships runnable Databricks bundle resources, notebook entry points,
and benchmark evidence-producing execution.

## What this repository contains

| Surface | Purpose |
| ------- | ------- |
| `src/driftsentinel/` | First-party product code for intake, drift, benchmark, evidence, and orchestration |
| `notebooks/` | Onboarding, execution, and evidence-review notebooks for Databricks |
| `resources/` | Databricks Asset Bundle pipeline and job definitions |
| `templates/` | Dataset contract, drift policy, and benchmark policy templates |
| `specs/` | Canonical SDLC documents governing the product |
| `docs/` | Explanatory docs, deployment guide, and Notion sync policy |
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

### Databricks Bundle Validation

```bash
# The bundle requires an existing Unity Catalog catalog.
DATABRICKS_CONFIG_PROFILE=<profile> \
  databricks bundle validate --target dev --var="catalog=my_catalog"
```

Deploy and run with the same catalog selection:

```bash
DATABRICKS_CONFIG_PROFILE=<profile> \
  databricks bundle deploy --target dev --var="catalog=my_catalog"

DATABRICKS_CONFIG_PROFILE=<profile> \
  databricks bundle run benchmark_job --target dev --var="catalog=my_catalog"
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
  <a href="https://app.codacy.com/gh/Org-EthereaLogic/DriftSentinel/dashboard"><img src="https://img.shields.io/badge/codacy-pending-lightgrey" alt="Codacy grade (pending setup)"></a>
  <a href="https://codecov.io/gh/Org-EthereaLogic/DriftSentinel"><img src="https://codecov.io/gh/Org-EthereaLogic/DriftSentinel/graph/badge.svg" alt="Codecov coverage"></a>
</p>

MIT License. See [LICENSE](LICENSE) for details.
