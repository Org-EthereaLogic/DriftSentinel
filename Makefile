UV ?= uv
DATABRICKS ?= databricks
PROFILE_ARG := $(if $(PROFILE),-p $(PROFILE),)

.PHONY: sync lint typecheck test coverage bundle-catalog-check bundle-validate app-deploy bootstrap

sync:
	$(UV) sync --all-groups

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
	$(DATABRICKS) bundle validate $(PROFILE_ARG) --target dev --var="catalog=$${BUNDLE_VAR_catalog:-$${CATALOG:?Set CATALOG or BUNDLE_VAR_catalog}}"

app-deploy:
	$(UV) run python scripts/deploy_databricks_app.py $(if $(PROFILE),--profile $(PROFILE),) --target dev --catalog "$${BUNDLE_VAR_catalog:-$${CATALOG:?Set CATALOG or BUNDLE_VAR_catalog}}"

bootstrap:
	@test -n "$(DATASET_ID)" || (echo "Set DATASET_ID=<registered_dataset>" >&2; exit 2)
	@test -n "$(DRIFT_POLICY)" || (echo "Set DRIFT_POLICY=<local_drift_policy.yml>" >&2; exit 2)
	$(UV) run driftsentinel databricks connect \
		--catalog "$${BUNDLE_VAR_catalog:-$${CATALOG:?Set CATALOG or BUNDLE_VAR_catalog}}" \
		$(if $(PROFILE),--profile $(PROFILE),) \
		--dataset-id "$(DATASET_ID)" \
		$(if $(REGISTRY),--registry "$(REGISTRY)",) \
		--drift-policy "$(DRIFT_POLICY)" \
		$(if $(BENCHMARK_POLICY),--benchmark-policy "$(BENCHMARK_POLICY)",) \
		$(if $(LANDING_PATH),--landing-path "$(LANDING_PATH)",) \
		$(if $(BASELINE_PATH),--baseline-path "$(BASELINE_PATH)",) \
		--wait
