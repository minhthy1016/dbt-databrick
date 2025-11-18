# Databricks notebook source
# MAGIC %md
# MAGIC # INCREMENTAL DATA INGESTION 

# COMMAND ----------

# MAGIC %sql 
# MAGIC --CREATE VOLUME workspace.raw.gold

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step: Fetch Binance Klines and Save as Delta Table
# MAGIC
# MAGIC 1. **Loop through all destination currencies** (from transactions).
# MAGIC 2. **Skip USD/USDT** since no conversion needed.
# MAGIC 3. **Construct symbol** for Binance API: `CURUSDT`.
# MAGIC 4. **Fetch historical klines** (OHLCV data) from Binance:
# MAGIC    - Use hourly interval (`1h`).
# MAGIC    - Handle pagination (max 1000 rows per request).
# MAGIC    - Retry on errors or rate limits.
# MAGIC 5. **Convert raw JSON to Pandas DataFrame**:
# MAGIC    - Set correct column names.
# MAGIC    - Convert timestamps to UTC datetime.
# MAGIC    - Convert numeric columns to proper types.
# MAGIC 6. **Save per-symbol CSV** for inspection.
# MAGIC 7. **Combine all symbols** into a single Pandas DataFrame.
# MAGIC 8. **Convert to Spark DataFrame** and write as **Delta table** to `OUTPUT_DIR`.
# MAGIC

# COMMAND ----------

# ingest_rates.py
import os
import time
import math
import requests
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path

# ---------- CONFIG ----------
TRANSACTIONS_PATH = "/Volumes/workspace/raw/rawvolume/rawdata/transactions/transactions.csv"
USERS_PATH = "/Volumes/workspace/raw/rawvolume/rawdata/users/users.csv"

OUTPUT_DIR = "/Volumes/workspace/raw/rawvolume/rawdata/raw_rates/output"
TABLE_NAME = "workspace.raw.combine_raw_rates"
#OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# BINANCE API (Mirror endpoint, NOT region locked)
BINANCE_BASE = "https://data-api.binance.vision"
KLINES_ENDPOINT = "/api/v3/klines"

INTERVAL = "1h"
REQUEST_LIMIT = 1000
SLEEP_BETWEEN_REQUESTS = 0.5
MAX_RETRIES = 5
# ----------------------------


def read_transactions(path):
    return pd.read_csv(path, parse_dates=["created_at"])


def get_destination_currencies(df):
    return sorted(df["destination_currency"].dropna().unique().tolist())


def get_time_range(df):
    start = df["created_at"].min()
    end = df["created_at"].max()

    start = pd.to_datetime(start).tz_localize(None).replace(minute=0, second=0, microsecond=0)
    end = pd.to_datetime(end).tz_localize(None)
    if end.minute != 0 or end.second != 0 or end.microsecond != 0:
        end = (end + pd.Timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)

    start_ms = int(start.replace(tzinfo=timezone.utc).timestamp() * 1000)
    end_ms = int(end.replace(tzinfo=timezone.utc).timestamp() * 1000)

    return start_ms, end_ms, start, end


def call_binance_klines(symbol, interval, start_time_ms, end_time_ms, limit=REQUEST_LIMIT):
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time_ms,
        "endTime": end_time_ms,
        "limit": limit
    }
    url = BINANCE_BASE + KLINES_ENDPOINT

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = requests.get(url, params=params, timeout=20)
            if r.status_code == 200:
                return r.json()
            elif r.status_code == 429:
                wait = 2 ** attempt
                print(f"[{symbol}] Rate limit, sleeping {wait}s")
                time.sleep(wait)
            else:
                print(f"[{symbol}] HTTP {r.status_code}: {r.text}")
                time.sleep(1)
        except Exception as e:
            print(f"[{symbol}] Error {e}, retrying...")
            time.sleep(2 ** attempt)

    raise RuntimeError(f"Failed to fetch {symbol} klines after retries")


