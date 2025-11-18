# Databricks notebook source
# MAGIC %md
# MAGIC 0. From workspace Catalog, create raw, bronze, silver, gold schemas
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC 1. From "raw" schema, create rawvolume where we will upload raw data by volume
# MAGIC 2. Create volume folder "rawdata" 
# MAGIC 3. In "rawdata" folder, create raw_rates, transactions, users folders 
# MAGIC 4. Upload transactions.csv and users.csv to transactions folder and users folder. 

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE VOLUME IF NOT EXISTS workspace.raw.rawvolume

# COMMAND ----------

#dbutils.fs.mkdirs("/Volumes/workspace/raw/rawvolume/rawdata")
#dbutils.fs.mkdirs("/Volumes/workspace/raw/rawvolume/rawdata/transactions")

dbutils.fs.mkdirs("/Volumes/workspace/raw/rawvolume/rawdata/users")

# COMMAND ----------

dbutils.fs.mkdirs("/Volumes/workspace/raw/rawvolume/rawdata/raw_rates")