# Day 3 — E2E Verification Summary (v2 — Post-UI Overhaul)

## Tasks Completed
- [x] Task 3.1 — Ran drift demo, verified provenance with overall_verdict=FAIL
- [x] Task 3.2 — Wrote drift evidence for meridian_project_costs
- [x] Task 3.3 — Date filter: Date To=2026-04-01 correctly excludes all artifacts
- [x] Task 3.4 — Run ID prefix filter: "dcf61792" returns exactly 1 artifact
- [x] Task 3.5 — Ran second dataset pipeline for meridian_labor_hours

## Issues Found

### ISSUE-3.1 — Run ID prefix filter does exact match instead of prefix match
- **Severity:** high
- **Category:** backend
- **Description:** `list_evidence` in `writer.py:270` does `meta.get("run_id") != run_id` (exact match) but UI label says "Run ID prefix" and displays truncated 8-char IDs
- **Resolution:** Changed to `not (meta.get("run_id") or "").startswith(run_id)` for prefix matching
- **Verification:** Re-launched app, prefix filter "dcf61792" now returns the matching drift artifact
- **Files changed:** src/driftsentinel/evidence/writer.py

## Visual Verifications
- 9 artifacts with verdict summary "9 artifacts | PASS: 4 | FAIL: 5"
- Drift artifact visible: Kind=drift, Verdict=FAIL, Run ID=dcf61792
- Date filter exclusion produces clean "(no artifacts found)" state
- Run ID prefix filter isolates single artifact correctly
