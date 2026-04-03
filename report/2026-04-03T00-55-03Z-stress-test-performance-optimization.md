# Stress Test & Performance Optimization Evidence

**Generated:** 2026-04-03T00:55:03Z
**Scope:** Evidence pipeline performance under 15,000+ artifact load
**Verdict:** PASS — all optimizations verified correct, 296 tests pass

## Stress Dataset

- **Days simulated:** 30
- **Records per day:** 500
- **Total artifacts:** 15,000 (+ 313 malformed @ 2% rate)
- **Datasets:** 5 (meridian_project_costs, revenue_recognition, customer_churn_model, supply_chain_optimization, anomaly_detection_network)
- **Run kinds:** intake, drift, benchmark, pipeline
- **Verdict distribution:** ~70% PASS, 15% FAIL, 10% WARN, 5% UNKNOWN

## Performance Benchmarks (15,000 artifacts)

| Operation | Before | After | Speedup |
|---|---|---|---|
| `list_evidence` (cold, first call) | 0.701s | 0.423s | 1.7x |
| `list_evidence` (warm, repeat) | 0.349s | 0.053s | **6.6x** |
| `list_evidence` (warm + dataset filter) | 0.577s | 0.062s | **9.3x** |
| `list_evidence` (warm + date filter) | 0.608s | 0.052s | **11.7x** |
| `list_evidence` (warm + combined filters) | 0.579s | 0.052s | **11.1x** |
| Full analytics pipeline (warm) | 0.701s | 0.084s | **8.3x** |
| 10x repeated full scans (avg) | 0.349s | 0.059s | **5.9x** |

### Memory Profile

| Operation | Before Peak | After Peak |
|---|---|---|
| `list_evidence` (no filter) | 19.2MB | 13.8MB (warm) |
| `list_evidence` (combined filter) | 9.9MB | 0.1MB (warm) |
| Analytics pipeline | 19.1MB | 13.8MB (warm) |

## Bottlenecks Identified & Fixed

### 1. Evidence Lookup — Full Directory Scan on Every Query

**Root cause:** `list_evidence()` opened and JSON-parsed every `.json` file in
the evidence directory on every call, regardless of filters. At 15K files, this
was 0.5-0.7s per query.

**Fix:** Added an in-memory metadata cache (`_metadata_cache`) to
`src/driftsentinel/evidence/writer.py`. Evidence is append-only, so cached
metadata never becomes stale. Only new files (not yet in cache) are parsed on
each call. Thread-safe via `threading.Lock()`.

**Files changed:** `src/driftsentinel/evidence/writer.py`

### 2. Analytics Pipeline — Redundant Daily Summary Computation

**Root cause:** `_daily_verdict_summary()` was called separately by both
`build_plotly_daily_volume()` and `build_plotly_health_trend()` with identical
input data, doubling the aggregation work.

**Fix:** Added optional `daily_summary` keyword argument to both chart builders.
The app's `_refresh_analytics()` now computes the summary once and passes it to
both builders.

**Files changed:** `app/analytics.py`, `app/app.py`

### 3. Analytics — Deferred Imports Inside Hot Path

**Root cause:** `_daily_verdict_summary()` imported `collections.defaultdict`
and `datetime.datetime` inside the function body, incurring import overhead on
every call.

**Fix:** Moved imports to module level.

**Files changed:** `app/analytics.py`

## New Test Coverage

Added `tests/test_stress.py` with 26 tests across 6 test classes:

| Class | Tests | Focus |
|---|---|---|
| `TestBulkEvidenceCorrectness` | 7 | Filter accuracy at 1,000 artifacts |
| `TestMalformedFileResilience` | 6 | Empty files, truncated JSON, 1MB payloads, deeply nested data |
| `TestCacheCorrectness` | 4 | Cache consistency, incremental pickup, invalidation |
| `TestAnalyticsPipelineAtScale` | 6 | Aggregation totals match evidence count |
| `TestPerformanceBounds` | 3 | Warm cache < 500ms, analytics < 1s |

## Verification

```
make lint      -> All checks passed
make typecheck -> Success: no issues found in 39 source files
make test      -> 296 passed in 3.83s
```

## Public API Changes

- **Added:** `invalidate_evidence_cache(evidence_dir=None)` to `writer.py`
  - Clears the in-memory metadata cache (all or per-directory)
  - Used by tests for isolation; available for app cache management
- **Added:** `_parse_evidence_file(p)` internal helper in `writer.py`
- **Added:** `daily_summary` keyword arg to `build_plotly_daily_volume()` and
  `build_plotly_health_trend()` in `analytics.py` (backward compatible)
