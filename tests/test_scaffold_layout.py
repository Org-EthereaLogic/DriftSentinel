"""Verify the DriftSentinel scaffold layout.

This test confirms that the greenfield scaffold created the expected directory
structure and key files. It runs as part of the standard pytest suite and
serves as a regression gate against accidental scaffold erosion.
"""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


# --- Root governance files ---


@pytest.mark.parametrize(
    "filename",
    [
        "README.md",
        "AGENTS.md",
        "CLAUDE.md",
        "CONSTITUTION.md",
        "DIRECTIVES.md",
        "SECURITY.md",
        "CONTRIBUTING.md",
        "LICENSE",
        "Makefile",
        ".gitignore",
        "pyproject.toml",
        "requirements.txt",
        "databricks.yml",
        "codecov.yaml",
        ".snyk",
    ],
)
def test_root_governance_file_exists(filename: str) -> None:
    assert (ROOT / filename).is_file(), f"Missing root file: {filename}"


# --- Quality-control integration ---


@pytest.mark.parametrize(
    "path",
    [
        ".github/workflows/ci.yml",
        ".codacy.yml",
        ".codacy/README.md",
    ],
)
def test_quality_control_file_exists(path: str) -> None:
    assert (ROOT / path).is_file(), f"Missing quality-control file: {path}"


# --- Canonical specs ---


@pytest.mark.parametrize(
    "spec",
    [
        "DS-PRD-001_Product_Requirements_Document.md",
        "DS-SRS-001_Software_Requirements_Specification.md",
        "DS-SDD-001_Architecture_Blueprint.md",
        "DS-IP-001_Implementation_Plan.md",
        "DS-TP-001_Test_Plan.md",
        "DS-TM-001_Traceability_Matrix.md",
        "DS-SCMP-001_Software_Configuration_Management_Plan.md",
        "DS-US-001_User_Stories_Acceptance_Criteria.md",
        "DS-WBS-001_Project_Plan_WBS.md",
        "DS-BI-001_Build_Instructions.md",
    ],
)
def test_spec_exists(spec: str) -> None:
    assert (ROOT / "specs" / spec).is_file(), f"Missing spec: {spec}"


def test_specs_readme_exists() -> None:
    assert (ROOT / "specs" / "README.md").is_file()


def test_deep_specs_readme_exists() -> None:
    assert (ROOT / "specs" / "deep_specs" / "README.md").is_file()


def test_schema_readme_exists() -> None:
    assert (ROOT / "specs" / "schema" / "README.md").is_file()


# --- Docs ---


@pytest.mark.parametrize(
    "doc",
    [
        "architecture.md",
        "deployment_guide.md",
        "operations_guide.md",
        "github_project_sync.md",
        "notion_dashboard_sync.md",
    ],
)
def test_doc_exists(doc: str) -> None:
    assert (ROOT / "docs" / doc).is_file(), f"Missing doc: {doc}"


# --- Claude commands (21 expected) ---

EXPECTED_COMMANDS = [
    "prime",
    "start",
    "plan",
    "implement",
    "review",
    "verify",
    "test",
    "audit",
    "feature",
    "bug",
    "patch",
    "chore",
    "classify_issue",
    "generate_branch_name",
    "commit",
    "pull-request",
    "git",
    "doc-maintain",
    "document",
    "cleanup_workspace",
    "sync",
]


@pytest.mark.parametrize("cmd", EXPECTED_COMMANDS)
def test_command_exists(cmd: str) -> None:
    assert (ROOT / ".claude" / "commands" / f"{cmd}.md").is_file(), f"Missing command: {cmd}.md"


def test_command_count() -> None:
    cmd_dir = ROOT / ".claude" / "commands"
    commands = [f for f in cmd_dir.iterdir() if f.suffix == ".md" and f.name != "README.md"]
    assert len(commands) == 21, f"Expected 21 commands, found {len(commands)}"


# --- Claude agents (5 expected) ---

