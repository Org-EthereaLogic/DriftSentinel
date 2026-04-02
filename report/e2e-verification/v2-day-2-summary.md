# Day 2 — E2E Verification Summary (v2 — Post-UI Overhaul)

## Tasks Completed
- [x] Task 2.1 — Created meridian_project_costs dataset contract
- [x] Task 2.2 — Registered dataset via DatasetRegistry
- [x] Task 2.3 — Verified registration in Gradio (1 row)
- [x] Task 2.4 — Registered meridian_labor_hours (2 rows)
- [x] Task 2.5 — Duplicate registration rejected with clear RegistryError
- [x] Task 2.6 — Ran local pipeline, 6 evidence files written
- [x] Task 2.7 — Ran dataset-aware pipeline for both datasets
- [x] Task 2.8 — Verified evidence in Run Status (6 artifacts, verdict summary)
- [x] Task 2.9 — Filtered by dataset_id=meridian_project_costs (2 results)
- [x] Task 2.11 — Loaded pipeline artifact in Evidence Explorer

## Issues Found

### ISSUE-2.1 — Evidence Explorer metadata preview shows dashes for all fields
- **Severity:** medium
- **Category:** backend
- **Description:** `_extract_artifact_meta` read from `data.get("dataset_id")` (top-level) but evidence envelope nests metadata under `data["meta"]`
- **Resolution:** Fixed `_extract_artifact_meta` to read from `data.get("meta", {})` with fallback to top-level fields
- **Verification:** Re-launched app, metadata preview now shows Dataset, Kind, Run ID, Generated, Verdict correctly
- **Files changed:** app/app.py

## Visual Verifications
- Registry: "2 datasets registered" with both rows populated
- Verdict summary line: "6 artifacts | PASS: 3 | FAIL: 3"
- Formatted timestamps: "Apr 02, 17:26 UTC"
- Truncated Run IDs: "1b84ef4c", "33a0cac0"
- Dataset filter narrows to 2 artifacts for meridian_project_costs
- Evidence Explorer metadata preview: Dataset/Kind/Run ID/Generated/Verdict line
