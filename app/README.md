# app

Databricks App UI for operator dashboard access.

Four read-only views:
- **Registry View** — browse registered datasets and contract metadata
- **Run Status** — filter and summarize recent control runs by dataset, kind, date
- **Evidence Explorer** — inspect full evidence artifact JSON detail
- **Analytics** — summarize verdict mix, run-kind breakdown, and timeline trends

Built with Gradio. Deployed as a DAB resource via `resources/driftsentinel_app.yml`.
Requires a Premium Databricks workspace. The notebook path remains fully
functional for Free Edition users.

Bundle-backed app deployments use the repository root as the source path so the
local `driftsentinel` package is installed from this repo, not from an external
package index. The `app/requirements.txt` file remains the local development
entry point for running the app directly from this directory.

Key file: `app.py`.
