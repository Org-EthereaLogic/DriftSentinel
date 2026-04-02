UV ?= uv
DATABRICKS ?= databricks
PROFILE_ARG := $(if $(PROFILE),-p $(PROFILE),)

.PHONY: sync lint typecheck test coverage bundle-catalog-check bundle-validate app-deploy

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
