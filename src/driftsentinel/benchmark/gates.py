"""10-gate evaluator for the dual-track benchmark.

Ported from Chapter 3 (measurable-control-effectiveness) as first-party DriftSentinel code.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class GateVerdict(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


@dataclass(frozen=True)
class GateConfig:
    """A single gate definition."""

    name: str
    gate_type: str
    operator: str
    threshold: float
    track: str
    description: str


@dataclass(frozen=True)
class GateResult:
    """Result of evaluating a single gate."""

    config: GateConfig
    measured_value: float
    verdict: GateVerdict


def evaluate_gates_from_dicts(
    gate_dicts: list[dict[str, Any]],
    measured: dict[str, float],
) -> tuple[list[GateResult], GateVerdict]:
    """Load gate configs from dicts and evaluate. For config-file-free usage."""
    configs = [
        GateConfig(
            name=g["name"],
            gate_type=g["type"],
            operator=g["operator"],
            threshold=g["threshold"],
            track=g.get("track", ""),
            description=g.get("description", ""),
        )
        for g in gate_dicts
    ]
    return evaluate_gates(configs, measured)


def _evaluate_single(config: GateConfig, value: float) -> GateVerdict:
    if config.operator == ">=":
        passed = value >= config.threshold
    elif config.operator == "<=":
        passed = value <= config.threshold
    else:
        passed = False

    if passed:
        return GateVerdict.PASS
    return GateVerdict.FAIL if config.gate_type == "FAIL" else GateVerdict.WARN


def evaluate_gates(
    configs: list[GateConfig],
    measured: dict[str, float],
) -> tuple[list[GateResult], GateVerdict]:
    """Evaluate all gates. Returns per-gate results and overall verdict."""
    results: list[GateResult] = []
    overall = GateVerdict.PASS

    for config in configs:
        value = measured.get(config.name, 0.0)
        verdict = _evaluate_single(config, value)
        results.append(GateResult(
            config=config, measured_value=value, verdict=verdict,
        ))
        if verdict == GateVerdict.FAIL:
            overall = GateVerdict.FAIL
        elif verdict == GateVerdict.WARN and overall != GateVerdict.FAIL:
            overall = GateVerdict.WARN

    return results, overall
