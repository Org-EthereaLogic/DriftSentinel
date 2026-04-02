# evidence

Append-only evidence artifact writing for auditability.

Responsibilities:
- Writing timestamped evidence records from control runs
- Tagging evidence with dataset identity, run ID, run kind, and version metadata
- Providing evidence lookup by run ID, dataset, and date range
- Quarantining malformed artifacts during lookup instead of crashing queries

Key exports: `write_evidence`, `write_benchmark_bundle`, `build_provenance_envelope`,
`list_evidence`, `load_evidence`, `generate_run_id`.

Key file: `writer.py`.
