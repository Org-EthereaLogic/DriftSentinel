# DriftSentinel

**Enterprise Data Trust — Chapter 4: Unified Drift Monitoring Application**

Built by Anthony Johnson | EthereaLogic LLC

---

DriftSentinel productizes the three Enterprise Data Trust control patterns into
a single Databricks application. Users download one repository, configure it
for their own datasets, and run intake certification, drift gating, and control
benchmarking with replayable evidence.

## What this repository contains

| Surface | Purpose |
| ------- | ------- |
| `src/driftsentinel/` | First-party product code for intake, drift, benchmark, evidence, and orchestration |
| `notebooks/` | Onboarding, execution, and evidence-review notebooks for Databricks |
| `resources/` | Databricks Asset Bundle pipeline and job definitions |
| `templates/` | Dataset contract, drift policy, and benchmark policy templates |
| `specs/` | Canonical SDLC documents governing the product |
| `.claude/` | Agent, command, hook, and configuration surfaces for agentic development |
| `report/` | Append-only evidence artifacts from verification and control runs |

## Quickstart

```bash
git clone https://github.com/Org-EthereaLogic/DriftSentinel.git
cd DriftSentinel

make sync   # installs runtime + dev dependencies via uv
make test   # runs the pytest suite
```

### Databricks deployment

```bash
databricks bundle validate
databricks bundle deploy --target dev
```

### Manual workspace import

Upload the `notebooks/` directory to your Databricks workspace and follow
`00_quickstart_setup.py`.

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
  <a href="https://app.codacy.com/gh/Org-EthereaLogic/DriftSentinel/dashboard"><img src="https://app.codacy.com/project/badge/Grade/placeholder" alt="Codacy grade"></a>
  <a href="https://codecov.io/gh/Org-EthereaLogic/DriftSentinel"><img src="https://codecov.io/gh/Org-EthereaLogic/DriftSentinel/graph/badge.svg" alt="Codecov coverage"></a>
</p>

MIT License. See [LICENSE](LICENSE) for details.
