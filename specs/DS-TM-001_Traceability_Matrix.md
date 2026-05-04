# DS-TM-001: DriftSentinel Traceability Matrix

| Field | Value |
| --- | --- |
| Document ID | DS-TM-001 |
| Version | 1.1 |
| Status | Draft |
| Author | Anthony Johnson |
| Date | 2026-05-04 |

| PRD Requirement | SRS Requirement | Spec Surface | Verification Surface |
| --- | --- | --- | --- |
| DS-FR-001 | DS-SR-001 | PRD, SDD | repo taxonomy, CLAUDE.md, specs/ |
| DS-FR-002 | DS-SR-009 | PRD, SRS | databricks.yml, resources/, bundle validation |
| DS-FR-003 | DS-SR-008 | PRD, SRS | notebooks, manual import path |
| DS-FR-004 | DS-SR-005 | PRD, SRS | templates/, config loaders, registration notebook |
| DS-FR-005 | DS-SR-002 | PRD, SDD | src/driftsentinel/intake/, quarantine outputs |
| DS-FR-006 | DS-SR-003 | PRD, SDD | src/driftsentinel/drift/, gate-evaluation outputs |
| DS-FR-007 | DS-SR-004 | PRD, SDD | src/driftsentinel/benchmark/, evidence bundle writer |
| DS-FR-008 | DS-SR-008 | PRD, SRS | notebooks and evidence review surfaces |
| DS-FR-009 | DS-SR-006 | PRD, TP | bundle deploy checks and manual import validation |
| DS-FR-010 | DS-SR-007, DS-SR-010 | PRD, TP | deterministic demo paths and integration tests |
| DS-FR-011 | DS-SR-011 | PRD, SRS, SCMP | .codacy/, codecov.yaml, .snyk, secret-name docs |
| DS-FR-012 | DS-SR-012 | PRD, SRS, SCMP | docs/github_project_sync.md, /sync command |
| DS-NFR-001 | DS-SNFR-002, DS-SNFR-006 | PRD, SRS, TP | report/, benchmark evidence |
| DS-NFR-002 | DS-SNFR-001 | PRD, SRS | append-only evidence writer and replay tests |
| DS-NFR-003 | DS-SNFR-003 | PRD, SRS | missing-field failure tests, blocked status checks |
| DS-NFR-004 | DS-SNFR-005 | PRD, SRS | Free Edition notebook path, workspace scheduling |
| DS-NFR-005 | DS-SNFR-004 | PRD, SDD, SCMP | specs/, .claude/, adws/, report/ scaffold |
| DS-NFR-006 | DS-SNFR-003 | PRD, SRS | blocked publication tests |
| DS-NFR-007 | DS-SNFR-007 | PRD, SRS | secret scan, .gitignore, CI checks |
| DS-NFR-008 | DS-SNFR-008 | PRD, SRS, WBS | documented pre-coding gate |
| DS-NFR-009 | DS-SNFR-009 | PRD, SRS, TP | non-blocking GitHub Project sync rules |

## Changelog

| Version | Date | Change |
| --- | --- | --- |
| 1.1 | 2026-05-04 | Updated DS-FR-012 and DS-NFR-009 verification surfaces from Notion to GitHub Project (#8) following governance migration in commit 78bdf82 |
| 1.0 | 2026-04-01 | Initial draft |
