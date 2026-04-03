"""Stress and performance tests for DriftSentinel evidence pipeline.

Validates that the evidence lookup, analytics pipeline, and app query
helpers behave correctly and perform well under high artifact volumes
(1,000+ artifacts) and with adversarial inputs (malformed JSON, empty
files, deeply nested payloads, very long strings).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

import pytest

from driftsentinel.evidence.writer import (
    generate_run_id,
    invalidate_evidence_cache,
    list_evidence,
    load_evidence,
    write_evidence,
)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
from analytics import (  # type: ignore[import-not-found]  # noqa: E402
    _daily_verdict_summary,
    build_analytics_data,
    kind_pie_data,
    timeline_data,
    verdict_bar_data,
)

FIXED_TS_BASE = "2026-04-{day:02d}T{hour:02d}:00:00+00:00"
DATASETS = ["alpha", "bravo", "charlie", "delta", "echo"]
KINDS = ["intake", "drift", "benchmark", "pipeline"]
VERDICTS = ["PASS", "FAIL", "WARN"]


def _generate_bulk_artifacts(tmp_path: Path, n_days: int, per_day: int) -> int:
    """Write bulk evidence artifacts across n_days. Returns total count."""
    count = 0
    for day in range(1, n_days + 1):
        for i in range(per_day):
            hour = i % 24
            ds = DATASETS[i % len(DATASETS)]
            kind = KINDS[i % len(KINDS)]
            verdict = VERDICTS[i % len(VERDICTS)]
            ts = FIXED_TS_BASE.format(day=day, hour=hour)
            write_evidence(
                tmp_path,
                f"d{day}_{i}.json",
                {"overall_verdict": verdict, "metric": i * 0.01},
                run_ts=ts,
                dataset_id=ds,
                contract_version="1.0.0",
                run_id=generate_run_id(),
                run_kind=kind,
            )
            count += 1
    return count


class TestBulkEvidenceCorrectness:
    """Verify that all filters and sorting remain correct at scale."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path: Path) -> None:
        invalidate_evidence_cache()
        self.tmp = tmp_path
        self.total = _generate_bulk_artifacts(tmp_path, n_days=10, per_day=100)

    def test_unfiltered_returns_all(self) -> None:
        results = list_evidence(self.tmp)
        assert len(results) == self.total

    def test_sorted_descending(self) -> None:
        results = list_evidence(self.tmp)
        dates = [r["generated_at"] for r in results if not r.get("parse_error")]
        assert dates == sorted(dates, reverse=True)

    def test_dataset_filter_correct(self) -> None:
        for ds in DATASETS:
            results = list_evidence(self.tmp, dataset_id=ds)
            assert all(r["dataset_id"] == ds for r in results)
            assert len(results) > 0

    def test_kind_filter_correct(self) -> None:
        for kind in KINDS:
            results = list_evidence(self.tmp, run_kind=kind)
            assert all(r["run_kind"] == kind for r in results)
            assert len(results) > 0

    def test_date_filter_single_day(self) -> None:
        results = list_evidence(self.tmp, date_from="2026-04-05", date_to="2026-04-05")
        assert len(results) == 100
        assert all("2026-04-05" in r["generated_at"] for r in results)

    def test_combined_filters_reduce_results(self) -> None:
        full = list_evidence(self.tmp)
        filtered = list_evidence(self.tmp, dataset_id="alpha", run_kind="intake")
        assert len(filtered) < len(full)
        assert all(r["dataset_id"] == "alpha" and r["run_kind"] == "intake" for r in filtered)

    def test_verdict_extraction_correct(self) -> None:
        results = list_evidence(self.tmp)
        verdicts = {r["overall_verdict"] for r in results if not r.get("parse_error")}
        assert verdicts == set(VERDICTS)


