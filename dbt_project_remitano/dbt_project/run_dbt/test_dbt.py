# Databricks notebook source
# MAGIC %pip install dbt-core dbt-databricks

# COMMAND ----------

# MAGIC %restart_python

# COMMAND ----------

# MAGIC %sh
# MAGIC dbt --version

# COMMAND ----------

# MAGIC
# MAGIC %sh
# MAGIC dbt debug --profiles-dir .
# MAGIC

# COMMAND ----------

# MAGIC %sh
# MAGIC dbt run --models stg_users --profiles-dir ~/.dbt

# COMMAND ----------

# MAGIC %sh
# MAGIC mkdir -p /Workspace/Users/minhthy1016@gmail.com/.dbt

# COMMAND ----------

# MAGIC %sh
# MAGIC cat <<EOT > /Workspace/Users/minhthy1016@gmail.com/.dbt/profiles.yml
# MAGIC databricks_dwh:
# MAGIC   target: dev
# MAGIC   outputs:
# MAGIC     dev:
# MAGIC       type: databricks
# MAGIC       catalog: workspace
# MAGIC       schema: bronze
# MAGIC       host: dbc-48f6dc09-1a50.cloud.databricks.com
# MAGIC       http_path: /sql/1.0/warehouses/032b36f9186aab40
# MAGIC       token: dapi471feb6e682b1e73a224c9920d1503b2
# MAGIC       threads: 4
# MAGIC       connect_retries: 1
# MAGIC EOT
# MAGIC

# COMMAND ----------

# MAGIC %sh
# MAGIC ls -l /Workspace/Users/minhthy1016@gmail.com/.dbt
# MAGIC

# COMMAND ----------

# MAGIC %sh
# MAGIC rm -f /Workspace/Users/minhthy1016@gmail.com/.dbt/profiles.yml
# MAGIC

# COMMAND ----------

# MAGIC %sh
# MAGIC cat /Workspace/Users/minhthy1016@gmail.com/.dbt/profiles.yml
# MAGIC

# COMMAND ----------

# MAGIC %sh 
# MAGIC dbt debug --profiles-dir /Workspace/Users/minhthy1016@gmail.com/.dbt
# MAGIC

# COMMAND ----------

import os
os.environ["DBT_PROFILES_DIR"] = "/Workspace/Users/minhthy1016@gmail.com/.dbt"


# COMMAND ----------

# MAGIC %sh
# MAGIC
# MAGIC dbt run --profiles-dir /Workspace/Users/minhthy1016@gmail.com/.dbt
# MAGIC

# COMMAND ----------

# MAGIC %sh 
# MAGIC dbt run
# MAGIC dbt snapshot
# MAGIC dbt test
# MAGIC