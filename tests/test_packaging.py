"""Tests for Phase 2 Databricks MVP packaging.

Verifies that notebooks are operational, resource files contain deployable
definitions, and the benchmark policy normalizes into gate dicts.
"""

from __future__ import annotations

import re
import subprocess
import tomllib
import zipfile
from pathlib import Path
from typing import Any

import yaml

from driftsentinel.config.loader import load_benchmark_policy, normalize_benchmark_gates

ROOT = Path(__file__).resolve().parent.parent
NOTEBOOKS = ROOT / "notebooks"
RESOURCES = ROOT / "resources"
TEMPLATES = ROOT / "templates"
BUNDLE_CONFIG = ROOT / "databricks.yml"
MAKEFILE = ROOT / "Makefile"
COMMANDS_DIR = ROOT / ".claude" / "commands"
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
PUBLISH_WORKFLOW = ROOT / ".github" / "workflows" / "publish.yml"
WORKFLOWS_DIR = ROOT / ".github" / "workflows"
CODACY_CONFIG = ROOT / ".codacy.yml"
WORKFLOW_USES_PATTERN = re.compile(
    r"^\s*-\s+uses:\s+(?P<action>\S+?)@(?P<ref>[^\s#]+)",
    re.MULTILINE,
)

NOTEBOOK_FILES = [
    "00_quickstart_setup.py",
    "01_register_dataset.py",
    "02_seed_or_import_baseline.py",
    "03_run_intake_controls.py",
    "04_run_drift_gate.py",
    "05_run_control_benchmark.py",
    "06_review_evidence.py",
    "07_run_dataset_pipeline.py",
]

