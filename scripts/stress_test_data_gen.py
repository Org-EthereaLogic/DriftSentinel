#!/usr/bin/env python3
"""Simulation script for stress testing DriftSentinel UI.

Generates thousands of synthetic evidence artifacts stretching over
a configurable multi-day period. Useful for evaluating Analytics dashboard
rendering performance, edge case handling, and table performance.
"""

from __future__ import annotations

import argparse
import logging
import os
import random
import shutil
from datetime import datetime, timedelta, timezone

from driftsentinel.evidence.writer import generate_run_id, write_evidence

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Constants
DEFAULT_OUTPUT_DIR = "/tmp/driftsentinel_evidence"
DATASETS = [
    "meridian_project_costs",
    "revenue_recognition",
    "customer_churn_model",
    "supply_chain_optimization",
    "anomaly_detection_network",
]
RUN_KINDS = ["intake", "drift", "benchmark", "pipeline"]
VERDICTS = ["PASS", "FAIL", "WARN", "UNKNOWN"]
VERDICT_WEIGHTS = [0.70, 0.15, 0.10, 0.05]  # ~70% pass, 15% fail, 10% warn, 5% unknown


def _generate_synthetic_payload(kind: str, verdict: str) -> dict:
    """Generate a dummy payload matching the generic structure of evidence output."""
    base = {
        "overall_verdict": verdict,
        "dummy_metric_1": random.uniform(0.1, 0.99),
        "dummy_metric_2": random.randint(100, 10000),
    }

    if kind == "drift":
        return {
            "drift": base,
            "columns_checked": random.randint(10, 50),
            "columns_drifted": random.randint(0, 5),
        }
    elif kind == "benchmark":
        return {
            "benchmark": base,
            "gates_evaluated": random.randint(1, 10),
            "n_rows": random.randint(1000, 50000),
        }
    return base


def run_simulation(
    days: int,
    records_per_day: int,
    output_dir: str,
    clear_existing: bool,
    malform_rate: float,
) -> None:
    logger.info(f"Starting stress test generation: {days} days, {records_per_day} records/day")

    out_path = os.path.abspath(output_dir)
    if clear_existing and os.path.exists(out_path):
        logger.info(f"Clearing existing directory: {out_path}")
        shutil.rmtree(out_path)

    os.makedirs(out_path, exist_ok=True)

    today = datetime.now(timezone.utc)
    total_records = days * records_per_day
    count = 0
    malformed_count = 0

    for day_offset in range(days):
        # We start looking 'days' ago up to 'today'
        current_date_base = today - timedelta(days=days - day_offset - 1)
        # Shift start to midnight for uniform distribution inside the day
        current_date_base = current_date_base.replace(hour=0, minute=0, second=0, microsecond=0)

        for i in range(records_per_day):
            # Randomize time within the day
            hours = random.randint(0, 23)
            minutes = random.randint(0, 59)
            seconds = random.randint(0, 59)
            run_ts = current_date_base + timedelta(hours=hours, minutes=minutes, seconds=seconds)

            dataset = random.choice(DATASETS)
            kind = random.choice(RUN_KINDS)
            verdict = random.choices(VERDICTS, weights=VERDICT_WEIGHTS, k=1)[0]
            run_id = generate_run_id()

            filename = f"{kind}_{dataset}_{run_id[:8]}.json"

            # Occasionally write an intentionally malformed JSON or empty file to test resilience
            if random.random() < malform_rate:
                malform_target = os.path.join(out_path, f"malformed_{run_id[:8]}.json")
                with open(malform_target, "w") as f:
                    if random.random() < 0.5:
                        f.write("{ \"unclosed_string\": \"bad")
                    else:
                        f.write("")
                malformed_count += 1
            else:
                payload = _generate_synthetic_payload(kind, verdict)
                write_evidence(
                    output_dir=out_path,
                    filename=filename,
                    payload=payload,
                    run_ts=run_ts.isoformat(),
                    dataset_id=dataset,
                    contract_version="1.0.0",
                    policy_version="v2",
                    run_id=run_id,
                    run_kind=kind,
                )
            count += 1

            if count % 500 == 0:
                logger.info(f"Generated {count} / {total_records} artifacts...")

    logger.info(
        f"Completed! Generated {count} normal artifacts and "
        f"{malformed_count} malformed artifacts in {out_path}."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic evidence for stress testing.")
    parser.add_argument("--days", type=int, default=14, help="Number of days to simulate.")
    parser.add_argument("--records-per-day", type=int, default=200, help="Number of records to generate per day.")
    parser.add_argument("--output-dir", type=str, default=DEFAULT_OUTPUT_DIR, help="Destination directory.")
    parser.add_argument("--clear", action="store_true", help="Clear existing artifacts first.")
    parser.add_argument(
        "--malform-rate", type=float, default=0.01,
        help="Chance (0.0 to 1.0) to generate invalid JSON to test error handling."
    )
    args = parser.parse_args()

    run_simulation(
        days=args.days,
        records_per_day=args.records_per_day,
        output_dir=args.output_dir,
        clear_existing=args.clear,
        malform_rate=args.malform_rate,
    )
