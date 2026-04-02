# driftsentinel

Unified drift monitoring application combining intake certification, drift
gating, and control benchmarking into a single Databricks-deployable product.

## Module Layout

| Module | Purpose | Source Chapter |
| --- | --- | --- |
| `intake/` | Schema drift detection, duplicate replay blocking, contract validation, quarantine routing | Chapter 1 |
| `drift/` | Distribution drift detection and publication gate logic | Chapter 2 |
| `benchmark/` | Control effectiveness benchmarking against known failure scenarios | Chapter 3 |
| `evidence/` | Append-only evidence artifact writing for auditability | Cross-cutting |
| `orchestration/` | Workflow sequencing for the DriftSentinel control pipeline | Cross-cutting |
| `config/` | Dataset contract, drift policy, and benchmark policy configuration | Cross-cutting |

## Current State

All modules are scaffold stubs (`__init__.py` with docstrings only). Phase 1
(DS-IP-001) will port real implementations from the chapter repositories.
