# test

Run the DriftSentinel validation suite and return structured results.

## Variables

TEST_COMMAND_TIMEOUT: 5 minutes

## Instructions

- Execute each check in the sequence below
- Capture the result (passed/failed) and any error messages
- Return ONLY the JSON array with test results
- If a check fails, include the error message and stop processing remaining checks

## Test Execution Sequence

### 1. Placeholder Scan
- Command: `PATTERN='TO''DO|FIX''ME|TB''D|PLACE''HOLDER'; rg -n "$PATTERN" specs .claude CLAUDE.md docs`
- test_name: `placeholder_scan`
- test_purpose: "Ensures no forbidden placeholder markers remain in canonical surfaces"

### 2. Lint
- Command: `uv run ruff check .`
- test_name: `ruff_lint`
- test_purpose: "Style and correctness lint using Ruff"

### 3. Type Check
- Command: `uv run mypy src/driftsentinel tests`
- test_name: `mypy_typecheck`
- test_purpose: "Static type verification of product and test code"

### 4. Full Test Suite
- Command: `uv run pytest`
- test_name: `pytest_suite`
- test_purpose: "Runs all pytest tests with coverage enforcement"

### 5. Catalog Check
- Command: `make bundle-catalog-check CATALOG=<existing_uc_catalog> PROFILE=<profile>`
- test_name: `catalog_check`
- test_purpose: "Proves the selected Unity Catalog catalog exists in the target workspace"

### 6. Bundle Validation
- Command: `make bundle-validate CATALOG=<existing_uc_catalog> PROFILE=<profile>`
- test_name: `bundle_validate`
- test_purpose: "Validates the Databricks Asset Bundle configuration after catalog existence is proven"

## Report

Return results exclusively as a JSON array. Sort failed checks first.

```json
[
  {
    "test_name": "string",
    "passed": true,
    "execution_command": "string",
    "test_purpose": "string",
    "error": "optional string"
  }
]
```