class TestMalformedFileResilience:
    """Verify evidence pipeline handles adversarial file content."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path: Path) -> None:
        invalidate_evidence_cache()
        self.tmp = tmp_path

    def test_empty_files_counted_as_malformed(self) -> None:
        for i in range(50):
            (self.tmp / f"empty_{i}.json").write_text("")
        write_evidence(self.tmp, "good.json", {"overall_verdict": "PASS"}, run_ts="2026-04-01T00:00:00+00:00")
        results = list_evidence(self.tmp)
        malformed = [r for r in results if r.get("parse_error")]
        valid = [r for r in results if not r.get("parse_error")]
        assert len(malformed) == 50
        assert len(valid) == 1

    def test_truncated_json_counted_as_malformed(self) -> None:
        for i in range(20):
            (self.tmp / f"trunc_{i}.json").write_text('{"meta": {"generated_at": "2026-01')
        results = list_evidence(self.tmp)
        assert all(r.get("parse_error") for r in results)

    def test_deeply_nested_payload(self) -> None:
        deep: dict[str, Any] = {"level": 0}
        current: dict[str, Any] = deep
        for i in range(1, 100):
            current["child"] = {"level": i}
            current = current["child"]
        write_evidence(self.tmp, "deep.json", deep, run_ts="2026-04-01T00:00:00+00:00")
        results = list_evidence(self.tmp)
        assert len(results) == 1
        assert not results[0].get("parse_error")

    def test_large_string_payload(self) -> None:
        big_str = "x" * 1_000_000  # 1MB string
        write_evidence(
            self.tmp, "big.json", {"data": big_str},
            run_ts="2026-04-01T00:00:00+00:00",
        )
        results = list_evidence(self.tmp)
        assert len(results) == 1
        data = load_evidence(Path(results[0]["file"]))
        assert len(data["payload"]["data"]) == 1_000_000

    def test_mixed_valid_and_malformed(self) -> None:
        for i in range(30):
            if i % 3 == 0:
                (self.tmp / f"bad_{i}.json").write_text("{invalid")
            else:
                write_evidence(
                    self.tmp, f"ok_{i}.json", {"v": i},
                    run_ts=f"2026-04-01T{i % 24:02d}:00:00+00:00",
                    dataset_id="test", run_kind="intake",
                )
        results = list_evidence(self.tmp)
        malformed = [r for r in results if r.get("parse_error")]
        valid = [r for r in results if not r.get("parse_error")]
        assert len(malformed) == 10
        assert len(valid) == 20

    def test_filtered_query_skips_malformed(self) -> None:
        for i in range(10):
            (self.tmp / f"bad_{i}.json").write_text("")
        write_evidence(
            self.tmp, "good.json", {"overall_verdict": "PASS"},
            run_ts="2026-04-01T00:00:00+00:00",
            dataset_id="target", run_kind="drift",
        )
        results = list_evidence(self.tmp, dataset_id="target")
        assert len(results) == 1
        assert results[0]["dataset_id"] == "target"


class TestCacheCorrectness:
    """Verify the metadata cache behaves correctly across operations."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path: Path) -> None:
        invalidate_evidence_cache()
        self.tmp = tmp_path

    def test_cache_returns_same_results(self) -> None:
        _generate_bulk_artifacts(self.tmp, n_days=3, per_day=50)
        r1 = list_evidence(self.tmp)
        r2 = list_evidence(self.tmp)
        assert len(r1) == len(r2)
        assert [r["file"] for r in r1] == [r["file"] for r in r2]

    def test_cache_picks_up_new_files(self) -> None:
        _generate_bulk_artifacts(self.tmp, n_days=2, per_day=30)
        r1 = list_evidence(self.tmp)
        assert len(r1) == 60
        # Add more files
        write_evidence(
            self.tmp, "extra.json", {"overall_verdict": "PASS"},
            run_ts="2026-04-10T00:00:00+00:00",
            dataset_id="new_ds", run_kind="intake",
        )
        r2 = list_evidence(self.tmp)
        assert len(r2) == 61
        assert any(r["dataset_id"] == "new_ds" for r in r2)

    def test_invalidate_cache_full(self) -> None:
        _generate_bulk_artifacts(self.tmp, n_days=2, per_day=20)
        list_evidence(self.tmp)  # populate cache
        invalidate_evidence_cache()
        # Should still work after cache clear
        r = list_evidence(self.tmp)
        assert len(r) == 40

    def test_invalidate_cache_by_directory(self) -> None:
        dir_a = self.tmp / "a"
        dir_b = self.tmp / "b"
        dir_a.mkdir()
        dir_b.mkdir()
        write_evidence(dir_a, "a.json", {"v": 1}, run_ts="2026-04-01T00:00:00+00:00")
        write_evidence(dir_b, "b.json", {"v": 2}, run_ts="2026-04-01T00:00:00+00:00")
        list_evidence(dir_a)
        list_evidence(dir_b)
        invalidate_evidence_cache(dir_a)
        # dir_b should still be cached (returns same results)
        r_b = list_evidence(dir_b)
        assert len(r_b) == 1


