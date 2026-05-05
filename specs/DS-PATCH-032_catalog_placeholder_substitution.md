# DS-PATCH-032: Substitute ${CATALOG} Placeholder at YAML Load Time

| Field | Value |
| --- | --- |
| Document ID | DS-PATCH-032 |
| GitHub Issue | [#32](https://github.com/Org-EthereaLogic/DriftSentinel/issues/32) |
| Version | 1.0 |
| Status | Approved |
| Author | Anthony Johnson |
| Date | 2026-05-04 |
| Labels | area:config, type:improvement, priority:p1, demo:friction |

## Problem

`load_dataset_contract`, `load_drift_policy`, and `load_benchmark_policy` (and
their `load_packaged_*` variants) in `src/driftsentinel/config/loader.py` read
YAML files verbatim. The shipped templates use `${CATALOG}` placeholders in
path fields (e.g. `landing_path: /Volumes/${CATALOG}/default/landing/...`), but
no substitution happens — the literal string is what makes it into the registry
and gets uploaded to Databricks.

**Root cause of the demo regression (2026-05-04):** operators had to manually
`sed 's/${CATALOG}/driftsentinel_dev/g'` all three YAML files before upload.
The CLI already receives `catalog`, `schema`, and `volume_name` — they are just
not threaded into the loaders.

## Scope

| File | Change |
| --- | --- |
| `src/driftsentinel/config/loader.py` | Add `_substitute_placeholders` helper; update all 6 loader signatures |
| `src/driftsentinel/databricks/connect.py` | Resolve local YAML paths before `files.sync_files` uploads them |
| `tests/test_config_loading.py` | Add substitution unit tests per acceptance criteria |
| `templates/dataset_contract.yml` | Replace `example_catalog` literals with `${CATALOG}`/`${SCHEMA}` |
| `templates/drift_policy.yml` | Same |
| `templates/benchmark_policy.yml` | Same (if any path fields are present) |

## Design

### 1. `_substitute_placeholders` helper

```python
_PLACEHOLDER_MAP = {
    "${CATALOG}": "catalog",
    "${SCHEMA}": "schema",
    "${VOLUME}": "volume_name",
}

def _substitute_placeholders(
    data: Any,
    *,
    catalog: str | None,
    schema: str | None,
    volume_name: str | None,
) -> Any:
    """Recursively replace ${CATALOG}, ${SCHEMA}, ${VOLUME} in string leaves.

    Only substitutes a placeholder when the corresponding kwarg is not None.
    Non-string leaves are returned unchanged.
    """
    subs = {
        "${CATALOG}": catalog,
        "${SCHEMA}": schema,
        "${VOLUME}": volume_name,
    }
    if isinstance(data, dict):
        return {k: _substitute_placeholders(v, catalog=catalog, schema=schema, volume_name=volume_name)
                for k, v in data.items()}
    if isinstance(data, list):
        return [_substitute_placeholders(item, catalog=catalog, schema=schema, volume_name=volume_name)
                for item in data]
    if isinstance(data, str):
        result = data
        for placeholder, value in subs.items():
            if value is not None:
                result = result.replace(placeholder, value)
        return result
    return data
```

**Properties:**
- Backward compatible: all kwargs default to `None`; omitting them leaves
  placeholders intact exactly as before.
- Single-pass per string: no double-substitution risk (a value that happens to
  contain `${CATALOG}` after substitution is not re-processed).
- Pure function; no mutation of the input dict.

### 2. Updated loader signatures

All six loaders gain three keyword-only kwargs with `None` defaults:

```python
def load_dataset_contract(
    path: str | Path,
    *,
    catalog: str | None = None,
    schema: str | None = None,
    volume_name: str | None = None,
) -> dict[str, Any]:
    p = resolve_trusted_file(path, ...)
    data = _load_yaml(p)
    data = _substitute_placeholders(data, catalog=catalog, schema=schema, volume_name=volume_name)
    return _validate_dataset_contract(data, ...)
```

Apply the same pattern to `load_drift_policy`, `load_benchmark_policy`, and
their three `load_packaged_*` variants.

**Ordering:** substitution happens AFTER `_load_yaml` and BEFORE `_validate_*`.
This ensures the validator sees the resolved strings.

### 3. CLI wiring in `connect.py`

`connect.py` currently passes local policy paths directly to `files.sync_files`
without loading them first. With this patch, `connect()` and `run()` will:

1. Detect when a local drift/benchmark policy path is provided.
2. Load it with the appropriate loader (passing `catalog`, `schema`,
   `volume_name`), producing a resolved dict.
3. Dump the resolved dict to a `tempfile.NamedTemporaryFile` (`.yml`).
4. Pass the temp path to `files.sync_files` in place of the original path.
5. The temp file is cleaned up after `sync_files` returns.

This is the minimal change required: no API change to `files.sync_files`, no
new abstraction layer.

**Helper to add to `connect.py`:**

```python
def _resolve_local_yaml(
    path: str | Path,
    loader_fn: Callable[..., dict[str, Any]],
    *,
    catalog: str,
    schema: str,
    volume_name: str,
) -> Path:
    """Load and substitute a local YAML, writing the resolved content to a temp file."""
    import tempfile
    import yaml as _yaml
    resolved = loader_fn(path, catalog=catalog, schema=schema, volume_name=volume_name)
    tmp = tempfile.NamedTemporaryFile(
        suffix=".yml", mode="w", encoding="utf-8", delete=False
    )
    _yaml.safe_dump(resolved, tmp)
    tmp.close()
    return Path(tmp.name)
```

Call sites in `connect()` and `run()` resolve drift/benchmark policy paths
before passing to `files.sync_files`.

### 4. Template updates

Replace all `example_catalog` literals in path/table_name fields with
`${CATALOG}` (and `default` schema fields with `${SCHEMA}` where appropriate).
Add a header comment to each template explaining placeholder resolution:

```yaml
# Placeholders ${CATALOG}, ${SCHEMA}, and ${VOLUME} are resolved at load time
# when catalog=, schema=, or volume_name= are supplied to the loader.
```

## Acceptance Criteria

From issue #32, mapped to validation steps:

| # | Criterion | Validation |
| --- | --- | --- |
| AC-1 | `load_dataset_contract(path, catalog="c")` substitutes `${CATALOG}` in all string leaf values | Unit test: nested `landing_path` and `catalog` fields resolve correctly |
| AC-2 | Same substitution in `load_drift_policy` and `load_benchmark_policy` | Unit tests per loader |
| AC-3 | Same substitution in `load_packaged_*` variants | Unit tests per packaged loader |
| AC-4 | CLI `connect` and `run` resolve local YAML paths before upload | Integration: temp file path differs from original; resolved YAML contains catalog name |
| AC-5 | Backward compatible: omitting kwargs leaves `${CATALOG}` intact | Unit test: `load_dataset_contract(path)` with no kwargs preserves placeholders |
| AC-6 | Missing individual kwargs leave their placeholders intact | Unit test: `catalog=None, schema="s"` — `${CATALOG}` survives, `${SCHEMA}` resolves |
| AC-7 | No double-substitution when a resolved value contains `${CATALOG}` literally | Unit test: value `"${CATALOG}_suffix"` with `catalog="c"` → `"c_suffix"` not `"c_suffix"` re-processed |
| AC-8 | Unit tests pass under `make test` | CI green |
| AC-9 | `make lint` and `make typecheck` pass | CI green |

## Validation Steps

1. `make lint` — Ruff clean.
2. `make typecheck` — mypy clean (type annotations on new helper and updated
   signatures must be complete).
3. `make test` — full pytest suite passes including the new substitution cases.
4. Manual smoke: create a temp YAML with `${CATALOG}` in `landing_path`, call
   `load_dataset_contract(path, catalog="smoke_catalog")`, assert the resolved
   value contains `smoke_catalog`.

## Out of Scope

- Substituting environment variable placeholders beyond `${CATALOG}`,
  `${SCHEMA}`, `${VOLUME}` (future issue).
- Validation that the resolved paths actually exist on Databricks (separate
  concern handled by `doctor`).
- Changing the `DatasetRegistry` load/save paths (JSON, not YAML — no
  placeholder syntax used there).
