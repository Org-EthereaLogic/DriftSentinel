# DS-SRS-001: DriftSentinel Software Requirements Specification

| Field | Value |
| --- | --- |
| Document ID | DS-SRS-001 |
| Version | 1.1 |
| Status | Draft |
| Author | Anthony Johnson |
| Date | 2026-05-04 |

## 1. Functional Requirements

| ID | Traces to | Requirement |
| --- | --- | --- |
| DS-SR-001 | DS-FR-001 | Single repository layout with product code, deployment assets, notebooks, specs, and agent-layer scaffolding |
| DS-SR-002 | DS-FR-005 | First-party intake-control logic derived from Chapter 1 |
| DS-SR-003 | DS-FR-006 | First-party drift-detection and publication-gate logic derived from Chapter 2 |
| DS-SR-004 | DS-FR-007 | First-party benchmark and evidence-writing logic derived from Chapter 3 |
| DS-SR-005 | DS-FR-004 | Declarative dataset registration through config or notebook-driven setup |
| DS-SR-006 | DS-FR-009 | Downstream-safe output surface separate from raw and quarantined surfaces |
| DS-SR-007 | DS-FR-010 | Persist quarantine reasons, replay detection, baseline metadata, drift verdicts, and benchmark evidence |
| DS-SR-008 | DS-FR-003, DS-FR-008 | Onboarding, execution, and evidence-review notebooks |
| DS-SR-009 | DS-FR-002 | Bundle deployment path and manual import path |
| DS-SR-010 | DS-FR-010 | Deterministic demo path for local and workspace validation |
| DS-SR-011 | DS-FR-011 | Pre-implementation Codacy, Codecov, and Snyk setup |
| DS-SR-012 | DS-FR-012 | Evidence-backed GitHub Project (#8) sync policy |

## 2. Non-Functional Requirements

| ID | Traces to | Requirement |
| --- | --- | --- |
| DS-SNFR-001 | DS-NFR-002 | Evidence shall be append-only and audit-friendly |
| DS-SNFR-002 | DS-NFR-001 | Release claims bounded by measured proof from this repository |
| DS-SNFR-003 | DS-NFR-006 | Missing evidence fields force explicit failure or blocked status |
| DS-SNFR-004 | DS-NFR-005 | Separation between canonical specs, explanatory docs, agent prompts, and evidence |
| DS-SNFR-005 | DS-NFR-004 | Notebook-first for Free Edition with clean path to paid-workspace scheduling |
| DS-SNFR-006 | DS-NFR-001 | No runtime dependency on sibling chapter clones |
| DS-SNFR-007 | DS-NFR-007 | No secrets or hard-coded customer data in repository content |
| DS-SNFR-008 | DS-NFR-008 | No coding before quality-control preflight gate is satisfied |
| DS-SNFR-009 | DS-NFR-009 | GitHub Project sync is non-blocking and truthful |

## 3. External Interfaces

- Databricks CLI and Asset Bundles
- Databricks notebooks and workspace import
- Unity Catalog (catalogs, schemas, tables, volumes)
- Local Python tooling for packaging and tests
- GitHub Issues and DriftSentinel Roadmap Project (#8) as external coordination surface

## 4. Assumptions

- Free Edition has strict limits on apps, pipelines, jobs
- Marketplace provider operations require a paid workspace with Unity Catalog
- GitHub Actions secrets: `CODECOV_TOKEN` (preferred) or
  `CODECOV_PROJECT_TOKEN` for backward compatibility, plus
  `SNYK_PROJECT_TOKEN`; `CODACY_PROJECT_TOKEN` is only required if the project
  switches to Codacy client-side upload mode

## 5. Changelog

| Version | Date | Change |
| --- | --- | --- |
| 1.1 | 2026-05-04 | Replaced Notion dashboard with GitHub Issues + Project (#8) as external coordination surface (DS-SR-012, DS-SNFR-009, §3) following governance migration in commit 78bdf82 |
| 1.0 | 2026-04-01 | Initial draft |