EXPECTED_AGENTS = [
    "lead-software-engineer",
    "sdlc-technical-writer",
    "test-automator",
    "python-pro",
    "ux-delight-specialist",
]


@pytest.mark.parametrize("agent", EXPECTED_AGENTS)
def test_agent_exists(agent: str) -> None:
    assert (ROOT / ".claude" / "agents" / f"{agent}.md").is_file(), f"Missing agent: {agent}.md"


# --- Claude hooks (8 expected) ---

EXPECTED_HOOKS = [
    "pre-tool-use.js",
    "post-tool-use.js",
    "user-prompt-submit.js",
    "notification.js",
    "pre-compact.js",
    "stop.js",
    "subagent-stop.js",
    "utils.js",
]


@pytest.mark.parametrize("hook", EXPECTED_HOOKS)
def test_hook_exists(hook: str) -> None:
    assert (ROOT / ".claude" / "hooks" / hook).is_file(), f"Missing hook: {hook}"


# --- Claude settings ---


def test_claude_settings_exists() -> None:
    assert (ROOT / ".claude" / "settings.json").is_file()


# --- Reserved surfaces ---


def test_adws_readme_exists() -> None:
    assert (ROOT / "adws" / "README.md").is_file()


def test_report_readme_exists() -> None:
    assert (ROOT / "report" / "README.md").is_file()


# --- Databricks surfaces ---


@pytest.mark.parametrize(
    "resource",
    [
        "intake_pipeline.yml",
        "drift_gate_job.yml",
        "benchmark_job.yml",
        "dataset_pipeline_job.yml",
        "driftsentinel_app.yml",
        "runtime_volume.yml",
    ],
)
def test_resource_exists(resource: str) -> None:
    assert (ROOT / "resources" / resource).is_file(), f"Missing resource: {resource}"


@pytest.mark.parametrize(
    "notebook",
    [
        "00_quickstart_setup.py",
        "01_register_dataset.py",
        "02_seed_or_import_baseline.py",
        "03_run_intake_controls.py",
        "04_run_drift_gate.py",
        "05_run_control_benchmark.py",
        "06_review_evidence.py",
        "07_run_dataset_pipeline.py",
    ],
)
def test_notebook_exists(notebook: str) -> None:
    assert (ROOT / "notebooks" / notebook).is_file(), f"Missing notebook: {notebook}"


@pytest.mark.parametrize(
    "template",
    [
        "dataset_contract.yml",
        "drift_policy.yml",
        "benchmark_policy.yml",
    ],
)
def test_template_exists(template: str) -> None:
    assert (ROOT / "templates" / template).is_file(), f"Missing template: {template}"


# --- Package layout ---


@pytest.mark.parametrize(
    "subpackage",
    [
        "config",
        "intake",
        "drift",
        "benchmark",
        "evidence",
        "orchestration",
    ],
)
def test_subpackage_exists(subpackage: str) -> None:
    init = ROOT / "src" / "driftsentinel" / subpackage / "__init__.py"
    assert init.is_file(), f"Missing subpackage init: {subpackage}"


def test_root_package_init() -> None:
    assert (ROOT / "src" / "driftsentinel" / "__init__.py").is_file()


def test_runtime_paths_module_exists() -> None:
    assert (ROOT / "src" / "driftsentinel" / "runtime_paths.py").is_file()


def test_tests_init() -> None:
    assert (ROOT / "tests" / "__init__.py").is_file()


@pytest.mark.parametrize(
    "path",
    [
        "app/README.md",
        "app/__init__.py",
        "app/app.py",
        "app/app.yaml",
        "app/requirements.txt",
    ],
)
def test_app_surface_exists(path: str) -> None:
    assert (ROOT / path).is_file(), f"Missing app surface: {path}"


@pytest.mark.parametrize(
    "path",
    [
        "scripts/README.md",
        "scripts/deploy_databricks_app.py",
    ],
)
def test_scripts_surface_exists(path: str) -> None:
    assert (ROOT / path).is_file(), f"Missing scripts surface: {path}"
