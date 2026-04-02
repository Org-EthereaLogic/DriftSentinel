# audit

Full governance, quality-control integration, and canonical docs audit.

## Variables

scope: $ARGUMENTS

## Instructions

### Phase 1: Context
- Read `CLAUDE.md`, `AGENTS.md`
- Run `git log --oneline -10` and `git branch`
- If `scope` is provided, narrow the audit accordingly

### Phase 2: Governance Compliance
- Run placeholder scan
- Run `uv run ruff check .`
- Confirm `docs/` does not override `specs/` on any canonical claim
- Confirm quality-control files exist: `.github/workflows/ci.yml`, `.codacy/`,
  `codecov.yaml`, `.snyk`

### Phase 3: Product Boundary Verification
- Confirm no runtime dependency on sibling chapter clones
- Confirm `src/driftsentinel/` follows the module taxonomy from `specs/DS-SDD-001`
- Verify `specs/` is current relative to `src/driftsentinel/`

### Phase 4: Test Coverage
- Run `uv run pytest`
- Note overall coverage percentage and any modules below threshold

### Phase 5: Report

Return results as JSON with `audit_date`, `branch`, `scope`,
`overall_status`, `governance`, `product_boundary`, `testing`, and `issues`.
