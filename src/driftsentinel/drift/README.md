# drift

Distribution drift detection module derived from Chapter 2 (Silent Failure
Prevention).

Responsibilities:
- Method-aware distribution stability scoring
  (`shannon_entropy` and `wasserstein` for numeric/datetime columns)
- Windowed trend analysis for gradual drift detection
- Publication gate logic (pass/warn/fail decisions)
- Column-level drift diagnostics with per-column evidence

Implemented in DS-IP-001 Phase 1. Key files: `entropy.py`, `baseline.py`,
`detection.py`, `gates.py`, `sample_data.py`, `scoring.py`.
