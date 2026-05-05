# scripts

Operational helper scripts for DriftSentinel.

- `deploy_databricks_app.py` performs the repo-supported Databricks App deploy
  sequence: bundle deploy, app start, app source deploy, and final status
  verification.
- `databricks_tf_env.sh` is a sourceable POSIX shell helper that exports
  `DATABRICKS_TF_EXEC_PATH` (and `DATABRICKS_TF_VERSION` when unset) so
  `databricks bundle …` bypasses the upstream terraform 1.5.5 PGP-expired
  download path. Operator-set values are honored verbatim; otherwise the
  helper prefers `tofu` over `terraform` and fails closed when neither is
  available with an actionable `brew install opentofu` recommendation. The
  Makefile sources this helper before every bundle/app/bootstrap target;
  the Python parity lives in `src/driftsentinel/databricks/tf_env.py`. See
  `specs/DS-PATCH-035_opentofu_auto_detection.md`.
