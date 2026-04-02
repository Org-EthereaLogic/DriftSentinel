# Databricks notebook source
# MAGIC %md
# MAGIC # DriftSentinel — Run Control Benchmark
# MAGIC
# MAGIC Run control effectiveness benchmarking against known failure scenarios
# MAGIC and write scored evidence bundles.

# COMMAND ----------

# MAGIC %pip install git+https://github.com/Org-EthereaLogic/DriftSentinel.git
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

dbutils.widgets.text("seed", "42", "Random seed for reproducibility")
dbutils.widgets.text("n_rows", "1000", "Number of synthetic rows")
dbutils.widgets.text("catalog", "driftsentinel", "Unity Catalog name")
dbutils.widgets.text("schema", "default", "Schema name")

# COMMAND ----------

seed = int(dbutils.widgets.get("seed"))
n_rows = int(dbutils.widgets.get("n_rows"))
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
print(f"Benchmark config: seed={seed}, n_rows={n_rows}, target={catalog}.{schema}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Run Benchmark

# COMMAND ----------

from driftsentinel.benchmark.orchestrator import run_benchmark

result = run_benchmark(seed=seed, n_rows=n_rows)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Measured Metrics

# COMMAND ----------

print("Measured metrics:")
for name, value in result["measured"].items():
    print(f"  {name}: {value}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gate Results

# COMMAND ----------

for gr in result["gate_results"]:
    print(f"  {gr.config.name}: threshold={gr.config.threshold}, "
          f"measured={gr.measured_value:.4f}, verdict={gr.verdict.value}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Overall Verdict

# COMMAND ----------

print(f"Overall verdict: {result['overall_verdict'].value}")
