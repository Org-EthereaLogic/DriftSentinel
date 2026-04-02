# start

Set up the local development environment and verify the project is functional.

## Steps

1. Install dependencies:
   ```
   uv sync --all-groups
   ```

2. Run the placeholder scan:
   ```
   PATTERN='TO''DO|FIX''ME|TB''D|PLACE''HOLDER'; rg -n "$PATTERN" specs .claude CLAUDE.md docs
   ```

3. Run lint:
   ```
   uv run ruff check .
   ```

4. Run the full test suite:
   ```
   uv run pytest
   ```

5. Validate the Databricks bundle (if configured):
   ```
   databricks bundle validate
   ```

## Report

Return the results of each step. Flag any failures and recommend corrective
action before proceeding with work.
