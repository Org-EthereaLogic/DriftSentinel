# config

Dataset contract, drift policy, and benchmark policy configuration.

Responsibilities:
- Loading and validating YAML policy files from `templates/`
- Loading read-only packaged template copies for GitHub-installed notebook runs
- Providing typed configuration objects to other modules
- Supporting per-dataset policy overrides

Implemented in DS-IP-001 Phase 1. Key file: `loader.py`.
