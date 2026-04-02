"""Distribution drift detection and publication gate logic
(derived from Chapter 2)."""

from driftsentinel.drift.baseline import BaselineSnapshot
from driftsentinel.drift.detection import (
    DriftClassification,
    DriftResult,
    detect_drift,
)
from driftsentinel.drift.gates import GateVerdict, evaluate_gates

__all__ = [
    "BaselineSnapshot",
    "DriftClassification",
    "DriftResult",
    "GateVerdict",
    "detect_drift",
    "evaluate_gates",
]
