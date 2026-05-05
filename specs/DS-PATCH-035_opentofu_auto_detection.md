# DS-PATCH-035 — Auto-Detect OpenTofu and Set `DATABRICKS_TF_EXEC_PATH`

| Field | Value |
| --- | --- |
| Tracking issue | [Org-EthereaLogic/DriftSentinel#35](https://github.com/Org-EthereaLogic/DriftSentinel/issues/35) |
| Type | improvement |
| Area | `area:bundle`, `area:docs` |
| Priority | p2 |
| Status | Planned |
| Owner | lead-software-engineer |
| Methodology precedence | FailLens_Core (explicit, actionable failure), E62 (Databricks runtime path), DS-SDD-001 §Application Layer / §Bundle Operations |

## 1. Problem Statement

The Databricks CLI pins terraform `1.5.5` and verifies the auto-downloaded
binary against an upstream PGP signature that expired in 2025. On a fresh
machine, the very first `databricks bundle deploy` (and any other
`databricks bundle …` invocation that materializes terraform state) fails
with:

> `Error: error downloading Terraform: unable to verify checksums signature: openpgp: key expired`

This blocks every Make-driven deployment surface in this repository:

- `make bundle-validate` (direct `databricks bundle validate` call)
- `make app-deploy` (which calls `scripts/deploy_databricks_app.py`,
  which runs `databricks bundle deploy` / `databricks bundle summary`
  and `databricks apps deploy`)
- `make bootstrap` (which calls `uv run driftsentinel databricks connect`,
  which calls `databricks bundle deploy` through
  `src/driftsentinel/databricks/bundle.py`)

The repository EVIDENCE_LOG (issue #35 §Evidence) records two consecutive
deploy failures with the PGP-expired error before the manual OpenTofu
workaround unblocked the demo.

The Databricks CLI honors two operator-set environment variables that bypass
the bundled terraform path entirely:

- `DATABRICKS_TF_EXEC_PATH` — absolute path to a terraform-compatible binary
- `DATABRICKS_TF_VERSION` — declared version of that binary

OpenTofu (`tofu`) is a wire-compatible drop-in for terraform that the
Databricks CLI accepts when these env vars point at it. Setting both
unblocks every bundle command without requiring any change in the
Databricks CLI itself.

## 2. Goal

Every Make target that invokes the Databricks CLI for bundle or app
operations auto-detects OpenTofu and pre-sets `DATABRICKS_TF_EXEC_PATH`
(and `DATABRICKS_TF_VERSION` when unset) before the CLI runs, so a fresh
machine with `brew install opentofu` succeeds on the first deploy.
Operator overrides are preserved. When neither `tofu` nor `terraform` is
available and no override is set, the surface fails closed with a single
actionable message recommending `brew install opentofu`.

## 3. Non-Goals

- Fixing the upstream Databricks CLI terraform pin or PGP key cache —
  that is a Databricks-side concern.
- Bundling, vendoring, or auto-installing OpenTofu itself.
- Adding `tofu` as a Python dependency, `pyproject.toml` extra, or
  `make sync` install step — operators install it through their package
  manager (`brew install opentofu` on macOS).
- Pinning terraform binaries inside CI — CI does not currently run
  `databricks bundle …` end-to-end (no Databricks credentials in CI).
- Changing bundle resources, job parameter schemas, or runtime volume
  layout. This patch is purely an environment-resolution shim.

## 4. Design

### 4.1 Detection precedence

A single, deterministic precedence order applies everywhere the shim
runs (Make targets and Python subprocess wrappers):

1. **Operator override.** If `DATABRICKS_TF_EXEC_PATH` is already set in
   the environment, do nothing. The operator's choice wins. Do not log
   a warning; do not validate the path.
2. **OpenTofu on PATH.** If `command -v tofu` resolves, export
   `DATABRICKS_TF_EXEC_PATH=<resolved tofu path>`. Additionally, if
   `DATABRICKS_TF_VERSION` is unset, export
   `DATABRICKS_TF_VERSION=1.11.6` (the version the demo workaround
   pins; aligned with the OpenTofu release line known to satisfy the
   Databricks CLI's terraform-protocol expectations).
3. **System terraform on PATH.** If only `terraform` resolves, export
   `DATABRICKS_TF_EXEC_PATH=<resolved terraform path>`. Do not set
   `DATABRICKS_TF_VERSION`; let the Databricks CLI use its default
   version handling against the user's terraform binary.
4. **Neither available.** Fail closed with the actionable message in
   §4.4. Do not invoke `databricks bundle …`.

### 4.2 Shell helper — `scripts/databricks_tf_env.sh`

A new POSIX-shell helper, designed to be **sourced** (not executed),
exports the env vars in-place. It encapsulates §4.1 once and is reused
by every Make target.

```sh
# scripts/databricks_tf_env.sh
# Source me. I export DATABRICKS_TF_EXEC_PATH (+DATABRICKS_TF_VERSION
# when unset) so 'databricks bundle ...' bypasses the upstream
# terraform 1.5.5 PGP-expired download path.

if [ -n "${DATABRICKS_TF_EXEC_PATH:-}" ]; then
  return 0 2>/dev/null || exit 0
fi

if command -v tofu >/dev/null 2>&1; then
  DATABRICKS_TF_EXEC_PATH="$(command -v tofu)"
  export DATABRICKS_TF_EXEC_PATH
  if [ -z "${DATABRICKS_TF_VERSION:-}" ]; then
    DATABRICKS_TF_VERSION=1.11.6
    export DATABRICKS_TF_VERSION
  fi
  return 0 2>/dev/null || exit 0
fi

if command -v terraform >/dev/null 2>&1; then
  DATABRICKS_TF_EXEC_PATH="$(command -v terraform)"
  export DATABRICKS_TF_EXEC_PATH
  return 0 2>/dev/null || exit 0
fi

echo "DriftSentinel: neither 'tofu' nor 'terraform' is on PATH and DATABRICKS_TF_EXEC_PATH is unset." >&2
echo "  Install OpenTofu (recommended, wire-compatible drop-in for terraform):" >&2
echo "    brew install opentofu" >&2
echo "  Or set DATABRICKS_TF_EXEC_PATH to an existing terraform-compatible binary." >&2
echo "  See specs/DS-PATCH-035_opentofu_auto_detection.md for the upstream PGP-expired context." >&2
return 1 2>/dev/null || exit 1
```

The script is intentionally side-effect-only. It exports vars and
returns/exits with `0` on success or `1` on the fail-closed branch. No
stdout output on success; no positional arguments; no flags.

### 4.3 Makefile wrapping

Each affected Make target sources the helper before its existing
command. Make recipe lines run in their own shell, so the `source` and
the consuming command must be on the same recipe line, joined by `&&`.
The `set -e` ensures the recipe fails immediately if the helper exits
non-zero (the §4.1(4) fail-closed branch).

```make
TF_ENV := . scripts/databricks_tf_env.sh

bundle-validate:
	@$(TF_ENV) && $(DATABRICKS) bundle validate $(PROFILE_ARG) --target dev \
	  --var="catalog=$${BUNDLE_VAR_catalog:-$${CATALOG:?Set CATALOG or BUNDLE_VAR_catalog}}"

bundle-deploy:
	@$(TF_ENV) && $(DATABRICKS) bundle deploy $(PROFILE_ARG) --target dev \
	  --var="catalog=$${BUNDLE_VAR_catalog:-$${CATALOG:?Set CATALOG or BUNDLE_VAR_catalog}}"

app-deploy:
	@$(TF_ENV) && $(UV) run python scripts/deploy_databricks_app.py \
	  $(if $(PROFILE),--profile $(PROFILE),) --target dev \
	  --catalog "$${BUNDLE_VAR_catalog:-$${CATALOG:?Set CATALOG or BUNDLE_VAR_catalog}}"

bootstrap:
	@test -n "$(DATASET_ID)" || (echo "Set DATASET_ID=<registered_dataset>" >&2; exit 2)
	@test -n "$(DRIFT_POLICY)" || (echo "Set DRIFT_POLICY=<local_drift_policy.yml>" >&2; exit 2)
	@$(TF_ENV) && $(UV) run driftsentinel databricks connect \
	  --catalog "$${BUNDLE_VAR_catalog:-$${CATALOG:?Set CATALOG or BUNDLE_VAR_catalog}}" \
	  $(if $(PROFILE),--profile $(PROFILE),) \
	  --dataset-id "$(DATASET_ID)" \
	  $(if $(REGISTRY),--registry "$(REGISTRY)",) \
	  --drift-policy "$(DRIFT_POLICY)" \
	  $(if $(BENCHMARK_POLICY),--benchmark-policy "$(BENCHMARK_POLICY)",) \
	  $(if $(LANDING_PATH),--landing-path "$(LANDING_PATH)",) \
	  $(if $(BASELINE_PATH),--baseline-path "$(BASELINE_PATH)",) \
	  --wait
```

`bundle-deploy` is added (it does not exist today) because the issue
acceptance criteria names it explicitly; the equivalent direct CLI form
is documented in `docs/deployment_guide.md` already.

The `.PHONY` line is updated to declare `bundle-deploy`.

The Make help text (a new `help` target plus a brief comment block at
the top of the Makefile) names OpenTofu as the recommended terraform
binary alongside `make sync`. The issue explicitly asks for this in
`make sync`'s help text; the cleanest way to surface it is a single
`help` target that prints the canonical command list, including a
"Prerequisites" line. `make sync` itself does not change — the install
ergonomics are documentation, not a runtime dependency.

### 4.4 Fail-closed message

When §4.1(4) triggers, the operator sees exactly the four-line block
shown in §4.2. The wording:

- Names both candidate binaries (`tofu`, `terraform`) so the operator
  knows which detection paths failed.
- Recommends `brew install opentofu` as the issue's prescribed fix.
- Names the override env var (`DATABRICKS_TF_EXEC_PATH`) so an
  operator with a non-Homebrew binary already installed knows the
  escape hatch.
- Points at this spec for the upstream context.

The Makefile target exits non-zero before any `databricks` command
runs, so the operator does not see the confusing PGP error first.

### 4.5 Python parity for non-Make callers

Python wrappers that fork `databricks bundle …` outside the Make
surface must apply the same precedence so direct invocations (e.g.,
`uv run driftsentinel databricks connect …`, `uv run python
scripts/deploy_databricks_app.py …`) succeed even when the user
bypasses Make.

Add `src/driftsentinel/databricks/tf_env.py`:

```python
"""Resolve DATABRICKS_TF_EXEC_PATH for subprocess invocations of the
Databricks CLI, working around the upstream terraform 1.5.5 PGP key
expiry. Mirrors scripts/databricks_tf_env.sh."""

from __future__ import annotations

import os
import shutil
from typing import Mapping, MutableMapping

OPENTOFU_VERSION_DEFAULT = "1.11.6"


class TerraformBinaryMissingError(RuntimeError):
    """Raised when no terraform-compatible binary is resolvable."""


def resolve_tf_env(base: Mapping[str, str] | None = None) -> dict[str, str]:
    """Return a copy of the environment with the terraform-binary vars set.

    Precedence matches scripts/databricks_tf_env.sh:
      1. Existing DATABRICKS_TF_EXEC_PATH wins.
      2. tofu on PATH -> set DATABRICKS_TF_EXEC_PATH and (if unset)
         DATABRICKS_TF_VERSION=OPENTOFU_VERSION_DEFAULT.
      3. terraform on PATH -> set DATABRICKS_TF_EXEC_PATH only.
      4. Otherwise raise TerraformBinaryMissingError.
    """
    env: MutableMapping[str, str] = dict(base if base is not None else os.environ)
    if env.get("DATABRICKS_TF_EXEC_PATH"):
        return dict(env)

    tofu = shutil.which("tofu")
    if tofu:
        env["DATABRICKS_TF_EXEC_PATH"] = tofu
        env.setdefault("DATABRICKS_TF_VERSION", OPENTOFU_VERSION_DEFAULT)
        return dict(env)

    terraform = shutil.which("terraform")
    if terraform:
        env["DATABRICKS_TF_EXEC_PATH"] = terraform
        return dict(env)

    raise TerraformBinaryMissingError(
        "DriftSentinel: neither 'tofu' nor 'terraform' is on PATH and "
        "DATABRICKS_TF_EXEC_PATH is unset. Install OpenTofu "
        "(recommended): 'brew install opentofu'. Or set "
        "DATABRICKS_TF_EXEC_PATH to an existing terraform-compatible "
        "binary. See specs/DS-PATCH-035_opentofu_auto_detection.md."
    )
```

`src/driftsentinel/databricks/bundle.py:_run_bundle` calls
`resolve_tf_env()` and passes the result as the `env=` kwarg to
`subprocess.run`. The same applies to `app_start` and `app_get` for
consistency, though they do not go through terraform — passing the
env there is a no-op cost and keeps the wrapper uniform.

`scripts/deploy_databricks_app.py:_run` accepts an optional `env`
parameter and forwards it to `subprocess.run`. `main()` calls
`resolve_tf_env()` once at start and passes the result into every `_run`
invocation. If `TerraformBinaryMissingError` is raised, `main` prints
the message to stderr and returns exit code 2.

### 4.6 Documentation

`docs/deployment_guide.md` gains a new "Terraform binary" subsection
under "Prerequisites" that:

- Names the upstream issue (terraform 1.5.5 bundled by Databricks CLI;
  PGP signature expired 2025).
- Names the recommended fix: `brew install opentofu`.
- States what the Make targets do automatically (auto-set
  `DATABRICKS_TF_EXEC_PATH` and `DATABRICKS_TF_VERSION` when unset).
- Names the manual override path (`export DATABRICKS_TF_EXEC_PATH=…`)
  for operators with a non-Homebrew binary or an alternate version.
- Cross-references this spec for full context.

`README.md` gains a single bullet under "Quickstart > Clone and
develop locally" naming OpenTofu as a Databricks-deploy prerequisite,
linking to the deployment guide section. The README copy stays terse;
deep context lives in the deployment guide and this spec.

### 4.7 Out of scope (re-stated)

- The path-resolved `tofu` binary's version is not validated. The
  `DATABRICKS_TF_VERSION=1.11.6` default matches the demo evidence;
  operators with newer or older OpenTofu builds can override
  `DATABRICKS_TF_VERSION` themselves. Validating the binary's actual
  reported version would add a fork on every Make recipe and is not
  warranted by the failure mode this patch addresses.
- Windows operator workflows are not supported by the existing Make
  targets and remain unsupported by this patch. The shell helper uses
  POSIX shell only; the Python helper is portable but is only invoked
  by callers that already assume a POSIX environment.

## 5. Files Touched

| File | Change |
| --- | --- |
| `scripts/databricks_tf_env.sh` | New — sourceable POSIX shell helper per §4.2 |
| `Makefile` | Wrap `bundle-validate`, `app-deploy`, `bootstrap`; add `bundle-deploy`; add `help` target naming OpenTofu prerequisite; update `.PHONY` |
| `src/driftsentinel/databricks/tf_env.py` | New — Python helper per §4.5 |
| `src/driftsentinel/databricks/bundle.py` | `_run_bundle` / `app_start` / `app_get` pass `env=resolve_tf_env()` to `subprocess.run` |
| `scripts/deploy_databricks_app.py` | `_run` accepts `env` kwarg; `main()` resolves env once and forwards |
| `docs/deployment_guide.md` | New "Terraform binary" subsection per §4.6 |
| `README.md` | One-line OpenTofu prerequisite bullet under quickstart |
| `tests/test_databricks_tf_env.py` | New — Python helper coverage per §6.1 |
| `tests/test_databricks_connect.py` | Extend — `bundle._run_bundle` is patched / spied for env propagation in existing happy-path tests where reasonable |
| `specs/DS-TM-001_Traceability_Matrix.md` | Append a row mapping DS-FR-002 / DS-SR-009 (bundle deploy) to this patch |
| `specs/README.md` | Index entry for `DS-PATCH-035` (per existing convention) |

No source code under `src/driftsentinel/{intake,drift,benchmark,
evidence,orchestration,config}/` changes. No bundle resources, job
parameters, or runtime volume layout change.

## 6. Validation

### 6.1 Unit tests — `tests/test_databricks_tf_env.py`

Mock `shutil.which` and the input env mapping. Cover every branch of
§4.1:

1. **Operator override wins.** Input env contains
   `DATABRICKS_TF_EXEC_PATH=/custom/tf`. `shutil.which` is not called
   for `tofu` or `terraform`. Output env preserves the override and
   does not inject `DATABRICKS_TF_VERSION`.
2. **OpenTofu detected.** `shutil.which("tofu")` returns
   `/opt/homebrew/bin/tofu`. Output env has
   `DATABRICKS_TF_EXEC_PATH=/opt/homebrew/bin/tofu` and
   `DATABRICKS_TF_VERSION=1.11.6` (default applied).
3. **OpenTofu detected, version pre-set.** Same as #2 but input env
   already contains `DATABRICKS_TF_VERSION=1.10.2`. Output env
   preserves `1.10.2` (no override of operator-set version).
4. **OpenTofu absent, terraform present.** `shutil.which("tofu")`
   returns `None`; `shutil.which("terraform")` returns
   `/usr/local/bin/terraform`. Output env has
   `DATABRICKS_TF_EXEC_PATH=/usr/local/bin/terraform` and **no**
   `DATABRICKS_TF_VERSION` injection.
5. **Neither available.** Both `shutil.which` calls return `None`.
   `resolve_tf_env` raises `TerraformBinaryMissingError` with a message
   that contains the strings `tofu`, `terraform`,
   `DATABRICKS_TF_EXEC_PATH`, `brew install opentofu`, and the spec
   filename `DS-PATCH-035`.
6. **Process env unmodified.** When `base` is omitted, the function
   reads `os.environ` but does not mutate it — verified by snapshotting
   `os.environ` before and after.
7. **Empty override is treated as unset.** Input env contains
   `DATABRICKS_TF_EXEC_PATH=""`. The function does not treat the empty
   string as a valid override and proceeds to detection (matches the
   shell `[ -n "${...:-}" ]` semantics). This guards against operators
   exporting an unset variable as empty.

### 6.2 Bundle-wrapper integration tests

Extend `tests/test_databricks_connect.py` (or add minimal coverage to
`tests/test_databricks_files.py` if scoping is cleaner) to assert that
`bundle._run_bundle` invokes `subprocess.run` with an `env` mapping
that includes `DATABRICKS_TF_EXEC_PATH`. Use `monkeypatch` to:

- Set `shutil.which` to return a fixed `tofu` path.
- Capture the `env=` kwarg passed to `subprocess.run`.
- Assert the captured env contains the expected
  `DATABRICKS_TF_EXEC_PATH` and `DATABRICKS_TF_VERSION` values.

This is the contract that prevents regression of §4.5: future edits to
`bundle.py` cannot drop the `env=` propagation without failing this
test.

### 6.3 Required local checks

```bash
uv run ruff check .
uv run mypy src/driftsentinel tests
uv run pytest -k "tf_env or databricks"
uv run pytest
```

### 6.4 Manual smoke test (post-merge, optional)

On a machine with `tofu` installed and no `DATABRICKS_TF_EXEC_PATH` in
the environment:

```bash
unset DATABRICKS_TF_EXEC_PATH DATABRICKS_TF_VERSION
make bundle-validate CATALOG=<C> PROFILE=<P>     # must succeed
make bundle-deploy   CATALOG=<C> PROFILE=<P>     # must succeed
make app-deploy      CATALOG=<C> PROFILE=<P>     # must succeed
make bootstrap       CATALOG=<C> PROFILE=<P> \   # must succeed
  DATASET_ID=<D> DRIFT_POLICY=<path>
```

On a machine with neither binary installed:

```bash
which tofu terraform     # both must be absent
unset DATABRICKS_TF_EXEC_PATH
make bundle-validate CATALOG=<C> PROFILE=<P>
# must exit non-zero with the §4.4 actionable message and not invoke
# 'databricks bundle validate'.
```

This is operator-side verification, captured in `report/` under the
existing append-only convention if performed.

## 7. Acceptance Criteria

- [ ] `Makefile` targets `bundle-validate`, `bundle-deploy`,
   `app-deploy`, and `bootstrap` source `scripts/databricks_tf_env.sh`
   before invoking any `databricks` or `driftsentinel` command.
- [ ] `bundle-deploy` exists as a Make target (it is added by this
   patch; the issue assumes its presence).
- [ ] When `DATABRICKS_TF_EXEC_PATH` is unset and `tofu` is on PATH,
   the affected targets export
   `DATABRICKS_TF_EXEC_PATH=$(command -v tofu)` and
   `DATABRICKS_TF_VERSION=1.11.6` (the latter only when unset).
- [ ] When `DATABRICKS_TF_EXEC_PATH` is unset and only `terraform` is
   on PATH, the affected targets export
   `DATABRICKS_TF_EXEC_PATH=$(command -v terraform)` and do not set
   `DATABRICKS_TF_VERSION`.
- [ ] When neither `tofu` nor `terraform` is available and
   `DATABRICKS_TF_EXEC_PATH` is unset, the affected targets fail
   non-zero with a single actionable message recommending
   `brew install opentofu`, before any `databricks` command runs.
- [ ] Operator-set `DATABRICKS_TF_EXEC_PATH` is never overridden.
- [ ] `src/driftsentinel/databricks/bundle.py` propagates the resolved
   env to every `subprocess.run` call (verified by unit test).
- [ ] `scripts/deploy_databricks_app.py` propagates the resolved env to
   every `subprocess.run` call.
- [ ] `docs/deployment_guide.md` adds a "Terraform binary" subsection
   covering the upstream cause, the auto-fix, and the manual override.
- [ ] `README.md` quickstart names OpenTofu as a Databricks-deploy
   prerequisite (one bullet, links to the deployment guide section).
- [ ] `make help` (or equivalent comment block) names OpenTofu as a
   recommended prerequisite alongside `make sync`.
- [ ] Unit tests cover all seven branches in §6.1 and the env
   propagation contract in §6.2.
- [ ] `make lint`, `make typecheck`, `make test` all pass.
- [ ] `specs/DS-TM-001_Traceability_Matrix.md` and `specs/README.md`
   are updated per §5.

## 8. Residual Risks

- **OpenTofu version drift.** The `1.11.6` default may lag the
  current OpenTofu release line. Mitigation: operators can override
  `DATABRICKS_TF_VERSION`. The default is documented in the spec and
  the Python helper module-level constant
  (`OPENTOFU_VERSION_DEFAULT`); future bumps are a one-line change.
- **Operator confusion with mixed PATH state.** A user with both
  `tofu` and `terraform` installed gets `tofu` (per §4.1(2)). This
  is the documented preference. Mitigation: documented in
  `docs/deployment_guide.md`.
- **Upstream Databricks CLI fix.** If Databricks ships a CLI release
  with a refreshed PGP key or a different terraform version, this
  shim becomes redundant but harmless — the operator override
  precedence guarantees the helper never overrides a user choice, and
  setting `DATABRICKS_TF_EXEC_PATH` to a working binary remains
  compatible. No removal is required when upstream is fixed; the shim
  can stay.
- **CI parity.** This patch does not exercise `databricks bundle …`
  in CI (CI lacks Databricks credentials). The unit tests guard the
  resolution contract; manual smoke per §6.4 covers the integration.

## 9. Traceability

- DS-PRD: §Deployment Assets, §Operator-Friendly Bundle.
- DS-SRS: DS-FR-002 (deployable Databricks bundle), DS-SR-009 (bundle
  resource resolution).
- DS-SDD-001: §Application Layer (`scripts/`,
  `src/driftsentinel/databricks/`), §Bundle Operations.
- DS-TP-001: §CLI tests, §Databricks integration tests, §Packaging
  tests.
- Issue #35 acceptance criteria mapped 1:1 to §7 above.