class TestAnalyticsPipelineAtScale:
    """Verify analytics aggregation correctness at scale."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path: Path) -> None:
        invalidate_evidence_cache()
        self.tmp = tmp_path
        self.total = _generate_bulk_artifacts(tmp_path, n_days=10, per_day=100)

    def test_analytics_records_match_evidence_count(self) -> None:
        records = build_analytics_data(str(self.tmp))
        assert len(records) == self.total

    def test_verdict_bar_totals_match(self) -> None:
        records = build_analytics_data(str(self.tmp))
        vbar = verdict_bar_data(records)
        total_from_bar = sum(row[1] for row in vbar)
        assert total_from_bar == self.total

    def test_kind_pie_totals_match(self) -> None:
        records = build_analytics_data(str(self.tmp))
        kpie = kind_pie_data(records)
        total_from_pie = sum(row[1] for row in kpie)
        assert total_from_pie == self.total

    def test_timeline_preserves_all_records(self) -> None:
        records = build_analytics_data(str(self.tmp))
        tline = timeline_data(records)
        assert len(tline) == self.total

    def test_daily_summary_covers_all_days(self) -> None:
        records = build_analytics_data(str(self.tmp))
        tline = timeline_data(records)
        dates, daily_counts, daily_pass, daily_total = _daily_verdict_summary(tline)
        assert len(dates) == 10
        total_from_daily = sum(daily_total[d] for d in dates)
        assert total_from_daily == self.total

    def test_daily_pass_rate_within_bounds(self) -> None:
        records = build_analytics_data(str(self.tmp))
        tline = timeline_data(records)
        _, _, daily_pass, daily_total = _daily_verdict_summary(tline)
        for d in daily_total:
            rate = daily_pass[d] / daily_total[d] * 100
            assert 0 <= rate <= 100


class TestPerformanceBounds:
    """Verify that operations complete within reasonable time bounds.

    These are not strict benchmarks but sanity checks that the cache
    and optimizations keep operations well under interactive thresholds.
    """

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path: Path) -> None:
        invalidate_evidence_cache()
        self.tmp = tmp_path
        _generate_bulk_artifacts(tmp_path, n_days=5, per_day=200)

    def test_warm_cache_query_under_500ms(self) -> None:
        list_evidence(self.tmp)  # cold
        t0 = time.perf_counter()
        list_evidence(self.tmp)  # warm
        elapsed = time.perf_counter() - t0
        assert elapsed < 0.5, f"Warm cache query took {elapsed:.3f}s"

    def test_filtered_query_under_500ms(self) -> None:
        list_evidence(self.tmp)  # warm cache
        t0 = time.perf_counter()
        list_evidence(self.tmp, dataset_id="alpha", run_kind="intake")
        elapsed = time.perf_counter() - t0
        assert elapsed < 0.5, f"Filtered query took {elapsed:.3f}s"

    def test_analytics_pipeline_under_1s(self) -> None:
        list_evidence(self.tmp)  # warm cache
        t0 = time.perf_counter()
        records = build_analytics_data(str(self.tmp))
        verdict_bar_data(records)
        kind_pie_data(records)
        tline = timeline_data(records)
        _daily_verdict_summary(tline)
        elapsed = time.perf_counter() - t0
        assert elapsed < 1.0, f"Analytics pipeline took {elapsed:.3f}s"
