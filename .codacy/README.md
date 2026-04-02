# Codacy Integration

This directory is reserved for Codacy configuration.

## Setup

1. Enable the DriftSentinel repository in the Codacy dashboard.
2. Add `CODACY_PROJECT_TOKEN` as a GitHub Actions repository secret.
3. Codacy analysis runs automatically on push and pull request events.

## Repository Secret Names

| Secret | Purpose |
| --- | --- |
| `CODACY_PROJECT_TOKEN` | Codacy project-level API token |
| `CODECOV_PROJECT_TOKEN` | Codecov upload token |
| `SNYK_PROJECT_TOKEN` | Snyk CLI authentication token |
