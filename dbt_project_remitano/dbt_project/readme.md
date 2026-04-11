# README

## Project Overview

This project builds a **Bronze → Silver → Gold ETL pipeline** on **Databricks Delta Lake** using **dbt**.

**Purpose:**

* Provide a **Single Source of Truth** for crypto transaction data.
* Enable analytics on:

  * Daily / monthly / quarterly transaction volumes in USD
  * Completed transactions per user KYC level
  * Historical KYC levels at the time of each transaction

**Data Flow:**

```
Bronze (raw tables) --> Silver (enriched/intermediate) --> Gold (fact/aggregates)
```

---

## Folder Structure

```
dbt_project/
├── models/
│   ├── staging/       # Bronze → cleaning, type casting, renaming
│   ├── int/           # Silver → enriched transactions, KYC snapshot joins
│   └── marts/         # Gold → fact tables and aggregates
│       └── src.yml    # Source definitions and freshness checks
├── snapshots/         # Historical KYC levels (SCD Type 2)
├── tests/
│   └── dbt_schema.yml # Data quality tests
├── run_dbt/           # Python helper scripts for setup and ingestion
├── .gitignore
├── architecture.md
├── dbt_project.yml
├── project_de.md
└── readme.md
```

---

## Models

| Layer | Model | Materialization | Description |
|-------|-------|-----------------|-------------|
| Bronze | `stg_users` | view | Clean and cast raw user records |
| Bronze | `stg_transactions` | view | Clean and cast raw transaction records |
| Bronze | `stg_rates` | view | Clean and cast raw FX rate records |
| Silver | `int_transactions_enriched` | view | Join transactions with historical KYC and FX rates |
| Silver | `kyc_users` *(snapshot)* | snapshot | SCD Type 2 history of user KYC levels |
| Gold | `fact_transactions` | table | Completed transactions with USD amounts and KYC level |
| Gold | `agg_transactions_daily` | table | Daily transaction aggregates per user |
| Gold | `agg_transactions_monthly` | table | Monthly transaction aggregates per user |
| Gold | `agg_transactions_quarterly` | table | Quarterly transaction aggregates per user |

---

## How to Run

### 1. Set up environment in Databricks

Create a `.dbt` folder in your workspace:

```bash
mkdir -p /Workspace/Users/<your-email>/.dbt
```

Add `profiles.yml` (replace `<host>`, `<http_path>`, `<token>`):

```yaml
databricks_dwh:
  target: dev
  outputs:
    dev:
      type: databricks
      catalog: workspace
      schema: bronze
      host: "<host>"
      http_path: "<http_path>"
      token: "<token>"
      threads: 4
      connect_retries: 1
```

> `profiles.yml` is listed in `.gitignore` — do not commit it.

---

### 2. Run dbt Commands

**Test connection:**

```bash
dbt debug --profiles-dir /Workspace/Users/<your-email>/.dbt
```

**Run snapshots first (required before models — captures historical KYC):**

```bash
dbt snapshot --profiles-dir /Workspace/Users/<your-email>/.dbt
```

**Run all models:**

```bash
dbt run --profiles-dir /Workspace/Users/<your-email>/.dbt
```

**Run tests:**

```bash
dbt test --profiles-dir /Workspace/Users/<your-email>/.dbt
```

**Check source freshness:**

```bash
dbt source freshness --profiles-dir /Workspace/Users/<your-email>/.dbt
```

**Generate and serve docs:**

```bash
dbt docs generate --profiles-dir /Workspace/Users/<your-email>/.dbt
dbt docs serve --profiles-dir /Workspace/Users/<your-email>/.dbt
```

---

### 3. Notes

* **Snapshots must run before models** — `int_transactions_enriched` depends on `kyc_users` snapshot data.
* **Gold tables are materialized as `table`** — rebuilt on each run for fast BI queries.
* **Tests** validate critical columns: unique IDs, not-null fields, accepted status values, and referential integrity between transactions and users.
* **Source freshness checks** are enabled on the rates table — warn after 24h, error after 48h.
* Use **Airflow or dbt Cloud** to orchestrate daily runs.
