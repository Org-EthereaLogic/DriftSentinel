"""Orchestration for DriftSentinel control pipeline execution."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from driftsentinel.benchmark.orchestrator import run_benchmark
from driftsentinel.config.loader import (
    DatasetRegistry,
    check_policy_compatibility,
    normalize_benchmark_gates,
)
from driftsentinel.drift.baseline import BaselineSnapshot
from driftsentinel.drift.detection import detect_drift
from driftsentinel.drift.gates import GateConfig, evaluate_gates
from driftsentinel.drift.sample_data import MONITORED_COLUMNS, generate_baseline, generate_drifted
from driftsentinel.evidence.writer import build_provenance_envelope, generate_run_id, write_evidence
from driftsentinel.intake.contracts import evaluate_batch, evaluate_dataframe_contract
from driftsentinel.intake.sample_data import ALL_BATCHES
from driftsentinel.orchestration.dataset_runtime import (
    LoadedDataset,
    load_baseline_dataset,
    load_current_dataset,
)


def run_intake_demo() -> dict[str, Any]:
    """Run the intake domain using local sample data."""
    all_ready: list[dict[str, Any]] = []
    all_quarantined: list[dict[str, Any]] = []
    total_violations = 0

    for generator in ALL_BATCHES.values():
        rows = generator()
        ready, quarantined, violations = evaluate_batch(rows)
        all_ready.extend(ready)
        all_quarantined.extend(quarantined)
        total_violations += len(violations)

    return {
        "total_rows": len(all_ready) + len(all_quarantined),
        "ready": len(all_ready),
        "quarantined": len(all_quarantined),
        "violations": total_violations,
    }


def run_drift_demo(
    *,
    run_ts: str | None = None,
) -> dict[str, Any]:
    """Run the drift domain using local sample data."""
    baseline_rows = generate_baseline()
    drifted_rows = generate_drifted()

    baseline_df = pd.DataFrame(baseline_rows)
    drifted_df = pd.DataFrame(drifted_rows)

    baseline = BaselineSnapshot.from_dataframe(baseline_df, MONITORED_COLUMNS)
    drift_result = detect_drift(baseline, drifted_df)

    configs = [
        GateConfig(
            name="stability_health_score",
            gate_type="FAIL",
            operator=">=",
            threshold=0.70,
            description="Health score",
        ),
        GateConfig(
            name="columns_drifted_ratio",
            gate_type="WARN",
            operator="<=",
            threshold=0.50,
            description="Drift ratio",
        ),
    ]
    measured = {
        "stability_health_score": drift_result.health_score,
        "columns_drifted_ratio": drift_result.columns_drifted_ratio,
    }
    gate_results, overall = evaluate_gates(configs, measured)

    gate_dicts = [
        {
            "name": result.config.name,
            "threshold": result.config.threshold,
            "measured": result.measured_value,
            "verdict": result.verdict.value,
        }
        for result in gate_results
    ]
    col_dicts = [
        {
            "column": result.column,
            "baseline_score": result.baseline_score,
            "current_score": result.current_score,
            "classification": result.classification.value,
        }
        for result in drift_result.column_results
    ]

    provenance = build_provenance_envelope(
        health_score=drift_result.health_score,
        overall_verdict=overall.value,
        columns_checked=drift_result.columns_checked,
        columns_drifted=drift_result.columns_drifted,
        row_count_baseline=drift_result.row_count_baseline,
        row_count_current=drift_result.row_count_current,
        schema_match=drift_result.schema_match,
        gate_results=gate_dicts,
        column_details=col_dicts,
        run_ts=run_ts,
    )

    return {
        "health_score": drift_result.health_score,
        "columns_drifted": drift_result.columns_drifted,
        "overall_verdict": overall.value,
        "provenance": provenance,
    }


def run_local_pipeline(
    evidence_dir: str | Path | None = None,
    *,
    run_ts: str | None = None,
) -> dict[str, Any]:
    """Run all three demo domains in sequence and optionally write evidence."""
    intake_result = run_intake_demo()
    drift_result = run_drift_demo(run_ts=run_ts)
    benchmark_result = run_benchmark(seed=42, n_rows=200, evidence_dir=evidence_dir, run_ts=run_ts)

    combined = {
        "execution_mode": "demo",
        "intake": intake_result,
        "drift": drift_result,
        "benchmark": {
            "execution_mode": benchmark_result["execution_mode"],
            "overall_verdict": benchmark_result["overall_verdict"].value,
            "measured": benchmark_result["measured"],
            "evidence_path": str(benchmark_result["evidence_path"]) if benchmark_result["evidence_path"] else None,
        },
    }

    if evidence_dir:
        write_evidence(
            evidence_dir,
            "pipeline_summary.json",
            combined,
            run_ts=run_ts,
            execution_mode="demo",
        )

    return combined


def _stage_evidence_payload_path(path: Path | None) -> str | None:
    return str(path) if path is not None else None


def _loaded_trace(loaded: LoadedDataset) -> dict[str, Any]:
    return {
        "path": loaded.source_path,
        "format": loaded.source_format,
        "files_loaded_count": len(loaded.files_loaded),
        "files_loaded_sample": list(loaded.files_loaded[:20]),
    }


def _monitored_columns(drift_policy: dict[str, Any]) -> list[str]:
    section = drift_policy["drift_policy"]
    monitored = [
        str(item["column_name"])
        for item in section.get("monitored_columns", [])
        if item.get("column_name")
    ]
    if not monitored:
        raise ValueError("Drift policy must define at least one monitored column.")
    return monitored


def _drift_gate_type(drift_policy: dict[str, Any]) -> str:
    behavior = str(drift_policy["drift_policy"].get("verdict_on_fail", "block")).strip().lower()
    return "FAIL" if behavior == "block" else "WARN"


def _drift_gate_configs(drift_policy: dict[str, Any]) -> list[GateConfig]:
    gates = drift_policy["drift_policy"].get("gates", {})
    if not isinstance(gates, dict):
        raise ValueError("Drift policy gates must be provided as a mapping.")
    gate_type = _drift_gate_type(drift_policy)
    configs: list[GateConfig] = []

    if "health_score_threshold" in gates:
        configs.append(
            GateConfig(
                name="stability_health_score",
                gate_type=gate_type,
                operator=">=",
                threshold=float(gates["health_score_threshold"]),
                description="Minimum drift health score",
            )
        )
    if "max_columns_failed" in gates:
        configs.append(
            GateConfig(
                name="columns_drifted",
                gate_type=gate_type,
                operator="<=",
                threshold=float(gates["max_columns_failed"]),
                description="Maximum monitored columns allowed to drift",
            )
        )
    return configs


def _validate_dataset_readiness(
    contract: dict[str, Any],
    frame: pd.DataFrame,
    *,
    dataset_label: str,
) -> dict[str, Any]:
    evaluation = evaluate_dataframe_contract(frame, contract)
    if not evaluation["schema_valid"] or evaluation["quarantined"] > 0:
        missing_columns = list(evaluation.get("schema_missing_columns", []))
        violation_counts = evaluation.get("violation_counts", {})
        top_violations = ", ".join(
            f"{name}={count}"
            for name, count in sorted(
                violation_counts.items(),
                key=lambda item: (-int(item[1]), item[0]),
            )[:3]
        )
        details: list[str] = [f"quarantined={evaluation['quarantined']}"]
        if missing_columns:
            details.append(f"missing_columns={missing_columns}")
        if top_violations:
            details.append(f"top_violations={top_violations}")
        raise ValueError(
            f"{dataset_label} does not satisfy the registered contract. "
            f"Fix the {dataset_label.lower()} before running drift or benchmark. "
            + "; ".join(details)
        )
    return evaluation


def _combine_stage_verdicts(*verdicts: str | None) -> str:
    normalized = [str(verdict or "").strip().upper() for verdict in verdicts if str(verdict or "").strip()]
    if "FAIL" in normalized:
        return "FAIL"
    if "WARN" in normalized:
        return "WARN"
    if "PASS" in normalized:
        return "PASS"
    return ""


def run_dataset_intake(
    contract: dict[str, Any],
    *,
    current_data: LoadedDataset | None = None,
    evidence_dir: str | Path | None = None,
    run_ts: str | None = None,
    dataset_id: str | None = None,
    contract_version: str | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Run dataset-backed intake certification against a registered contract."""
    current = current_data or load_current_dataset(contract)
    result = evaluate_dataframe_contract(current.frame, contract)
    intake_verdict = "PASS" if result["schema_valid"] and result["quarantined"] == 0 else "FAIL"
    payload = {
        **result,
        "overall_verdict": intake_verdict,
        "execution_mode": "dataset_backed",
        "source": _loaded_trace(current),
    }

    evidence_path = None
    if evidence_dir and dataset_id:
        evidence_path = write_evidence(
            evidence_dir,
            f"intake_{dataset_id}.json",
            payload,
            run_ts=run_ts,
            dataset_id=dataset_id,
            contract_version=contract_version,
            run_id=run_id,
            run_kind="intake",
            execution_mode="dataset_backed",
        )
    payload["evidence_path"] = _stage_evidence_payload_path(evidence_path)
    return payload


