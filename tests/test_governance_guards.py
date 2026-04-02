"""Regression guards for scaffold integrity and bundle wiring."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

EXECUTABLE_SURFACES = (
    ROOT / "databricks.yml",
    ROOT / "src",
    ROOT / "tests",
    ROOT / "notebooks",
    ROOT / "resources",
    ROOT / "templates",
)

TEXT_SUFFIXES = {".py", ".toml", ".yml", ".yaml"}

BANNED_MARKERS = re.compile(
    r"\b(?:to" r"do|fix" r"me|tb" r"d|place" r"holder)\b",
    re.IGNORECASE,
)


def _iter_surface_files() -> list[Path]:
    files: list[Path] = []
    for surface in EXECUTABLE_SURFACES:
        if surface.is_file():
            files.append(surface)
            continue
        files.extend(
            path
            for path in surface.rglob("*")
            if path.is_file() and path.suffix in TEXT_SUFFIXES and "__pycache__" not in path.parts
        )
    return sorted(files)


def test_executable_surfaces_have_no_banned_markers() -> None:
    violations: list[str] = []
    for path in _iter_surface_files():
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            if BANNED_MARKERS.search(line):
                rel_path = path.relative_to(ROOT)
                violations.append(f"{rel_path}:{lineno}: {line.strip()}")

    assert not violations, "Found banned scaffold markers:\n" + "\n".join(violations)


def test_bundle_config_uses_external_auth_and_includes_resources() -> None:
    config_path = ROOT / "databricks.yml"
    raw = config_path.read_text(encoding="utf-8")

    assert 'include:\n  - "resources/*.yml"' in raw
    assert "${var.databricks_host}" not in raw
    assert "databricks_host:" not in raw
