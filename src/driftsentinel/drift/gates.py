"""Gate evaluator -- configurable release control with pass/warn/fail verdicts.

Ported from Chapter 2 (silent-failure-prevention) as first-party DriftSentinel code.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class GateVerdict(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


@dataclass(frozen=True)
class GateConfig:
    """A single gate definition."""

    name: str
    gate_type: str  # "FAIL" or "WARN"
    operator: str   # ">=" or "<="
    threshold: float
    description: str


@dataclass(frozen=True)
class GateResult:
    """Result of evaluating a single gate."""

    config: GateConfig
    measured_value: float
    verdict: GateVerdict


def _evaluate_single(config: GateConfig, value: float) -> GateVerdict:
    """Evaluate a single gate against a measured value."""
    if config.operator == ">=":
        passed = value >= config.threshold
    elif config.operator == "<=":
        passed = value <= config.threshold
    else:
        passed = False

    if passed:
        return GateVerdict.PASS
    if config.gate_type == "FAIL":
        return GateVerdict.FAIL
    return GateVerdict.WARN


def evaluate_gates(
    configs: list[GateConfig],
    measured: dict[str, float],
) -> tuple[list[GateResult], GateVerdict]:
    """Evaluate all gates against measured values.

    Returns:
        results: List of per-gate results.
        overall: Overall verdict (worst of all individual verdicts).
    """
    results: list[GateResult] = []
    overall = GateVerdict.PASS

    for config in configs:
        value = measured.get(config.name, 0.0)
        verdict = _evaluate_single(config, value)
        results.append(GateResult(config=config, measured_value=value, verdict=verdict))

        if verdict == GateVerdict.FAIL:
            overall = GateVerdict.FAIL
        elif verdict == GateVerdict.WARN and overall != GateVerdict.FAIL:
            overall = GateVerdict.WARN

    return results, overall
