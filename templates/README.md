# templates

YAML policy and contract templates for dataset configuration.

| File | Purpose |
| --- | --- |
| `dataset_contract.yml` | Schema and quality contract for a registered dataset, including source format, file path or table reference, and optional `read_options` |
| `drift_policy.yml` | Drift detection thresholds, monitored columns, and explicit trusted baseline path or table reference |
| `benchmark_policy.yml` | Benchmark scenarios and pass/fail criteria applied to a trusted reference sample |

Users copy and customize these templates for their own datasets. File-backed
datasets declare `landing_path` or `baseline.path`; table-backed datasets use
`table_name` or `baseline.table_name`.
