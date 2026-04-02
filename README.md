# DriftSentinel

**Enterprise Data Trust — Chapter 4: Unified Drift Monitoring Application**

Built by Anthony Johnson | EthereaLogic LLC

---

DriftSentinel establishes the standalone repository, governance layer, and
Databricks scaffold that will unify the three Enterprise Data Trust control
patterns into one application. Phase 0/1 validates repository integrity,
bundle surfaces, and notebook entry points; DS-IP-001 Phase 2 adds runnable
Databricks workflows and evidence-producing execution.

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

### Databricks scaffold validation

```bash
# If your Databricks CLI default profile is already configured:
databricks bundle validate

# Or choose a specific Databricks CLI profile explicitly:
DATABRICKS_CONFIG_PROFILE=<profile> databricks bundle validate
```

Phase 0/1 validates the bundle scaffold only. The repository does not yet ship
operational Databricks jobs or pipelines; Phase 2 adds runnable bundle
resources.

### Manual workspace import

Upload the `notebooks/` directory to your Databricks workspace to inspect the
planned entry points. The current scaffold notebooks fail closed with an
explicit DS-IP-001 Phase 2 runtime error until implementation lands.

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
