# templates

YAML policy and contract templates for dataset configuration.

| File | Purpose |
| --- | --- |
| `dataset_contract.yml` | Schema and quality contract for a registered dataset, including source landing path |
| `drift_policy.yml` | Drift detection thresholds, monitored columns, and explicit trusted baseline path |
| `benchmark_policy.yml` | Benchmark scenarios and pass/fail criteria applied to a trusted reference sample |

Users copy and customize these templates for their own datasets.
