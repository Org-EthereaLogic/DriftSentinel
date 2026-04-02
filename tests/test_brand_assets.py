from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BRAND_ROOT = ROOT / "assets" / "driftsentinel-brand-system"


def test_brand_system_files_exist() -> None:
    required = [
        BRAND_ROOT / "README.md",
        BRAND_ROOT / "generate_brand_assets.py",
        BRAND_ROOT / "source" / "driftsentinel-mark-source.svg",
        BRAND_ROOT / "source" / "driftsentinel-logo-source.svg",
        BRAND_ROOT / "favicons" / "favicon.ico",
        BRAND_ROOT / "favicons" / "site.webmanifest",
        BRAND_ROOT / "social" / "og-image.png",
        BRAND_ROOT / "variants" / "logo-transparent.png",
    ]

    for path in required:
        assert path.is_file(), f"Missing brand asset: {path.relative_to(ROOT)}"
        assert path.stat().st_size > 0, f"Empty brand asset: {path.relative_to(ROOT)}"


def test_web_manifest_matches_exported_icons() -> None:
    manifest = json.loads((BRAND_ROOT / "favicons" / "site.webmanifest").read_text(encoding="utf-8"))

    assert manifest["name"] == "DriftSentinel"
    assert manifest["short_name"] == "DriftSentinel"
    assert manifest["theme_color"] == "#071824"
    assert manifest["background_color"] == "#071824"

    icon_sources = {item["src"] for item in manifest["icons"]}
    assert icon_sources == {"android-chrome-192x192.png", "android-chrome-512x512.png"}
