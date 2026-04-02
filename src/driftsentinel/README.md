# driftsentinel

Unified drift monitoring application combining intake certification, drift
gating, and control benchmarking into a single Databricks-deployable product.

## Module Layout

| Module | Purpose | Source Chapter |
| --- | --- | --- |
| `intake/` | Schema drift detection, duplicate replay blocking, contract validation, quarantine routing | Chapter 1 |
| `drift/` | Distribution drift detection and publication gate logic | Chapter 2 |
| `benchmark/` | Control effectiveness benchmarking against known failure scenarios | Chapter 3 |
| `evidence/` | Append-only evidence artifact writing, metadata tagging, and lookup | Cross-cutting |
| `orchestration/` | Workflow sequencing for the DriftSentinel control pipeline | Cross-cutting |
| `config/` | Dataset contract, drift policy, benchmark policy configuration, and multi-dataset registry | Cross-cutting |

## Current State

Phase 3 (DS-IP-001) is complete. All modules contain first-party implementations
ported from the chapter repositories with no sibling clone dependencies. The
config surface includes a serializable dataset registry with semver-aware
version resolution, explicit policy-to-dataset compatibility checks, and
version metadata on all templates. The evidence surface supports queryable
lookup by dataset, date range, and run ID. The orchestration surface provides
dataset-aware execution alongside the original deterministic demo helpers.
