
# ARCHITECTURE.md

## 1. DWH Choice

**Selected:** Databricks (Delta Lake + Unity Catalog)

**Reasons:**

* Combines data lake + data warehouse in one platform

* Delta Lake supports **ACID transactions** and **time travel**, perfect for tracking historical KYC. 
* Scales easily for large crypto transaction volumes.
* Native **dbt integration** and easy CI/CD.
* SQL-friendly for BI tools. Deep integration with DBT Cloud / dbt-databricks adapter
* Supports **incremental models** to save compute costs.
* Auto-scaling compute and cost efficiency for big workloads

---

## 2. dbt Materialization Strategy

| Layer / Model                | Materialization         | Reason                                                                 |
| ---------------------------- | ----------------------- | ---------------------------------------------------------------------- |
| **Staging (Bronze)**         | `view`                  | Clean and cast raw data, fast and lightweight.                         |
| **Intermediate (Silver)**    | `view` / `incremental`  | Enriched transactions; incremental reduces compute for large datasets. |
| **Snapshots**                | `snapshot`              | Track historical KYC levels (SCD Type 2).                              |
| **Gold (Fact / Aggregates)** | `table` / `incremental` | Fast BI queries; aggregates updated daily/monthly/quarterly.           |
| **Ephemeral**                | `ephemeral`             | Reusable logic without storing data.                                   |

---
## 3. Data Model Overview
**Bronze Layer**
From `workspace.raw.` we use `raw_users`, `raw_transactions`, `combine_raw_rates table`. 
- Raw ingestion into Delta Lake: `stg_transactions`, `stg_users`, `stg_rates`

- Stored in `bronze_bronze`

**Silver Layer (DBT Transformations)**

- Cleaned models:

`kyc_users` (cleaned KYC records)

- These apply: Type casting, Deduplication, Standardized column names

**Gold Layer**

Final business-ready model: `fct_transactions`

Features:
- USD conversion using FX rates

- Latest KYC level joined to each transaction

- Materialized as view or table depending on requirement



## 4. Orchestration (Daily Pipeline)

**Tool:** Airflow or dbt Cloud Job

**Pipeline:**

1. **Ingestion** → load raw raw_users, raw_transactions, raw_rates into **Bronze**.
2. **Transformation** → run dbt:

   * Snapshots: KYC history
   * Staging → Silver → Gold models
   * Tests for data quality
   * Optional docs generation
3. **Aggregates** → daily, monthly, quarterly summaries

**Dependencies:**

```
raw_users --------+---> stg_users ----> kyc_users
                  |
raw_transactions --+--> stg_transactions
                  |
raw_rates --------+---> stg_rates
                  |
         int_transactions_enriched_new --> fact_transactions --> aggregates
```

* Snapshots run **before enriched transactions**
* Aggregates depend on **fact tables**
* Schedule daily at off-peak hours, with retries and logging.

---
## 5. Data Quality & Testing
* dbt tests

- Not null: `transaction_id`, `user_id`, `kyc_level`

- Relationships:

transactions.user_id ↔ kyc_users.user_id

transactions.source_currency ↔ rates.symbol

- Unique keys: Freshness for rates (daily)

## 6. Scheduling & Orchestration

Use Databricks Jobs or dbt Cloud:

- Bronze ingestion: every 5 minutes (streaming or batch)

- Silver transforms: hourly

- Gold mart rebuild: hourly or daily

## 7. Security & Governance

- Unity Catalog for access control

- Table-level, column-level, and row-level permissions

- Auto lineage tracking via Databricks + dbt

## 8. Scalability Considerations

- Auto-scaling clusters for heavy dbt transformations

- Photon execution for SQL acceleration

- Delta Lake Z-Ordering for fast reads

- Streaming support for real-time transactions

