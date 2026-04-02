"""Tests for Phase 2 Databricks MVP packaging.

Verifies that notebooks are operational, resource files contain deployable
definitions, and the benchmark policy normalizes into gate dicts.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from driftsentinel.config.loader import load_benchmark_policy, normalize_benchmark_gates

ROOT = Path(__file__).resolve().parent.parent
NOTEBOOKS = ROOT / "notebooks"
RESOURCES = ROOT / "resources"
TEMPLATES = ROOT / "templates"

NOTEBOOK_FILES = [
    "00_quickstart_setup.py",
    "01_register_dataset.py",
    "02_seed_or_import_baseline.py",
    "03_run_intake_controls.py",
    "04_run_drift_gate.py",
    "05_run_control_benchmark.py",
    "06_review_evidence.py",
]

RESOURCE_FILES = [
    "intake_pipeline.yml",
    "drift_gate_job.yml",
    "benchmark_job.yml",
]


# --- Notebook activation ---


def test_no_notebook_contains_phase_two_runtime_error() -> None:
    """No notebook should still raise the DS-IP-001 Phase 2 scaffold error."""
    violations: list[str] = []
    for name in NOTEBOOK_FILES:
        text = (NOTEBOOKS / name).read_text(encoding="utf-8")
        if "DS-IP-001 Phase 2" in text:
            violations.append(name)
    assert not violations, (
        f"Notebooks still contain DS-IP-001 Phase 2 RuntimeError: {violations}"
    )


def test_all_notebooks_have_databricks_header() -> None:
    """Every notebook must start with the Databricks notebook source header."""
    for name in NOTEBOOK_FILES:
        text = (NOTEBOOKS / name).read_text(encoding="utf-8")
        assert text.startswith("# Databricks notebook source"), (
            f"{name} missing '# Databricks notebook source' header"
        )


def test_all_notebooks_have_pip_install() -> None:
    """Every notebook should include a pip install cell."""
    for name in NOTEBOOK_FILES:
        text = (NOTEBOOKS / name).read_text(encoding="utf-8")
        assert "%pip install" in text, f"{name} missing %pip install cell"


def test_all_notebooks_have_command_separators() -> None:
    """Every notebook should use COMMAND separators between cells."""
    for name in NOTEBOOK_FILES:
        text = (NOTEBOOKS / name).read_text(encoding="utf-8")
        assert "# COMMAND ----------" in text, (
            f"{name} missing COMMAND separator"
        )


# --- Resource files ---


def test_all_resources_contain_resources_key() -> None:
    """All resource files must parse as YAML with a top-level 'resources' key."""
    for name in RESOURCE_FILES:
        path = RESOURCES / name
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert isinstance(data, dict), f"{name} did not parse as a YAML mapping"
        assert "resources" in data, f"{name} missing top-level 'resources' key"


def test_intake_pipeline_resource_structure() -> None:
    with open(RESOURCES / "intake_pipeline.yml", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    pipelines = data["resources"]["pipelines"]
    assert "intake_pipeline" in pipelines
    pipeline = pipelines["intake_pipeline"]
    assert pipeline["name"] == "driftsentinel_intake"
    assert len(pipeline["libraries"]) > 0


def test_drift_gate_job_resource_structure() -> None:
    with open(RESOURCES / "drift_gate_job.yml", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    jobs = data["resources"]["jobs"]
    assert "drift_gate_job" in jobs
    job = jobs["drift_gate_job"]
    assert job["name"] == "driftsentinel_drift_gate"
    assert len(job["tasks"]) > 0


def test_benchmark_job_resource_structure() -> None:
    with open(RESOURCES / "benchmark_job.yml", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    jobs = data["resources"]["jobs"]
    assert "benchmark_job" in jobs
    job = jobs["benchmark_job"]
    assert job["name"] == "driftsentinel_benchmark"
    assert len(job["tasks"]) > 0
    params = job["tasks"][0]["notebook_task"]["base_parameters"]
    assert "seed" in params
    assert "n_rows" in params


# --- Benchmark policy normalization ---


def test_benchmark_policy_loads_and_normalizes() -> None:
    """The benchmark policy template must load and normalize into gate dicts."""
    policy = load_benchmark_policy(TEMPLATES / "benchmark_policy.yml")
    gates = normalize_benchmark_gates(policy)
    assert len(gates) > 0
    for gate in gates:
        assert set(gate.keys()) == {
            "name", "type", "operator", "threshold", "track", "description",
        }
        assert gate["type"] in ("FAIL", "WARN")
        assert gate["operator"] in (">=", "<=")
        assert isinstance(gate["threshold"], float)
