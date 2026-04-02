# benchmark

Control effectiveness benchmarking module derived from Chapter 3 (Measurable
Control Effectiveness).

Responsibilities:
- Running controls against known failure scenarios
- Measuring detection rates, false positive rates, and latency
- Producing benchmark evidence for gate contract evaluation

Implemented in DS-IP-001 Phase 1. Key files: `synthetic.py`, `drift_detectors.py`,
`quality_detectors.py`, `gates.py`, `scoring.py`, `orchestrator.py`.
