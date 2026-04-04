# Databricks notebook source
# MAGIC %md
# MAGIC # DriftSentinel — Register Dataset
# MAGIC
# MAGIC Register a new dataset for DriftSentinel monitoring by loading a dataset
# MAGIC contract from `templates/dataset_contract.yml` or providing inline config.
# MAGIC Persists the registration to a local JSON registry.

# COMMAND ----------

# Resolve the bundle workspace root when this notebook is deployed through
# Databricks Asset Bundles, then fall back to GitHub for manual imports.
from pathlib import Path
import subprocess
import sys


def _resolve_install_target() -> str:
    try:
        notebook_path = (
            dbutils.notebook.entry_point.getDbutils()
            .notebook()
            .getContext()
            .notebookPath()
            .get()
        )
        workspace_path = Path("/Workspace") / notebook_path.lstrip("/")
        for parent in workspace_path.parents:
            if (parent / "pyproject.toml").exists() and (parent / "src" / "driftsentinel").exists():
                return str(parent)
    except Exception:
        pass
    return "git+https://github.com/Org-EthereaLogic/DriftSentinel.git"


install_target = _resolve_install_target()
if install_target.startswith("/Workspace/"):
    source_root = str(Path(install_target) / "src")
    if source_root not in sys.path:
        sys.path.insert(0, source_root)
    print(f"Using DriftSentinel from workspace source tree: {source_root}")
else:
    print(f"Installing DriftSentinel from: {install_target}")
    subprocess.check_call([sys.executable, "-m", "pip", "install", install_target])
    dbutils.library.restartPython()

# COMMAND ----------

# Installation is handled in the previous cell so serverless runs do not rely on writing a temp file.

# COMMAND ----------

dbutils.widgets.text("catalog", "", "Unity Catalog name")
dbutils.widgets.text("schema", "default", "Schema name")
dbutils.widgets.text("contract_path", "", "Optional workspace path to dataset contract YAML")
dbutils.widgets.text("registry_path", "/tmp/driftsentinel_registry.json", "Path to dataset registry JSON")

# COMMAND ----------

catalog = dbutils.widgets.get("catalog").strip()
schema = dbutils.widgets.get("schema").strip()
contract_path = dbutils.widgets.get("contract_path").strip()
registry_path = dbutils.widgets.get("registry_path").strip()
if not catalog:
    raise ValueError("Set the catalog widget to an existing Unity Catalog catalog before running this notebook.")
if not schema:
    raise ValueError("Set the schema widget to an existing schema before running this notebook.")
print(f"Target: {catalog}.{schema}")

# COMMAND ----------

import os


def _configure_trusted_roots(*raw_paths: str) -> None:
    roots = {"/Workspace", "/Volumes", "/dbfs"}
    for raw in raw_paths:
        raw = str(raw or "").strip()
        if not raw:
            continue
        candidate = Path(raw.replace("dbfs:/", "/dbfs/", 1)).expanduser()
        if candidate.is_absolute():
            roots.add(str(candidate.parent if candidate.suffix else candidate))
    existing = {
        item for item in os.environ.get("DRIFTSENTINEL_ALLOWED_PATH_ROOTS", "").split(os.pathsep) if item
    }
    os.environ["DRIFTSENTINEL_ALLOWED_PATH_ROOTS"] = os.pathsep.join(sorted(existing | roots))


os.environ["REGISTRY_PATH"] = registry_path
_configure_trusted_roots(contract_path, registry_path)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load and Validate a Dataset Contract Template

# COMMAND ----------

import json
from pathlib import Path as _Path
from driftsentinel.config.loader import (
    DatasetRegistry,
    RegistryError,
    load_dataset_contract,
    load_packaged_dataset_contract,
)

if contract_path:
    contract = load_dataset_contract(contract_path)
    contract_source = contract_path
else:
    contract = load_packaged_dataset_contract()
    contract["dataset"]["catalog"] = catalog
    contract["dataset"]["schema"] = schema
    contract_source = "bundled package template"

print(f"Dataset contract loaded successfully from {contract_source}.")
print(json.dumps(contract, indent=2))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Register Dataset

# COMMAND ----------

if _Path(registry_path).is_file():
    registry = DatasetRegistry.load(registry_path)
    print(f"Loaded existing registry from {registry_path}")
else:
    registry = DatasetRegistry()
    print("Created new dataset registry")

try:
    dataset_id, contract_version = registry.register(contract)
    registry.save(registry_path)
    print(f"Registered: {dataset_id} v{contract_version}")
except RegistryError as exc:
    print(f"Registration blocked: {exc}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Registry Summary

# COMMAND ----------

datasets = registry.list_datasets()
print(f"Registered datasets: {len(datasets)}")
for ds in datasets:
    print(f"  {ds['dataset_id']} v{ds['contract_version']}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Contract Summary

# COMMAND ----------

ds = contract["dataset"]
ct = contract["contract"]
print(f"Dataset:          {ds['name']}")
print(f"Catalog:          {ds.get('catalog', catalog)}")
print(f"Schema:           {ds.get('schema', schema)}")
print(f"Version:          {ds.get('contract_version', 'unversioned')}")
print(f"Required columns: {len(ct['required_columns'])}")
print(f"Business key:     {ct['business_key']}")
print(f"Batch identifier: {ct['batch_identifier']}")
