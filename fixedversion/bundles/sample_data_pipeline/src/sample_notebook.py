# Databricks notebook source
# COMMAND ----------
# Placeholder ETL — replace with real pipeline logic.
# Catalog/schema come from job base_parameters when run as a job task.

# COMMAND ----------
dbutils.widgets.text("catalog", "sample_dev")
dbutils.widgets.text("schema", "etl")
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")

# COMMAND ----------
print(f"sample_data_pipeline target: {catalog}.{schema}")
# Example (uncomment when tables exist):
# spark.sql(f"USE CATALOG {catalog}")
# spark.sql(f"USE SCHEMA {schema}")
# spark.table(f"{catalog}.{schema}.example").limit(10).show()
