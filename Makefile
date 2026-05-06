UV ?= uv
DATABRICKS ?= databricks
PROFILE_ARG := $(if $(PROFILE),-p $(PROFILE),)

# Source scripts/databricks_tf_env.sh before any 'databricks bundle ...' or
# 'driftsentinel databricks ...' invocation so the upstream terraform 1.5.5
# PGP-expired download path is bypassed via OpenTofu (or operator override).
# See specs/DS-PATCH-035_opentofu_auto_detection.md.
TF_ENV := . scripts/databricks_tf_env.sh

.PHONY: help sync hooks-install lint typecheck test coverage \
	bundle-catalog-check bundle-validate bundle-deploy app-deploy bootstrap \
	demo-nyc-taxi

help:
	@echo "DriftSentinel — Make targets"
	@echo ""
	@echo "Prerequisites:"
	@echo "  Databricks bundle/app targets require OpenTofu (recommended) or terraform"
	@echo "  on PATH. Install with: brew install opentofu"
	@echo "  See specs/DS-PATCH-035_opentofu_auto_detection.md for context."
	@echo ""
	@echo "Targets:"
	@echo "  sync                   Install runtime + dev dependencies (uv sync)"
	@echo "  hooks-install          Install pre-commit hooks (depends on sync)"
	@echo "  lint                   ruff check ."
	@echo "  typecheck              mypy src/driftsentinel tests"
	@echo "  test                   pytest"
	@echo "  coverage               pytest with coverage reporting"
	@echo "  bundle-catalog-check   Verify Unity Catalog catalog exists (CATALOG=, [PROFILE=])"
	@echo "  bundle-validate        databricks bundle validate (CATALOG=, [PROFILE=])"
	@echo "  bundle-deploy          databricks bundle deploy (CATALOG=, [PROFILE=])"
	@echo "  app-deploy             Deploy DriftSentinel App (CATALOG=, [PROFILE=])"
	@echo "  bootstrap              Dataset-backed Databricks connect flow"
	@echo "                         (DATASET_ID=, DRIFT_POLICY=, CATALOG=, [...])"
	@echo "  demo-nyc-taxi          One-shot NYC TLC Yellow Taxi demo replay"
	@echo "                         (CATALOG=, [PROFILE=])"

sync:
	$(UV) sync --all-groups

hooks-install: sync
	$(UV) run pre-commit install

lint:
	$(UV) run ruff check .

typecheck:
	$(UV) run mypy src/driftsentinel tests

test:
	$(UV) run pytest

coverage:
	$(UV) run pytest --cov=src/driftsentinel --cov-branch --cov-report=term-missing --cov-report=xml

bundle-catalog-check:
	$(DATABRICKS) catalogs get "$${CATALOG:?Set CATALOG}" $(PROFILE_ARG) -o json

bundle-validate:
	@$(TF_ENV) && $(DATABRICKS) bundle validate $(PROFILE_ARG) --target dev --var="catalog=$${BUNDLE_VAR_catalog:-$${CATALOG:?Set CATALOG or BUNDLE_VAR_catalog}}"

bundle-deploy:
	@$(TF_ENV) && $(DATABRICKS) bundle deploy $(PROFILE_ARG) --target dev --var="catalog=$${BUNDLE_VAR_catalog:-$${CATALOG:?Set CATALOG or BUNDLE_VAR_catalog}}"

app-deploy:
	@$(TF_ENV) && $(UV) run python scripts/deploy_databricks_app.py $(if $(PROFILE),--profile $(PROFILE),) --target dev --catalog "$${BUNDLE_VAR_catalog:-$${CATALOG:?Set CATALOG or BUNDLE_VAR_catalog}}"

demo-nyc-taxi:
	@scripts/run_nyc_taxi_demo.sh \
		--catalog "$${BUNDLE_VAR_catalog:-$${CATALOG:?Set CATALOG or BUNDLE_VAR_catalog}}" \
		$(if $(PROFILE),--profile $(PROFILE),)

bootstrap:
	@test -n "$(DATASET_ID)" || (echo "Set DATASET_ID=<registered_dataset>" >&2; exit 2)
	@test -n "$(DRIFT_POLICY)" || (echo "Set DRIFT_POLICY=<local_drift_policy.yml>" >&2; exit 2)
	@$(TF_ENV) && $(UV) run driftsentinel databricks connect \
		--catalog "$${BUNDLE_VAR_catalog:-$${CATALOG:?Set CATALOG or BUNDLE_VAR_catalog}}" \
		$(if $(PROFILE),--profile $(PROFILE),) \
		--dataset-id "$(DATASET_ID)" \
		$(if $(REGISTRY),--registry "$(REGISTRY)",) \
		--drift-policy "$(DRIFT_POLICY)" \
		$(if $(BENCHMARK_POLICY),--benchmark-policy "$(BENCHMARK_POLICY)",) \
		$(if $(LANDING_PATH),--landing-path "$(LANDING_PATH)",) \
		$(if $(BASELINE_PATH),--baseline-path "$(BASELINE_PATH)",) \
		--wait
