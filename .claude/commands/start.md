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

5. Verify catalog access and validate the Databricks bundle when Databricks
   authentication is configured and you have a real Unity Catalog catalog:
   ```
   make bundle-catalog-check CATALOG=<existing_uc_catalog> PROFILE=<profile>
   make bundle-validate CATALOG=<existing_uc_catalog> PROFILE=<profile>
   ```

   `bundle validate` alone does not prove catalog existence or deployment
   success.

## Report

Return the results of each step. Flag any failures and recommend corrective
action before proceeding with work.
