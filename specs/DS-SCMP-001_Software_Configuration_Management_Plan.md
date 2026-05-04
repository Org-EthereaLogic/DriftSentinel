# DS-SCMP-001: DriftSentinel Software Configuration Management Plan

| Field | Value |
| --- | --- |
| Document ID | DS-SCMP-001 |
| Version | 1.1 |
| Status | Draft |
| Author | Anthony Johnson |
| Date | 2026-05-04 |

## 1. Repository Model

- Primary branch: `main`
- Feature work: short-lived feature and fix branches

## 2. Controlled Items

| Item Type | Location |
| --- | --- |
| Product code | `src/driftsentinel/` |
| Tests | `tests/` |
| Deployment assets | `databricks.yml`, `resources/`, `notebooks/`, `templates/` |
| Canonical SDLC docs | `specs/` |
| Narrative docs | `docs/` |
| Claude commands, agents, hooks | `.claude/` |
| Workflow orchestration | `adws/` |
| Evidence artifacts | `report/` |
| Quality-control integration | `.github/`, `.codacy/`, `codecov.yaml`, `.snyk` |
| External coordination | GitHub Issues + DriftSentinel Roadmap Project (#8) |

## 3. Change Rules

- `specs/` is canonical and version-controlled
- `docs/` must not override `specs/`
- Evidence artifacts are append-only
- Secrets must never be committed
- Codacy, Codecov, and Snyk are pre-implementation gates
- Repository-secret names are documented; token values are never stored
- GitHub Project IDs and field option IDs must never be invented; only those confirmed via the API are used

## 4. Changelog

| Version | Date | Change |
| --- | --- | --- |
| 1.1 | 2026-05-04 | Replaced Notion dashboard with GitHub Issues + Project (#8) as external coordination surface (§2, §3) following governance migration in commit 78bdf82 |
| 1.0 | 2026-04-01 | Initial draft |
