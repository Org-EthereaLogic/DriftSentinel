# pull-request

Create a GitHub pull request for the current branch after verifying all checks pass.

## Variables

target_branch: $ARGUMENTS (default: main)

## Run

1. `git diff origin/main...HEAD --stat`
2. `git log origin/main..HEAD --oneline`
3. Run placeholder scan — must return clean
4. `uv run ruff check .` — must pass
5. `uv run pytest` — must pass
6. `databricks bundle validate` when `databricks.yml` exists
7. Push: `git push -u origin $(git branch --show-current)`
8. Create PR: `gh pr create --title "<title>" --body "<body>" --base <target_branch>`

If any check fails, stop and fix before creating the PR.

## Report

Return ONLY the PR URL that was created.