def fetch_symbol_full(symbol, interval, start_ms, end_ms):
    all_rows = []
    cur_start = start_ms

    interval_ms = 60 * 60 * 1000  # 1 hour

    while cur_start < end_ms:
        raw = call_binance_klines(symbol, interval, cur_start, end_ms)
        if not raw:
            break

        all_rows.extend(raw)

        last_open = raw[-1][0]
        next_start = last_open + interval_ms
        if next_start <= cur_start:
            break

        cur_start = next_start
        time.sleep(SLEEP_BETWEEN_REQUESTS)

    if not all_rows:
        return pd.DataFrame()

    df = pd.DataFrame(all_rows, columns=[
        "open_time","open","high","low","close","volume",
        "close_time","quote_asset_volume","num_trades",
        "taker_buy_base","taker_buy_quote","ignore"
    ])

    df["symbol"] = symbol
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms", utc=True)

    numeric_cols = ["open","high","low","close","volume","quote_asset_volume",
                    "taker_buy_base","taker_buy_quote"]
    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df["num_trades"] = pd.to_numeric(df["num_trades"], errors="coerce").astype("Int64")
    # Reorder columns so symbol comes first
    df = df[["symbol"] + [c for c in df.columns if c != "symbol"]]

    return df


def main():
    print("Reading transactions...")
    tx = read_transactions(TRANSACTIONS_PATH)

    dest_currencies = get_destination_currencies(tx)
    start_ms, end_ms, start_dt, end_dt = get_time_range(tx)

    print(f"Dest currencies: {dest_currencies}")
    print(f"Time range: {start_dt} -> {end_dt}")

    all_results = []

    for cur in dest_currencies:
        cur = str(cur).strip().upper()

        if cur in ("USD", "USDT"):
            print(f"Skipping {cur}")
            continue

        symbol = f"{cur}USDT"
        print(f"Fetching {symbol} ...")

        try:
            df = fetch_symbol_full(symbol, INTERVAL, start_ms, end_ms)
            if df.empty:
                print(f"{symbol}: no data, skipping")
                continue

            out_path = OUTPUT_DIR / f"{symbol}.csv"
            df.to_csv(out_path, index=False)
            print(f"{symbol}: wrote {len(df)} rows → {out_path}")

            all_results.append(df)

        except Exception as e:
            print(f"ERROR {symbol}: {e}")

    if all_results:
        combined = pd.concat(all_results, ignore_index=True)
        spark_df = spark.createDataFrame(combined)

        # Save to Delta folder (first time)
        spark_df.write.format("delta").mode("overwrite").save(OUTPUT_DIR)

        # Register table in the metastore using the correct three-level namespace
        spark.sql(f"DROP TABLE IF EXISTS {TABLE_NAME}")
        spark.sql(f"CREATE TABLE IF NOT EXISTS {TABLE_NAME} USING DELTA")

        print(f"Delta table registered")


if __name__ == "__main__":
    main()


# COMMAND ----------

import pandas as pd
import glob

# ---- CONFIG ----
VOLUME_BASE = "/Volumes/workspace/raw/rawvolume/rawdata/raw_rates"
CSV_FOLDER = f"{VOLUME_BASE}/raw_rates/*.csv"
OUTPUT_DIR = f"{VOLUME_BASE}/output"
TABLE_NAME = "workspace.raw.combine_raw_rates"

# ---- LOAD CSVs USING GLOB (Python local) ----
files = glob.glob(CSV_FOLDER)

if not files:
    raise ValueError(f"No CSV files found in {CSV_FOLDER}")

dfs = [pd.read_csv(f) for f in files]

combined = pd.concat(dfs, ignore_index=True)

# ---- CONVERT TO SPARK DF ----
spark_df = spark.createDataFrame(combined)

# ---- WRITE DELTA TO VOLUME ----
spark_df.write.format("delta").mode("overwrite").save(OUTPUT_DIR)

# ---- REGISTER UC TABLE ----
spark.sql(f"DROP TABLE IF EXISTS {TABLE_NAME}")

spark.sql(f"""
    CREATE TABLE {TABLE_NAME}
    USING DELTA
    
""")

print(f"Delta table created at: {TABLE_NAME}")


# COMMAND ----------

