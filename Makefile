UV ?= uv

.PHONY: sync lint typecheck test coverage bundle-validate

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

bundle-validate:
	databricks bundle validate