RESOURCE_FILES = [
    "intake_pipeline.yml",
    "drift_gate_job.yml",
    "benchmark_job.yml",
    "dataset_pipeline_job.yml",
    "driftsentinel_app.yml",
    "runtime_volume.yml",
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
    assert not violations, f"Notebooks still contain DS-IP-001 Phase 2 RuntimeError: {violations}"


def test_all_notebooks_have_databricks_header() -> None:
    """Every notebook must start with the Databricks notebook source header."""
    for name in NOTEBOOK_FILES:
        text = (NOTEBOOKS / name).read_text(encoding="utf-8")
        assert text.startswith("# Databricks notebook source"), f"{name} missing '# Databricks notebook source' header"


def test_all_notebooks_have_bootstrap_install_logic() -> None:
    """Every notebook should bootstrap from the workspace tree or pip-install GitHub."""
    for name in NOTEBOOK_FILES:
        text = (NOTEBOOKS / name).read_text(encoding="utf-8")
        assert "_resolve_install_target" in text, f"{name} missing install target resolver"
        assert 'subprocess.check_call([sys.executable, "-m", "pip", "install", install_target])' in text, (
            f"{name} missing pip bootstrap fallback"
        )


def test_all_notebooks_support_bundle_local_bootstrap() -> None:
    """Bundle-deployed notebooks should prefer the workspace source tree."""
    for name in NOTEBOOK_FILES:
        text = (NOTEBOOKS / name).read_text(encoding="utf-8")
        assert 'Path("/Workspace")' in text, f"{name} missing workspace bundle bootstrap logic"
        assert 'source_root = str(Path(install_target) / "src")' in text, f"{name} missing src-layout bootstrap logic"
        assert "serverless runs do not rely on writing a temp file" in text, (
            f"{name} missing serverless bootstrap guard comment"
        )


def test_all_notebooks_have_command_separators() -> None:
    """Every notebook should use COMMAND separators between cells."""
    for name in NOTEBOOK_FILES:
        text = (NOTEBOOKS / name).read_text(encoding="utf-8")
        assert "# COMMAND ----------" in text, f"{name} missing COMMAND separator"


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
    jobs = data["resources"]["jobs"]
    assert "intake_pipeline" in jobs
    job = jobs["intake_pipeline"]
    assert job["name"] == "driftsentinel_intake"
    assert len(job["tasks"]) > 0
    params = job["tasks"][0]["notebook_task"]["base_parameters"]
    assert params["dataset_id"] == "{{job.parameters.dataset_id}}"
    assert params["registry_path"] == "{{job.parameters.registry_path}}"
    assert params["evidence_dir"] == "{{job.parameters.evidence_dir}}"
    assert params["require_dataset_backed"] == "true"
    job_params = {p["name"] for p in job["parameters"]}
    assert {"dataset_id", "registry_path", "evidence_dir"} <= job_params


def test_drift_gate_job_resource_structure() -> None:
    with open(RESOURCES / "drift_gate_job.yml", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    jobs = data["resources"]["jobs"]
    assert "drift_gate_job" in jobs
    job = jobs["drift_gate_job"]
    assert job["name"] == "driftsentinel_drift_gate"
    assert len(job["tasks"]) > 0
    params = job["tasks"][0]["notebook_task"]["base_parameters"]
    assert params["dataset_id"] == "{{job.parameters.dataset_id}}"
    assert params["drift_policy_path"] == "{{job.parameters.drift_policy_path}}"
    assert params["require_dataset_backed"] == "true"
    job_params = {p["name"] for p in job["parameters"]}
    assert {"dataset_id", "registry_path", "drift_policy_path", "evidence_dir"} <= job_params


def test_benchmark_job_resource_structure() -> None:
    with open(RESOURCES / "benchmark_job.yml", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    jobs = data["resources"]["jobs"]
    assert "benchmark_job" in jobs
    job = jobs["benchmark_job"]
    assert job["name"] == "driftsentinel_benchmark"
    assert len(job["tasks"]) > 0
    params = job["tasks"][0]["notebook_task"]["base_parameters"]
    assert params["seed"] == "{{job.parameters.seed}}"
    assert params["n_rows"] == "{{job.parameters.n_rows}}"
    assert params["dataset_id"] == "{{job.parameters.dataset_id}}"
    assert params["drift_policy_path"] == "{{job.parameters.drift_policy_path}}"
    assert params["policy_path"] == "{{job.parameters.benchmark_policy_path}}"
    assert params["evidence_dir"] == "{{job.parameters.evidence_dir}}"
    assert params["require_dataset_backed"] == "true"
    job_params = {p["name"] for p in job["parameters"]}
    expected_params = {
        "dataset_id",
        "registry_path",
        "drift_policy_path",
        "benchmark_policy_path",
        "evidence_dir",
        "seed",
        "n_rows",
    }
    assert expected_params <= job_params


def test_dataset_pipeline_job_resource_structure() -> None:
    with open(RESOURCES / "dataset_pipeline_job.yml", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    jobs = data["resources"]["jobs"]
    assert "dataset_pipeline_job" in jobs
    job = jobs["dataset_pipeline_job"]
    assert job["name"] == "driftsentinel_dataset_pipeline"
    params = job["tasks"][0]["notebook_task"]["base_parameters"]
    assert params["dataset_id"] == "{{job.parameters.dataset_id}}"
    assert params["drift_policy_path"] == "{{job.parameters.drift_policy_path}}"
    assert params["policy_path"] == "{{job.parameters.benchmark_policy_path}}"
    job_params = {p["name"] for p in job["parameters"]}
    expected_params = {
        "dataset_id",
        "registry_path",
        "drift_policy_path",
        "benchmark_policy_path",
        "evidence_dir",
        "seed",
        "n_rows",
    }
    assert expected_params <= job_params


def test_runtime_volume_resource_structure() -> None:
    with open(RESOURCES / "runtime_volume.yml", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    volumes = data["resources"]["volumes"]
    assert "runtime_volume" in volumes
    volume = volumes["runtime_volume"]
    assert volume["catalog_name"] == "${var.catalog}"
    assert volume["schema_name"] == "${var.schema}"
    assert volume["name"] == "${var.runtime_volume_name}"


def test_bundle_requires_explicit_catalog_var() -> None:
    with open(BUNDLE_CONFIG, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    variables = data["variables"]
    catalog = variables["catalog"]
    assert "default" not in catalog
    assert variables["schema"]["default"] == "default"
    assert variables["runtime_volume_name"]["default"] == "driftsentinel_runtime"
    # Runtime inputs (dataset_id, policy paths, seed, n_rows) are now job
    # parameters, not bundle variables.
    assert "dataset_id" not in variables
    assert "drift_policy_path" not in variables
    assert "benchmark_policy_path" not in variables
    assert "seed" not in variables
    assert "n_rows" not in variables


def test_bundle_sync_excludes_default_artifacts() -> None:
    """databricks.yml ships fail-closed sync.exclude defaults — see DS-PATCH-034."""
    with open(BUNDLE_CONFIG, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert isinstance(data, dict), "databricks.yml must parse to a top-level mapping"
    sync = data.get("sync")
    assert isinstance(sync, dict), "databricks.yml must define a top-level 'sync' mapping"
    excludes = sync.get("exclude")
    assert isinstance(excludes, list), "'sync.exclude' must be a list"
    required_patterns = {
        "/data/",
        "/evidence_pulled/",
        "/archive_exports/",
        "/orphaned_state_backup/",
        "/report/",
        ".venv/",
        "**/__pycache__/",
        ".pytest_cache/",
        ".mypy_cache/",
        ".ruff_cache/",
    }
    missing = required_patterns - set(excludes)
    assert not missing, f"databricks.yml sync.exclude is missing required patterns: {sorted(missing)}"


def test_makefile_exposes_catalog_check_and_profile_override() -> None:
    text = MAKEFILE.read_text(encoding="utf-8")
    assert "bundle-catalog-check:" in text
    assert 'catalogs get "$${CATALOG:?Set CATALOG}" $(PROFILE_ARG) -o json' in text
    expected_validate = (
        "bundle validate $(PROFILE_ARG) --target dev "
        '--var="catalog=$${BUNDLE_VAR_catalog:-$${CATALOG:?Set CATALOG or '
        'BUNDLE_VAR_catalog}}"'
    )
    assert expected_validate in text
    expected_app_deploy = (
        "$(UV) run python scripts/deploy_databricks_app.py "
        "$(if $(PROFILE),--profile $(PROFILE),) --target dev "
        '--catalog "$${BUNDLE_VAR_catalog:-$${CATALOG:?Set CATALOG or '
        'BUNDLE_VAR_catalog}}"'
    )
    assert expected_app_deploy in text


def test_root_requirements_install_local_package_for_app_deploy() -> None:
    text = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert "-e ." in text
    assert "gradio>=6.10.0,<7" in text
    assert "plotly>=5.0,<6" in text


def test_pyproject_app_group_includes_dashboard_runtime_deps() -> None:
    with open(ROOT / "pyproject.toml", "rb") as f:
        data = tomllib.load(f)
    app_group = data["dependency-groups"]["app"]
    assert "gradio>=6.10.0,<7" in app_group
    assert "plotly>=5.0,<6" in app_group


def test_app_requirements_match_local_dashboard_runtime() -> None:
    text = (ROOT / "app" / "requirements.txt").read_text(encoding="utf-8")
    assert "-e .." in text
    assert "gradio>=6.10.0,<7" in text
    assert "plotly>=5.0,<6" in text


def test_command_docs_do_not_use_bare_bundle_validate() -> None:
    for name in COMMAND_DOC_FILES:
        text = (COMMANDS_DIR / name).read_text(encoding="utf-8")
        assert "databricks bundle validate" not in text, (
            f"{name} should route bundle validation through the safe make target"
        )
        assert "make bundle-validate" in text, f"{name} should document the safe make bundle-validate command"


def test_start_test_and_sync_docs_require_catalog_check() -> None:
    for name in ["start.md", "test.md", "sync.md"]:
        text = (COMMANDS_DIR / name).read_text(encoding="utf-8")
        assert "make bundle-catalog-check" in text, f"{name} should require an explicit catalog existence check"


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
        assert "does not" in text and "prove" in text, f"{path.name} should distinguish validate from deploy proof"


def _load_ci_workflow() -> dict[str, Any]:
    with open(CI_WORKFLOW, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert isinstance(data, dict)
    return data


def _load_codacy_config() -> dict[str, Any]:
    with open(CODACY_CONFIG, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert isinstance(data, dict)
    return data


def _load_publish_workflow() -> dict[str, Any]:
    with open(PUBLISH_WORKFLOW, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert isinstance(data, dict)
    return data


def test_ci_workflow_pins_current_setup_uv_and_codecov_actions() -> None:
    data = _load_ci_workflow()
    lint_steps = data["jobs"]["lint-and-test"]["steps"]
    checkout_step = lint_steps[0]
    assert checkout_step["uses"] == "actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5"

    setup_python_step = next(step for step in lint_steps if step.get("name", "").startswith("Set up Python"))
    assert setup_python_step["uses"] == ("actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065")

    setup_uv_step = next(step for step in lint_steps if step.get("name") == "Install uv")
    assert setup_uv_step["uses"] == "astral-sh/setup-uv@8d55fbecc275b1c35dbe060458839f8d30439ccf"

    codecov_step = next(step for step in lint_steps if step.get("name") == "Upload coverage to Codecov")
    assert codecov_step["uses"] == "codecov/codecov-action@75cd11691c0faa626561e295848008c8a7dddffe"
    assert codecov_step["with"]["files"] == "coverage.xml"
    assert codecov_step["with"]["fail_ci_if_error"] is True
    assert "CODECOV_TOKEN" in codecov_step["env"]["CODECOV_TOKEN"]
    assert "CODECOV_PROJECT_TOKEN" in codecov_step["env"]["CODECOV_TOKEN"]


def test_ci_workflow_uses_default_codacy_analysis_mode() -> None:
    data = _load_ci_workflow()
    codacy_steps = data["jobs"]["codacy"]["steps"]
    codacy_step = next(step for step in codacy_steps if step.get("name") == "Run Codacy Analysis")
    assert codacy_step["uses"] == "codacy/codacy-analysis-cli-action@d43360362776a6789b47b99ae8973510854e2d3d"
    assert "with" not in codacy_step, (
        "Codacy CI should use default analysis mode unless client-side upload mode "
        "is intentionally enabled with matching Codacy settings"
    )


def test_ci_workflow_pins_current_snyk_action() -> None:
    data = _load_ci_workflow()
    snyk_steps = data["jobs"]["snyk"]["steps"]
    checkout_step = snyk_steps[0]
    assert checkout_step["uses"] == "actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5"

    snyk_step = next(step for step in snyk_steps if step.get("name") == "Run Snyk")
    assert snyk_step["uses"] == "snyk/actions/python@9adf32b1121593767fc3c057af55b55db032dc04"


def test_publish_workflow_pins_current_release_actions() -> None:
    data = _load_publish_workflow()
    publish_steps = data["jobs"]["publish"]["steps"]
    checkout_step = publish_steps[0]
    assert checkout_step["uses"] == "actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5"

    setup_python_step = next(step for step in publish_steps if step.get("name") == "Set up Python 3.11")
    assert setup_python_step["uses"] == ("actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065")

    setup_uv_step = next(step for step in publish_steps if step.get("name") == "Install uv")
    assert setup_uv_step["uses"] == "astral-sh/setup-uv@8d55fbecc275b1c35dbe060458839f8d30439ccf"

    publish_step = next(step for step in publish_steps if step.get("name") == "Publish to PyPI")
    assert publish_step["uses"] == ("pypa/gh-action-pypi-publish@ed0c53931b1dc9bd32cbe73a98c7f6766f8a527e")


def test_all_workflow_actions_are_pinned_to_immutable_commits() -> None:
    violations: list[str] = []
    for workflow_path in sorted(WORKFLOWS_DIR.glob("*.yml")):
        raw = workflow_path.read_text(encoding="utf-8")
        for match in WORKFLOW_USES_PATTERN.finditer(raw):
            action = match.group("action")
            ref = match.group("ref")
            if action.startswith("./"):
                continue
            if not re.fullmatch(r"[0-9a-f]{40}", ref):
                violations.append(f"{workflow_path.relative_to(ROOT)}: {action}@{ref}")

    assert not violations, (
        "GitHub Actions workflows must pin every external action to a full commit SHA:\n" + "\n".join(violations)
    )


def test_build_instructions_document_current_quality_control_modes() -> None:
    text = (ROOT / "specs" / "DS-BI-001_Build_Instructions.md").read_text(encoding="utf-8")
    assert "CODECOV_TOKEN" in text
    assert "CODECOV_PROJECT_TOKEN" in text
    assert "SNYK_PROJECT_TOKEN" in text
    assert "Run analysis on your build server" in text
    assert "default analysis mode" in text


def test_root_codacy_config_scopes_non_product_surfaces() -> None:
    data = _load_codacy_config()
    exclude_paths = set(data["exclude_paths"])
    assert {
        ".claude/**",
        ".codacy/**",
        ".github/prompts/**",
        "assets/**",
        "docs/prompts/**",
        "notebooks/**",
        "report/**",
        "uv.lock",
    } <= exclude_paths

    engines = data["engines"]
    for engine_name in ("bandit", "opengrep", "prospector", "pylintpython3"):
        engine = engines[engine_name]
        assert "tests/**" in engine["exclude_paths"]


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
        assert "databricks apps get" in text, f"{path.name} should document the app status proof surface"

    spec_text = (ROOT / "specs" / "DS-IP-001-P4_Phase_4_App_UI_Plan.md").read_text(encoding="utf-8")
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
            "name",
            "type",
            "operator",
            "threshold",
            "track",
            "description",
        }
        assert gate["type"] in ("FAIL", "WARN")
        assert gate["operator"] in (">=", "<=")
        assert isinstance(gate["threshold"], float)


def test_notebooks_expose_template_override_and_runtime_widgets() -> None:
    register_text = (NOTEBOOKS / "01_register_dataset.py").read_text(encoding="utf-8")
    intake_text = (NOTEBOOKS / "03_run_intake_controls.py").read_text(encoding="utf-8")
    drift_text = (NOTEBOOKS / "04_run_drift_gate.py").read_text(encoding="utf-8")
    benchmark_text = (NOTEBOOKS / "05_run_control_benchmark.py").read_text(encoding="utf-8")
    pipeline_text = (NOTEBOOKS / "07_run_dataset_pipeline.py").read_text(encoding="utf-8")
    assert 'dbutils.widgets.text("contract_path", "",' in register_text
    assert 'dbutils.widgets.text("registry_path", "",' in register_text
    assert "runtime_registry_path" in register_text
    assert 'dbutils.widgets.dropdown("require_dataset_backed", "false"' in intake_text
    assert 'dbutils.widgets.dropdown("require_dataset_backed", "false"' in drift_text
    assert 'dbutils.widgets.text("policy_path", "",' in benchmark_text
    assert 'dbutils.widgets.dropdown("require_dataset_backed", "false"' in benchmark_text
    assert "runtime_evidence_dir" in benchmark_text
    assert 'dbutils.widgets.text("dataset_id", "", "Dataset ID from registry")' in pipeline_text


def test_public_docs_describe_current_enterprise_ingest_surface() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    notebooks_readme = (ROOT / "notebooks" / "README.md").read_text(encoding="utf-8")
    templates_readme = (ROOT / "templates" / "README.md").read_text(encoding="utf-8")

    assert "Spark/Unity Catalog tables" in readme
    assert "csv" in readme and "orc" in readme and "excel" in readme
    assert "source.table_name" in notebooks_readme
    assert "baseline.table_name" in notebooks_readme
    assert "read_options" in templates_readme


# --- Phase 3: Dataset selection and evidence query widgets ---


def test_register_notebook_has_registry_widget() -> None:
    text = (NOTEBOOKS / "01_register_dataset.py").read_text(encoding="utf-8")
    assert 'dbutils.widgets.text("registry_path"' in text
    assert "DatasetRegistry" in text


def test_run_notebooks_have_dataset_id_widget() -> None:
    for name in ["03_run_intake_controls.py", "04_run_drift_gate.py", "05_run_control_benchmark.py"]:
        text = (NOTEBOOKS / name).read_text(encoding="utf-8")
        assert 'dbutils.widgets.text("dataset_id"' in text, f"{name} missing dataset_id widget"


def test_review_notebook_has_filter_widgets() -> None:
    text = (NOTEBOOKS / "06_review_evidence.py").read_text(encoding="utf-8")
    for widget in ["catalog", "schema", "evidence_dir", "dataset_id", "run_kind", "run_id", "date_from", "date_to"]:
        assert f'dbutils.widgets.text("{widget}"' in text, f"06_review_evidence.py missing {widget} widget"
    assert "list_evidence" in text
    assert "load_evidence" in text
    assert "runtime_evidence_dir" in text


def test_notebooks_delegate_to_package_code() -> None:
    """Notebooks must not re-implement registry, lookup, or orchestration logic."""
    for name in NOTEBOOK_FILES:
        text = (NOTEBOOKS / name).read_text(encoding="utf-8")
        assert "class DatasetRegistry" not in text, f"{name} re-implements DatasetRegistry instead of importing"
        assert "def list_evidence" not in text, f"{name} re-implements list_evidence instead of importing"


def test_nyc_taxi_example_ships_required_files() -> None:
    example_dir = ROOT / "examples" / "nyc_yellow_taxi"
    expected = {
        "dataset_contract.yml",
        "drift_policy.yml",
        "benchmark_policy.yml",
        "README.md",
    }
    actual = {p.name for p in example_dir.iterdir() if p.is_file()}
    missing = expected - actual
    assert not missing, f"examples/nyc_yellow_taxi/ is missing required files: {sorted(missing)}"

    contract = yaml.safe_load((example_dir / "dataset_contract.yml").read_text(encoding="utf-8"))
    assert contract["dataset"]["name"] == "nyc_yellow_taxi"
    assert contract["contract"]["batch_identifier"] == "tpep_pickup_datetime"
    assert len(contract["contract"]["business_key"]) == 8


def test_nyc_taxi_demo_script_is_executable_and_wired() -> None:
    script = ROOT / "scripts" / "run_nyc_taxi_demo.sh"
    assert script.is_file(), "scripts/run_nyc_taxi_demo.sh is missing"
    mode = script.stat().st_mode
    assert mode & 0o111, "scripts/run_nyc_taxi_demo.sh must be executable"

    text = script.read_text(encoding="utf-8")
    assert text.startswith("#!/usr/bin/env bash"), "demo script must declare a bash shebang"
    assert "driftsentinel registry add" in text
    assert "driftsentinel databricks connect" in text
    assert "--wait" in text

    makefile_text = MAKEFILE.read_text(encoding="utf-8")
    assert "demo-nyc-taxi:" in makefile_text
    assert "scripts/run_nyc_taxi_demo.sh" in makefile_text


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
