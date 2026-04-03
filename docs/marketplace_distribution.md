# DriftSentinel Marketplace Distribution Preparation

## Phase 5 Scope

DriftSentinel Phase 5 is a commercialization-preparation phase, not a product
rewrite. The canonical exit criterion in `specs/DS-IP-001_Implementation_Plan.md`
is to prepare provider-profile and listing material so distribution channels can
be put in place without changing the product core.

This packet stays within that boundary:

- It reuses existing repository proof for bundle validation, deployment, job
  execution, and Databricks App deployment readiness.
- It prepares provider and listing draft material from current repo-backed
  behavior and evidence.
- It records blocked external steps instead of implying that a live Databricks
  Marketplace provider or listing already exists.

The following remain out of scope for this packet:

- product-core changes under `src/driftsentinel/`, `app/`, `resources/`, or
  `notebooks/`
- pricing, legal terms, and billing policy invention
- live provider creation, listing creation, or listing submission

## Provider Profile Draft

| Field | Draft Value | Basis |
| --- | --- | --- |
| Product name | `DriftSentinel` | Repository name, `pyproject.toml`, canonical specs |
| Organization reference | `EthereaLogic LLC` | Root `README.md` credits |
| Legal provider display name | `operator input required` | The repo names an organization, but it does not define the exact legal Marketplace provider entity |
| Provider summary | `Standalone Databricks application that unifies intake certification, drift gating, and control benchmarking with replayable evidence.` | `specs/DS-PRD-001_Product_Requirements_Document.md`, root `README.md` |
| Primary support contact | `operator input required` | No canonical support mailbox is defined in the repo |
| Support URL | `operator input required` | No support portal URL is defined in the repo |
| Provider icon candidate | `assets/driftsentinel-brand-system/icons/driftsentinel-mark-512.png` | Existing brand asset sized for square icon use |
| Provider logo candidate | `assets/driftsentinel-brand-system/icons/driftsentinel-logo-1200x320.png` | Existing repository-managed wordmark asset |
| Provider workspace baseline | `Paid Databricks workspace with Unity Catalog` | `specs/DS-SRS-001_Software_Requirements_Specification.md` |
| App workspace requirement | `Premium workspace required for the Databricks App surface` | `app/README.md`, `docs/deployment_guide.md` |

## Listing Material Draft

### Listing Title

`DriftSentinel`

### Short Description

`Unified Databricks application for intake certification, drift gating, and control benchmarking with replayable evidence.`

### Detailed Description

DriftSentinel packages the three Enterprise Data Trust control patterns into a
single Databricks-deliverable repository. The current product surface supports
declarative dataset registration, intake certification, drift gating, control
benchmarking, and append-only evidence capture from one first-party codebase.

Current operator surfaces include:

- Databricks Asset Bundle resources for intake, drift-gate, and benchmark runs
- notebook-first onboarding and execution flow for evaluation
- a read-only Gradio-based Databricks App with Registry, Run Status, Evidence
  Explorer, and Analytics views

Current proof in this repository shows that the bundle can validate, deploy,
run the benchmark job, and destroy resources against a real Unity Catalog
catalog in the verified `e62-trial` workspace path. That proof supports
commercialization preparation, but it is not the same as a live Marketplace
publication.

### Installation And Delivery Notes

| Topic | Draft Copy |
| --- | --- |
| Delivery method | `Repository-backed Databricks deployment via Asset Bundles and notebook import path.` |
| Bundle path | `Use the GitHub repository with an existing Unity Catalog catalog, then validate, deploy, and run through the documented Databricks CLI workflow.` |
| Notebook path | `Import notebooks directly into a workspace for evaluation when the bundle path is not being used.` |
| Databricks App | `Deploy from the repository root so the local driftsentinel package is installed from this repo.` |
| Pricing model | `operator input required` |
| Marketplace category and tags | `operator input required` |
| Trial terms or entitlement policy | `operator input required` |

## Prerequisites And Workspace Requirements

| Requirement | Why It Matters | Source |
| --- | --- | --- |
| Paid Databricks workspace with Unity Catalog | Required baseline for Marketplace provider operations and bundle-backed deployment | `specs/DS-SRS-001_Software_Requirements_Specification.md` |
| Existing Unity Catalog catalog | Required input to the documented bundle validation and deployment path | `specs/DS-BI-001_Build_Instructions.md`, `docs/deployment_guide.md` |
| Premium workspace | Required for the Databricks App deployment surface | `app/README.md`, `docs/deployment_guide.md` |
| Python 3.11+ / DBR 14.3 LTS or later | Current deployment and notebook guidance assumes this runtime floor | `pyproject.toml`, `docs/deployment_guide.md` |
| Databricks CLI authentication | Required for bundle validation, deployment, and app deployment commands | `specs/DS-BI-001_Build_Instructions.md` |

