# drift

Distribution drift detection module derived from Chapter 2 (Silent Failure
Prevention).

Responsibilities:
- Shannon entropy-based distribution stability scoring
- Windowed trend analysis for gradual drift detection
- Publication gate logic (pass/warn/fail decisions)
- Column-level drift diagnostics with per-column evidence

Implemented in DS-IP-001 Phase 1. Key files: `entropy.py`, `baseline.py`,
`detection.py`, `gates.py`, `sample_data.py`.
