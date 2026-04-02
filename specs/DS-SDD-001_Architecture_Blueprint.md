# DS-SDD-001: DriftSentinel Architecture Blueprint

| Field | Value |
| --- | --- |
| Document ID | DS-SDD-001 |
| Version | 1.0 |
| Status | Draft |
| Author | Anthony Johnson |
| Date | 2026-04-01 |

## 1. Repository Taxonomy

```text
driftsentinel/
  README.md, AGENTS.md, CLAUDE.md, CONSTITUTION.md, DIRECTIVES.md
  specs/
  docs/
  .claude/ (commands/, agents/, hooks/, settings.json)
  adws/
  report/
  databricks.yml
  resources/
  notebooks/
  templates/
  src/driftsentinel/
  tests/
```

## 2. Layer Model

### Agentic Layer

- `specs/` — canonical SDLC contract
- `.claude/commands/` — 21 reusable task prompts
- `.claude/agents/` — 4 specialized subagent definitions
- `.claude/hooks/` — Claude Code hook handlers
- `CLAUDE.md` — quick-reference operational guide
- `adws/` — reserved for AI Developer Workflows
- `report/` — append-only evidence surface

### Application Layer

- `src/driftsentinel/intake/` — Chapter 1 logic
- `src/driftsentinel/drift/` — Chapter 2 logic
- `src/driftsentinel/benchmark/` — Chapter 3 logic
- `src/driftsentinel/evidence/` — append-only artifact writing
- `src/driftsentinel/orchestration/` — workflow sequencing
- `src/driftsentinel/config/` — dataset and policy configuration
- `resources/` — bundle pipeline and job definitions
- `notebooks/` — onboarding and review surfaces
- `templates/` — dataset and policy templates

## 3. Control Flow

1. Register dataset and policy
2. Seed or import baseline context
3. Run intake certification
4. Run drift gates before publication
5. Run control benchmark when requested
6. Write append-only evidence
7. Review outcomes through notebooks

## 4. Methodology Precedence

1. FailLens_Core
2. E62_Live_Databricks_Bronze_execution
3. E63_Natural-fault_Bronze_validation
4. ADWS_PRO
5. Supporting examples: agentic_coding_template, themegpt-v2.0, chapter repos
