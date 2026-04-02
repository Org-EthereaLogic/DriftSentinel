"""Intake certification: schema drift detection, duplicate replay blocking,
contract validation, and quarantine routing (derived from Chapter 1)."""

from driftsentinel.intake.contracts import (
    ContractViolation,
    evaluate_batch,
    evaluate_row,
)

__all__ = [
    "ContractViolation",
    "evaluate_batch",
    "evaluate_row",
]