# MAGIC %sql
# MAGIC select * from workspace.raw.combine_raw_rates limit 10
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC In workspace.bronze : 
# MAGIC
# MAGIC 9. Create volumes workspace.bronze.bronzevolume 
# MAGIC 10. Create table raw_users, raw_transactions, raw_rates 
# MAGIC
# MAGIC In raw schema: 
# MAGIC
# MAGIC 11. Create table combine_raw_rates, raw_users, raw_transactions

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE VOLUME IF NOT EXISTS workspace.bronze.bronzevolume

# COMMAND ----------

# Create bronze raw_users directory 
user_df = (
    spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "csv")
        .option("cloudFiles.schemaLocation", "/Volumes/workspace/bronze/bronzevolume/raw_users/checkpoint")
        .option("cloudFiles.schemaEvolutionMode", "rescue")
        .load("/Volumes/workspace/raw/rawvolume/rawdata/users/")   
)

(
    user_df.writeStream
        .format("delta")
        .outputMode("append")
        .trigger(once=True)
        .option("checkpointLocation", "/Volumes/workspace/bronze/bronzevolume/raw_users/checkpoint")
        .option("path", "/Volumes/workspace/bronze/bronzevolume/raw_users/data")
        .start()
)


# COMMAND ----------

# Create bronze raw_transactions directory 
transactions_df = (
    spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "csv")
        .option("cloudFiles.schemaLocation", "/Volumes/workspace/bronze/bronzevolume/raw_transactions/checkpoint")
        .option("cloudFiles.schemaEvolutionMode", "rescue")
        .load("/Volumes/workspace/raw/rawvolume/rawdata/transactions/")   
)

(
    transactions_df.writeStream
        .format("delta")
        .outputMode("append")
        .trigger(once=True)
        .option("checkpointLocation", "/Volumes/workspace/bronze/bronzevolume/raw_transactions/checkpoint")
        .option("path", "/Volumes/workspace/bronze/bronzevolume/raw_transactions/data")
        .start()
)


# COMMAND ----------

# MAGIC %sql 
# MAGIC -- Check data from delta directory 
# MAGIC SELECT * from delta.`/Volumes/workspace/bronze/bronzevolume/raw_users/data/`

# COMMAND ----------

# MAGIC %sql 
# MAGIC SELECT * from delta.`/Volumes/workspace/bronze/bronzevolume/raw_transactions/data/`

# COMMAND ----------

# Read from Delta table instead of cloudFiles
rawrates_df = (
    spark.readStream.format("delta")
        .load("/Volumes/workspace/raw/rawvolume/rawdata/raw_rates/ouput/")
)

(
    rawrates_df.writeStream
        .format("delta")
        .outputMode("append")
        .trigger(once=True)
        .option("checkpointLocation", "/Volumes/workspace/bronze/bronzevolume/raw_rates/checkpoint")
        .option("path", "/Volumes/workspace/bronze/bronzevolume/raw_rates/data")
        .start()
)

# COMMAND ----------

# MAGIC %sql 
# MAGIC SELECT * from delta.`/Volumes/workspace/bronze/bronzevolume/raw_rates/data`

# COMMAND ----------

# Create raw_users table 
user_df = spark.read.format("csv") \
    .option("header", "true") \
    .option("inferSchema", "true") \
    .load("/Volumes/workspace/raw/rawvolume/rawdata/users/users.csv")

user_df.write.format("delta") \
    .mode("overwrite") \
    .saveAsTable("workspace.raw.raw_users")



# COMMAND ----------

# Create raw_transactions table 
trans_df = spark.read.format("csv") \
    .option("header", "true") \
    .option("inferSchema", "true") \
    .load("/Volumes/workspace/raw/rawvolume/rawdata/transactions/transactions.csv")

trans_df.write.format("delta") \
    .mode("overwrite") \
    .saveAsTable("workspace.raw.raw_transactions")

# COMMAND ----------

# MAGIC %sql 
# MAGIC select * from workspace.raw.raw_users limit 10

# COMMAND ----------

# MAGIC %md
# MAGIC # Verify the tables exist in Databricks

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Check schema
# MAGIC SHOW TABLES IN bronze;
# MAGIC
# MAGIC -- Check table exists
# MAGIC SELECT * FROM delta.`/Volumes/workspace/bronze/bronzevolume/raw_users/data/` LIMIT 5;
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC