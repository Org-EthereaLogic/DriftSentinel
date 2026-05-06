# DS-PATCH-039: `driftsentinel registry` CLI Subcommands

| Field | Value |
| --- | --- |
| Document ID | DS-PATCH-039 |
| GitHub Issue | [#40](https://github.com/Org-EthereaLogic/DriftSentinel/issues/40) |
| Version | 1.0 |
| Status | Approved |
| Author | Anthony Johnson |
| Date | 2026-05-05 |
| Labels | area:cli, type:feature, priority:p2, demo:friction |
| Methodology precedence | FailLens_Core (explicit failure on collision), DS-SDD-001 §Application Layer / §CLI Surface, DS-SRS DS-FR-004 / DS-SR-005 |

## 1. Problem Statement

Building `registry.json` from a dataset contract today requires a 5-line
Python snippet:

```python
from driftsentinel.config.loader import DatasetRegistry, load_dataset_contract
contract = load_dataset_contract("configs/nyc_taxi/dataset_contract.yml")
reg = DatasetRegistry()
reg.register(contract)
reg.save("data/registry.json")
```

The `driftsentinel` CLI exposes `databricks {connect,run,status,sync,doctor}`
but no surface for managing the registry that those commands consume. The gap
forces operators (and the E2E verification runbook) to drop into Python to do
the one thing every dataset-backed flow requires first.

`EVIDENCE_LOG.md` Phase 5 in `DriftSentinel_demo` records this friction
explicitly: "Registry built locally" required a Python snippet rather than a
single CLI call.

## 2. Goal

Expose the registry surface as first-class CLI subcommands so operators never
need to write Python to register, list, or remove a dataset contract:

- `driftsentinel registry add --contract <yml> [--registry <json>] [--catalog X --schema Y --volume-name Z] [--force]`
- `driftsentinel registry list [--registry <json>]`
- `driftsentinel registry remove --dataset-id X --contract-version Y [--registry <json>]`

## 3. Non-Goals

- Replacing `DatasetRegistry`, the loader, or the JSON registry format. The
  CLI is a thin wrapper; the persistence shape is unchanged.
- Adding new placeholder substitution semantics. The `add` command threads
  `--catalog/--schema/--volume-name` straight into `load_dataset_contract` and
  reuses the substitution behavior delivered in DS-PATCH-032.
- Adding registry mutation surfaces beyond add/list/remove (e.g., bulk import,
  diff, merge). Each is out of scope here and will land in its own spec if
  motivated.

## 4. Design

### 4.1 Subcommand surface

| Command | Required | Optional | Effect |
| --- | --- | --- | --- |
| `registry add` | `--contract <path>` | `--registry <path>` (default `data/registry.json`), `--catalog`, `--schema`, `--volume-name`, `--force` | Loads the contract, validates it, then registers it in the JSON registry. Creates the registry file if missing. |
| `registry list` | — | `--registry <path>` (default `data/registry.json`) | Prints `(dataset_id, contract_version)` rows. |
| `registry remove` | `--dataset-id`, `--contract-version` | `--registry <path>` (default `data/registry.json`) | Removes the matching entry and rewrites the registry file. |

### 4.2 Failure modes

The CLI converts library exceptions into `exit 1` with a one-line stderr
message. No silent fallbacks:

| Condition | Exit | Message contains |
| --- | --- | --- |
| `add` collision on `(dataset_id, contract_version)` without `--force` | 1 | `already registered`, `--force` |
| `add --force` on a previously-registered identity | 0 | replaces the entry in place (single, deterministic write) |
| `list` against a non-existent registry path | 1 | `not found` |
| `remove` against a non-existent registry path | 1 | `not found` |
| `remove` on an unknown `(dataset_id, contract_version)` | 1 | `not registered` |
| `add` against a contract YAML that fails `_validate_dataset_contract` | nonzero (raised by the loader) | the loader's `ConfigError` text |

### 4.3 Default registry path

The default `--registry` value is `data/registry.json` (matching the
established demo and runbook layout). When the file does not exist on `add`,
the CLI creates it; `list` and `remove` do not create files and require an
existing path.

### 4.4 Placeholder substitution

`add` accepts the same `--catalog/--schema/--volume-name` flags as
`databricks connect` and threads them into `load_dataset_contract`. This is
the single substitution point — once the contract is registered, the JSON
registry stores the resolved (post-substitution) form.

### 4.5 Documentation surface

| File | Change |
| --- | --- |
| `docs/deployment_guide.md` | New "Build the Registry" section ahead of the run section, replacing implicit reliance on the Python snippet. |
| `docs/e2e_verification_prompt.md` | TASK 2.2, 2.4, and 2.5 updated to use the CLI rather than ad-hoc Python. |

## 5. Files Touched

| File | Change |
| --- | --- |
| `src/driftsentinel/cli.py` | New `registry` subparser group with `add/list/remove` handlers and a `DEFAULT_REGISTRY_PATH = "data/registry.json"` constant. |
| `tests/test_cli.py` | New `TestCLIParser::test_registry_*` parser tests; new `TestRegistryAddCommand`, `TestRegistryListCommand`, `TestRegistryRemoveCommand` classes covering create-on-missing, append, collision (with and without `--force`), placeholder substitution, list of empty/populated registry, and remove paths. |
| `docs/deployment_guide.md` | New "Build the Registry" section. |
| `docs/e2e_verification_prompt.md` | TASK 2.2, 2.4, and 2.5 switched from Python snippet to CLI. |
| `specs/DS-TM-001_Traceability_Matrix.md` | Append DS-PATCH-039 to the DS-FR-004 / DS-SR-005 row and add a 1.7 changelog entry on 2026-05-05. |

No source under `src/driftsentinel/config/`, `src/driftsentinel/databricks/`,
notebooks, bundle resources, or runtime volume layout changes.

## 6. Validation

### 6.1 Unit tests (added in `tests/test_cli.py`)

- `TestCLIParser::test_registry_no_command_shows_help`
- `TestCLIParser::test_registry_add_requires_contract`
- `TestCLIParser::test_registry_remove_requires_dataset_and_version`
- `TestCLIParser::test_registry_add_parses_all_args`
- `TestCLIParser::test_registry_list_uses_default_registry`
- `TestCLIParser::test_registry_remove_parses_required_args`
- `TestRegistryAddCommand::{test_creates_new_registry_when_missing, test_appends_to_existing_registry, test_collision_without_force_returns_error, test_collision_with_force_replaces_entry, test_substitutes_placeholders_when_supplied}`
- `TestRegistryListCommand::{test_missing_registry_returns_error, test_lists_registered_datasets}`
- `TestRegistryRemoveCommand::{test_removes_existing_entry, test_unknown_entry_returns_error, test_missing_registry_returns_error}`

### 6.2 Required local checks

```bash
uv run ruff check .
uv run mypy src/driftsentinel tests
uv run pytest -k test_cli
uv run pytest
```

### 6.3 Manual smoke test (post-merge)

```bash
uv run driftsentinel registry add \
  --contract templates/dataset_contract.yml \
  --registry /tmp/ds_registry.json \
  --catalog adb_dev --schema default --volume-name driftsentinel_runtime
uv run driftsentinel registry list --registry /tmp/ds_registry.json
uv run driftsentinel registry remove \
  --dataset-id example_dataset --contract-version 1.0.0 \
  --registry /tmp/ds_registry.json
```

Expected: each command exits 0, the JSON registry exists between calls, and
`remove` leaves the file with an empty `registry: []` array.

## 7. Acceptance Criteria

- [x] `driftsentinel registry add --contract <path>` loads, validates, and
  registers the contract into the JSON registry, creating the file when
  missing.
- [x] `--registry` defaults to `data/registry.json`; explicit overrides are
  honored.
- [x] `--catalog/--schema/--volume-name` substitute placeholders in the
  contract before registration (DS-PATCH-032 behavior, threaded through).
- [x] Collisions on `(dataset_id, contract_version)` exit 1 unless `--force`
  is supplied; with `--force`, the existing entry is replaced.
- [x] `driftsentinel registry list` prints the registered datasets.
- [x] `driftsentinel registry remove --dataset-id X --contract-version Y`
  removes the matching entry and rewrites the registry file.
- [x] Unit tests cover all three subcommands across the listed failure modes.
- [x] `docs/deployment_guide.md` documents the new flow.
- [x] `docs/e2e_verification_prompt.md` uses the CLI rather than the Python
  snippet for registration tasks.
- [x] `specs/DS-TM-001_Traceability_Matrix.md` references DS-PATCH-039.
- [x] `make lint`, `make typecheck`, `make test` all pass.

## 8. Residual Risks

- **Default registry path.** `data/registry.json` is repo-relative; running
  the CLI from a different working directory writes to a `data/` directory at
  that location. Mitigation: operators always pass `--registry` explicitly in
  the deployment runbook; the default is for local demo loops.
- **Path security envelope.** `DatasetRegistry.save/load` go through
  `resolve_trusted_file`, so registry paths must live under the repo, the
  system temp dir, or a root listed in `DRIFTSENTINEL_ALLOWED_PATH_ROOTS`.
  Operators using arbitrary absolute paths must export that env var (already
  the documented pattern).
- **Placeholder substitution scope.** The CLI threads catalog/schema/volume
  through `load_dataset_contract` only. Drift and benchmark policies, which
  are not touched here, continue to be substituted at run time (DS-PATCH-032
  remains the single source of truth for that contract).

## 9. Traceability

- DS-PRD: §Operator-Friendly Bundle, §CLI Surface.
- DS-SRS: DS-FR-004 (dataset contract authoring), DS-SR-005 (registry as the
  multi-dataset state of record).
- DS-SDD-001: §Application Layer (CLI), §Configuration Layer.
- DS-TP-001: §CLI test surface.
- Issue #40 acceptance criteria mapped 1:1 to §7 above.
- DS-PATCH-032 is the upstream dependency for the placeholder substitution
  behavior that `registry add` re-exposes via the new flags.
