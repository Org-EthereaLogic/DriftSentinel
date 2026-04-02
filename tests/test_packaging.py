"""Tests for Phase 2 Databricks MVP packaging.

Verifies that notebooks are operational, resource files contain deployable
definitions, and the benchmark policy normalizes into gate dicts.
"""

from __future__ import annotations

import subprocess
import zipfile
from pathlib import Path

import yaml

from driftsentinel.config.loader import load_benchmark_policy, normalize_benchmark_gates

ROOT = Path(__file__).resolve().parent.parent
NOTEBOOKS = ROOT / "notebooks"
RESOURCES = ROOT / "resources"
TEMPLATES = ROOT / "templates"
BUNDLE_CONFIG = ROOT / "databricks.yml"
MAKEFILE = ROOT / "Makefile"
COMMANDS_DIR = ROOT / ".claude" / "commands"

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
    "driftsentinel_app.yml",
]

COMMAND_DOC_FILES = [
    "start.md",
    "test.md",
    "sync.md",
    "feature.md",
    "pull-request.md",
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


def test_all_notebooks_support_bundle_local_bootstrap() -> None:
    """Bundle-deployed notebooks should install the uploaded bundle before GitHub."""
    for name in NOTEBOOK_FILES:
        text = (NOTEBOOKS / name).read_text(encoding="utf-8")
        assert "driftsentinel-bootstrap.txt" in text, f"{name} missing bootstrap requirements file"
        assert 'Path("/Workspace")' in text, f"{name} missing workspace bundle bootstrap logic"


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
    assert params["evidence_dir"] == "/tmp/driftsentinel_evidence"


def test_bundle_requires_explicit_catalog_var() -> None:
    with open(BUNDLE_CONFIG, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    catalog = data["variables"]["catalog"]
    assert "default" not in catalog
    assert data["variables"]["schema"]["default"] == "default"


def test_makefile_exposes_catalog_check_and_profile_override() -> None:
    text = MAKEFILE.read_text(encoding="utf-8")
    assert "bundle-catalog-check:" in text
    assert 'catalogs get "$${CATALOG:?Set CATALOG}" $(PROFILE_ARG) -o json' in text
    expected_validate = (
        'bundle validate $(PROFILE_ARG) --target dev '
        '--var="catalog=$${BUNDLE_VAR_catalog:-$${CATALOG:?Set CATALOG or '
        'BUNDLE_VAR_catalog}}"'
    )
    assert (
        expected_validate in text
    )
    expected_app_deploy = (
        '$(UV) run python scripts/deploy_databricks_app.py '
        '$(if $(PROFILE),--profile $(PROFILE),) --target dev '
        '--catalog "$${BUNDLE_VAR_catalog:-$${CATALOG:?Set CATALOG or '
        'BUNDLE_VAR_catalog}}"'
    )
    assert expected_app_deploy in text


def test_root_requirements_install_local_package_for_app_deploy() -> None:
    text = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert "-e ." in text
    assert "gradio" in text


def test_command_docs_do_not_use_bare_bundle_validate() -> None:
    for name in COMMAND_DOC_FILES:
        text = (COMMANDS_DIR / name).read_text(encoding="utf-8")
        assert "databricks bundle validate" not in text, (
            f"{name} should route bundle validation through the safe make target"
        )
        assert "make bundle-validate" in text, (
            f"{name} should document the safe make bundle-validate command"
        )


def test_start_test_and_sync_docs_require_catalog_check() -> None:
    for name in ["start.md", "test.md", "sync.md"]:
        text = (COMMANDS_DIR / name).read_text(encoding="utf-8")
        assert "make bundle-catalog-check" in text, (
            f"{name} should require an explicit catalog existence check"
        )


def test_bundle_docs_distinguish_catalog_check_validate_and_deploy() -> None:
    doc_paths = [
        ROOT / "README.md",
        ROOT / "docs" / "deployment_guide.md",
        ROOT / "specs" / "DS-BI-001_Build_Instructions.md",
    ]
    for path in doc_paths:
        text = path.read_text(encoding="utf-8")
        assert "make bundle-catalog-check" in text
        assert "databricks catalogs get" in text
        assert "does not" in text and "prove" in text, (
            f"{path.name} should distinguish validate from deploy proof"
        )


def test_app_deploy_docs_distinguish_resource_creation_from_app_runtime_deploy() -> None:
    doc_paths = [
        ROOT / "README.md",
        ROOT / "docs" / "deployment_guide.md",
        ROOT / "docs" / "operations_guide.md",
    ]
    for path in doc_paths:
        text = path.read_text(encoding="utf-8")
        assert "app-deploy" in text or "databricks apps deploy" in text, (
            f"{path.name} should document the app deployment step"
        )
        assert "bundle deploy" in text, f"{path.name} should still reference bundle deploy"
        assert "databricks apps get" in text, (
            f"{path.name} should document the app status proof surface"
        )

    spec_text = (ROOT / "specs" / "DS-IP-001-P4_Phase_4_App_UI_Plan.md").read_text(
        encoding="utf-8"
    )
    assert "make app-deploy" in spec_text
    assert "bundle deploy" in spec_text


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


def test_notebooks_expose_template_override_and_evidence_widgets() -> None:
    register_text = (NOTEBOOKS / "01_register_dataset.py").read_text(encoding="utf-8")
    benchmark_text = (NOTEBOOKS / "05_run_control_benchmark.py").read_text(encoding="utf-8")
    assert 'dbutils.widgets.text("contract_path", "",' in register_text
    assert 'dbutils.widgets.text("policy_path", "",' in benchmark_text
    assert 'dbutils.widgets.text("evidence_dir", "/tmp/driftsentinel_evidence",' in benchmark_text


# --- Phase 3: Dataset selection and evidence query widgets ---


def test_register_notebook_has_registry_widget() -> None:
    text = (NOTEBOOKS / "01_register_dataset.py").read_text(encoding="utf-8")
    assert 'dbutils.widgets.text("registry_path"' in text
    assert "DatasetRegistry" in text


def test_run_notebooks_have_dataset_id_widget() -> None:
    for name in ["03_run_intake_controls.py", "04_run_drift_gate.py", "05_run_control_benchmark.py"]:
        text = (NOTEBOOKS / name).read_text(encoding="utf-8")
        assert 'dbutils.widgets.text("dataset_id"' in text, (
            f"{name} missing dataset_id widget"
        )


def test_review_notebook_has_filter_widgets() -> None:
    text = (NOTEBOOKS / "06_review_evidence.py").read_text(encoding="utf-8")
    for widget in ["dataset_id", "run_kind", "run_id", "date_from", "date_to"]:
        assert f'dbutils.widgets.text("{widget}"' in text, (
            f"06_review_evidence.py missing {widget} widget"
        )
    assert "list_evidence" in text
    assert "load_evidence" in text


def test_notebooks_delegate_to_package_code() -> None:
    """Notebooks must not re-implement registry, lookup, or orchestration logic."""
    for name in NOTEBOOK_FILES:
        text = (NOTEBOOKS / name).read_text(encoding="utf-8")
        assert "class DatasetRegistry" not in text, (
            f"{name} re-implements DatasetRegistry instead of importing"
        )
        assert "def list_evidence" not in text, (
            f"{name} re-implements list_evidence instead of importing"
        )


def test_built_wheel_includes_packaged_templates(tmp_path: Path) -> None:
    subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(tmp_path)],
        check=True,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    wheels = list(tmp_path.glob("*.whl"))
    assert len(wheels) == 1
    with zipfile.ZipFile(wheels[0]) as zf:
        names = set(zf.namelist())
    assert "driftsentinel/templates/dataset_contract.yml" in names
    assert "driftsentinel/templates/drift_policy.yml" in names
    assert "driftsentinel/templates/benchmark_policy.yml" in names
