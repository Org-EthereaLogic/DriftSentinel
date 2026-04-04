"""Tests for trusted path normalization."""

from __future__ import annotations

import pytest

from driftsentinel.paths import resolve_trusted_path


def test_resolve_trusted_path_normalizes_dbfs_uri(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DRIFTSENTINEL_ALLOWED_PATH_ROOTS", "/dbfs")
    resolved = resolve_trusted_path("dbfs:/tmp/driftsentinel/sample.csv", context="DBFS sample path")
    assert str(resolved) == "/dbfs/tmp/driftsentinel/sample.csv"
