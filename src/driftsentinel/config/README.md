# config

Dataset contract, drift policy, and benchmark policy configuration.

Responsibilities:
- Loading and validating YAML policy files from `templates/`
- Loading read-only packaged template copies for GitHub-installed notebook runs
- Providing typed configuration objects to other modules
- Supporting per-dataset policy overrides
- Multi-dataset registry with serialization and collision prevention
- Explicit policy-to-dataset version binding with compatibility checks

Key exports: `DatasetRegistry`, `RegistryError`, `check_policy_compatibility`,
`load_dataset_contract`, `load_drift_policy`, `load_benchmark_policy`,
`normalize_benchmark_gates`.

Key file: `loader.py`.