Notes:

- `databricks bundle validate` proves bundle, auth, and resource resolution. It
  does not prove catalog existence or successful deployment by itself.
- Free Edition remains a supported notebook-first evaluation path, but the
  Databricks App and Marketplace provider operations both require paid-workspace
  capabilities.

## Asset Inventory

The detailed asset manifest lives in
`assets/driftsentinel-brand-system/marketplace/README.md`.

| Status | Asset | Current Repo Path |
| --- | --- | --- |
| available now | Primary wordmark | `assets/driftsentinel-brand-system/icons/driftsentinel-logo-1200x320.png` |
| available now | Square product mark | `assets/driftsentinel-brand-system/icons/driftsentinel-mark-512.png` |
| available now | Transparent and light/dark logo variants | `assets/driftsentinel-brand-system/variants/` |
| available now | Social preview graphics | `assets/driftsentinel-brand-system/social/` |
| available now | App screenshots — all 4 dashboard tabs (2x retina, dark mode) | `assets/driftsentinel-brand-system/marketplace/screenshots/` |

## Submission Checklist

| Item | Status | Notes |
| --- | --- | --- |
| Reconcile stale bundle-blocker claim against current repo evidence | complete | Existing bundle proof shows the blocker is closed for current planning |
| Draft provider profile in-repo | complete | This document provides the provider-profile draft |
| Draft listing material in-repo | complete | This document provides the listing copy and delivery notes |
| Create asset manifest in-repo | complete | `assets/driftsentinel-brand-system/marketplace/README.md` |
| Update README discovery | complete | Root `README.md` points to this packet |
| Update sprint coordination live in Notion | complete | Phase 5 moved to "In Progress" in Notion Tasks (2026-04-03) |
| Bundle validation against real catalog | complete | `make bundle-validate CATALOG=adb_dev PROFILE=e62-trial` passed. Evidence: `report/2026-04-03T01-40-bundle-validation-evidence.md` |
| App screenshots for listing gallery | complete | 4 retina screenshots (dark mode, populated data) in `assets/driftsentinel-brand-system/marketplace/screenshots/` |
| Databricks Partner application | pending review | Operator-reported submission on 2026-04-02 as Services Partner (C&SI). No repository artifact independently proves the external submission. Marketplace provider setup remains blocked until partner approval and paid workspace provisioning. |
| Inspect Marketplace provider/listing readiness read-only | blocked by workspace tier | Free Edition workspace does not support Account Console or Marketplace provider enablement. Requires paid (Premium/Enterprise) or partner NFR workspace. |
| Create provider or listing | blocked by partner approval | No irreversible Marketplace mutation was attempted |
| Final legal, pricing, and support metadata | operator input required | Business-owned fields are not defined in the repo |

## Operator Input Required

- Exact legal provider display name for Databricks Marketplace publication
- Support contact email, support URL, and escalation path
- Pricing model, entitlement model, and any trial policy
- Marketplace category, tags, and exchange-distribution strategy
- Privacy policy, terms of use, and any compliance or legal URLs required by
  listing submission
- Explicit approval before any live provider, listing, asset-upload, or submit
  action

## Evidence References

- `specs/DS-IP-001_Implementation_Plan.md`
  Phase 5 scope and exit criterion
- `specs/DS-PRD-001_Product_Requirements_Document.md`
  Marketplace provider operations are not a Version 1 release blocker
- `specs/DS-SRS-001_Software_Requirements_Specification.md`
  Paid workspace plus Unity Catalog requirement for provider operations
- `specs/DS-BI-001_Build_Instructions.md`
  Catalog check and bundle validation semantics
- `docs/deployment_guide.md`
  Verified deployment, app deployment, and runtime prerequisites
- `app/README.md`
  Read-only App behavior and Premium workspace requirement
- `resources/driftsentinel_app.yml`
  Current app resource name, description, and source path
- `report/2026-04-02T07-36-36Z-bundle-proof-reconciliation.md`
  Current replayable bundle proof
- `report/2026-04-02T23-23-notion-sync-record.md`
  Verified Phase 5 `Not Started` state plus missing current sprint
- `report/2026-04-03T01-05-notion-sync-record.md`
  Latest verified sprint-gap confirmation before this packet
- `report/2026-04-03T01-40-bundle-validation-evidence.md`
  First successful bundle-validate against adb_dev catalog (e62-trial workspace)