def run_dataset_drift(
    contract: dict[str, Any],
    drift_policy: dict[str, Any],
    *,
    current_data: LoadedDataset | None = None,
    baseline_data: LoadedDataset | None = None,
    evidence_dir: str | Path | None = None,
    run_ts: str | None = None,
    dataset_id: str | None = None,
    contract_version: str | None = None,
    policy_version: str | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Run drift detection against a trusted baseline for a registered dataset."""
    current = current_data or load_current_dataset(contract)
    baseline_loaded = baseline_data or load_baseline_dataset(contract, drift_policy)

    if current.frame.empty:
        raise ValueError("Current dataset is empty; drift execution requires at least one row.")
    if baseline_loaded.frame.empty:
        raise ValueError("Baseline dataset is empty; drift execution requires at least one row.")

    _validate_dataset_readiness(contract, current.frame, dataset_label="Current dataset")
    _validate_dataset_readiness(contract, baseline_loaded.frame, dataset_label="Trusted baseline data")

    min_rows = int(drift_policy["drift_policy"].get("baseline", {}).get("min_rows", 0) or 0)
    if min_rows and len(baseline_loaded.frame) < min_rows:
        raise ValueError(
            f"Baseline dataset has {len(baseline_loaded.frame)} rows, below required minimum {min_rows}."
        )

    monitored = _monitored_columns(drift_policy)
    baseline = BaselineSnapshot.from_dataframe(baseline_loaded.frame, monitored)
    drift_result = detect_drift(baseline, current.frame)

    measured = {
        "stability_health_score": drift_result.health_score,
        "columns_drifted": float(drift_result.columns_drifted),
    }
    gate_results, overall = evaluate_gates(_drift_gate_configs(drift_policy), measured)
    gate_dicts = [
        {
            "name": result.config.name,
            "threshold": result.config.threshold,
            "measured": result.measured_value,
            "verdict": result.verdict.value,
        }
        for result in gate_results
    ]
    col_dicts = [
        {
            "column": result.column,
            "baseline_score": result.baseline_score,
            "current_score": result.current_score,
            "classification": result.classification.value,
        }
        for result in drift_result.column_results
    ]

    provenance = build_provenance_envelope(
        health_score=drift_result.health_score,
        overall_verdict=overall.value,
        columns_checked=drift_result.columns_checked,
        columns_drifted=drift_result.columns_drifted,
        row_count_baseline=drift_result.row_count_baseline,
        row_count_current=drift_result.row_count_current,
        schema_match=drift_result.schema_match,
        gate_results=gate_dicts,
        column_details=col_dicts,
        run_ts=run_ts,
    )

    payload = {
        "execution_mode": "dataset_backed",
        "health_score": drift_result.health_score,
        "columns_drifted": drift_result.columns_drifted,
        "columns_drifted_ratio": drift_result.columns_drifted_ratio,
        "overall_verdict": overall.value,
        "schema_match": drift_result.schema_match,
        "monitored_columns": monitored,
        "current_source": _loaded_trace(current),
        "baseline_source": _loaded_trace(baseline_loaded),
        "provenance": provenance,
    }

    evidence_path = None
    if evidence_dir and dataset_id:
        evidence_path = write_evidence(
            evidence_dir,
            f"drift_{dataset_id}.json",
            provenance,
            run_ts=run_ts,
            dataset_id=dataset_id,
            contract_version=contract_version,
            policy_version=policy_version,
            run_id=run_id,
            run_kind="drift",
            execution_mode="dataset_backed",
        )
    payload["evidence_path"] = _stage_evidence_payload_path(evidence_path)
    return payload


def run_dataset_benchmark(
    contract: dict[str, Any],
    drift_policy: dict[str, Any],
    benchmark_policy: dict[str, Any] | None = None,
    *,
    baseline_data: LoadedDataset | None = None,
    evidence_dir: str | Path | None = None,
    seed: int = 42,
    n_rows: int = 200,
    run_ts: str | None = None,
    dataset_id: str | None = None,
    contract_version: str | None = None,
    policy_version: str | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Run the benchmark against a trusted real-data reference sample."""
    baseline_loaded = baseline_data or load_baseline_dataset(contract, drift_policy)
    _validate_dataset_readiness(contract, baseline_loaded.frame, dataset_label="Trusted baseline data")

    bench_section = benchmark_policy["benchmark_policy"] if benchmark_policy is not None else {}
    benchmark_result = run_benchmark(
        seed=seed,
        n_rows=n_rows,
        evidence_dir=evidence_dir,
        gate_dicts=normalize_benchmark_gates(benchmark_policy) if benchmark_policy is not None else None,
        run_ts=run_ts,
        dataset_id=dataset_id,
        contract_version=contract_version,
        policy_version=policy_version,
        run_id=run_id,
        reference_df=baseline_loaded.frame,
        expected_columns=list(baseline_loaded.frame.columns),
        monitored_columns=_monitored_columns(drift_policy),
        business_key=list(contract["contract"].get("business_key", [])),
        quality_faults=list(bench_section.get("quality_faults", [])),
        drift_patterns=list(bench_section.get("drift_patterns", [])),
    )
    return {
        "execution_mode": benchmark_result["execution_mode"],
        "reference_row_count": benchmark_result["reference_row_count"],
        "reference_source": _loaded_trace(baseline_loaded),
        "overall_verdict": benchmark_result["overall_verdict"].value,
        "gate_results": benchmark_result["gate_results"],
        "measured": benchmark_result["measured"],
        "evidence_path": _stage_evidence_payload_path(benchmark_result["evidence_path"]),
    }


def run_dataset_pipeline(
    registry: DatasetRegistry,
    dataset_id: str,
    *,
    evidence_dir: str | Path | None = None,
    drift_policy: dict[str, Any] | None = None,
    benchmark_policy: dict[str, Any] | None = None,
    seed: int = 42,
    n_rows: int = 200,
    run_ts: str | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Execute intake, drift, and benchmark for a registered dataset."""
    contract = registry.get(dataset_id)
    ds = contract["dataset"]
    contract_version = ds.get("contract_version", "0.0.0")
    rid = run_id or generate_run_id()

    if drift_policy is None:
        raise ValueError(
            "Dataset-backed pipeline execution requires a drift policy with monitored columns "
            "and a baseline path."
        )

    drift_binding = check_policy_compatibility(
        registry, drift_policy["drift_policy"], "Drift policy"
    )
    bench_binding: dict[str, str] | None = None
    if benchmark_policy is not None:
        bench_binding = check_policy_compatibility(
            registry, benchmark_policy["benchmark_policy"], "Benchmark policy"
        )

    current_loaded = load_current_dataset(contract)
    baseline_loaded = load_baseline_dataset(contract, drift_policy)

    intake_result = run_dataset_intake(
        contract,
        current_data=current_loaded,
        evidence_dir=evidence_dir,
        run_ts=run_ts,
        dataset_id=dataset_id,
        contract_version=contract_version,
        run_id=rid,
    )
    drift_result = run_dataset_drift(
        contract,
        drift_policy,
        current_data=current_loaded,
        baseline_data=baseline_loaded,
        evidence_dir=evidence_dir,
        run_ts=run_ts,
        dataset_id=dataset_id,
        contract_version=contract_version,
        policy_version=drift_binding["policy_version"],
        run_id=rid,
    )
    benchmark_result = run_dataset_benchmark(
        contract,
        drift_policy,
        benchmark_policy,
        baseline_data=baseline_loaded,
        evidence_dir=evidence_dir,
        seed=seed,
        n_rows=n_rows,
        run_ts=run_ts,
        dataset_id=dataset_id,
        contract_version=contract_version,
        policy_version=bench_binding["policy_version"] if bench_binding else None,
        run_id=rid,
    )
    overall_verdict = _combine_stage_verdicts(
        intake_result.get("overall_verdict"),
        drift_result.get("overall_verdict"),
        benchmark_result.get("overall_verdict"),
    )

    combined: dict[str, Any] = {
        "execution_mode": "dataset_backed",
        "overall_verdict": overall_verdict,
        "dataset_id": dataset_id,
        "contract_version": contract_version,
        "run_id": rid,
        "current_source": _loaded_trace(current_loaded),
        "baseline_source": _loaded_trace(baseline_loaded),
        "intake": intake_result,
        "drift": drift_result,
        "benchmark": benchmark_result,
    }

    if drift_binding:
        combined["drift_policy_version"] = drift_binding["policy_version"]
    if bench_binding:
        combined["benchmark_policy_version"] = bench_binding["policy_version"]

    if evidence_dir:
        summary_path = write_evidence(
            evidence_dir,
            f"pipeline_{dataset_id}.json",
            combined,
            run_ts=run_ts,
            dataset_id=dataset_id,
            contract_version=contract_version,
            policy_version=drift_binding["policy_version"],
            run_id=rid,
            run_kind="pipeline",
            execution_mode="dataset_backed",
        )
        combined["evidence_path"] = str(summary_path)

    return combined
