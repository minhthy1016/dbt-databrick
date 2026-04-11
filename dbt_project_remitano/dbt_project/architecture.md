# ARCHITECTURE

## 1. DWH Choice

**Selected:** Databricks (Delta Lake + Unity Catalog)

**Reasons:**

* Combines data lake and data warehouse in one platform.
* Delta Lake supports **ACID transactions** and **time travel**, making it ideal for tracking historical KYC changes.
* Scales easily for large crypto transaction volumes.
* Native **dbt integration** via the `dbt-databricks` adapter.
* SQL-friendly for BI tools.
* Auto-scaling compute and cost efficiency for large workloads.

---

## 2. dbt Materialization Strategy

| Layer | Model | Materialization | Reason |
|-------|-------|-----------------|--------|
| **Bronze (Staging)** | `stg_*` | `view` | Lightweight cleaning and type casting over raw tables. No storage cost. |
| **Silver (Snapshot)** | `kyc_users` | `snapshot` | SCD Type 2 — preserves full history of KYC level changes per user. |
| **Silver (Intermediate)** | `int_transactions_enriched` | `view` | Joins transactions with KYC history and FX rates. Kept as a view to avoid redundant storage. |
| **Gold (Fact)** | `fact_transactions` | `table` | Completed transactions only, materialized for fast BI queries. |
| **Gold (Aggregates)** | `agg_transactions_*` | `table` | Daily / monthly / quarterly summaries, materialized for dashboards. |

---

## 3. Data Model Overview

### Bronze Layer

Source tables in `workspace.raw`:

| Source Table | Staging Model | Description |
|---|---|---|
| `raw_users` | `stg_users` | User records with KYC metadata |
| `raw_transactions` | `stg_transactions` | Currency exchange transactions |
| `combine_raw_rates` | `stg_rates` | FX close prices by symbol and date |

Stored in schema: `workspace.bronze`

### Silver Layer

| Model | Type | Description |
|---|---|---|
| `kyc_users` | Snapshot (SCD2) | Full KYC history per user with `valid_from` / `valid_to` timestamps |
| `int_transactions_enriched` | View | Transactions enriched with the user's KYC level *at the time of the transaction* and the USD conversion rate for that day |

Stored in schema: `workspace.silver`

### Gold Layer

| Model | Type | Description |
|---|---|---|
| `fact_transactions` | Table | Completed transactions with `amount_usd`, `destination_currency`, and `kyc_level_at_transaction` |
| `agg_transactions_daily` | Table | Per-user transaction count and USD volume grouped by day |
| `agg_transactions_monthly` | Table | Per-user transaction count and USD volume grouped by month |
| `agg_transactions_quarterly` | Table | Per-user transaction count and USD volume grouped by quarter |

Stored in schema: `workspace.gold`

---

## 4. Data Lineage

```
raw_users ──────────────────────────────────> stg_users ──> kyc_users (snapshot)
                                                                  │
raw_transactions ──> stg_transactions ──> int_transactions_enriched ──> fact_transactions ──> agg_transactions_daily
                                                  │                                       ──> agg_transactions_monthly
raw_rates ──────────> stg_rates ─────────────────┘                                       ──> agg_transactions_quarterly
```

**Run order:**

1. `dbt snapshot` — build `kyc_users` SCD2 history
2. `dbt run --select staging` — Bronze models
3. `dbt run --select int` — Silver enrichment (depends on snapshot)
4. `dbt run --select marts` — Gold fact and aggregates

---

## 5. Orchestration

**Tool:** Airflow or dbt Cloud Job

**Recommended schedule:**

| Step | Frequency | Notes |
|------|-----------|-------|
| Raw ingestion | Every 5 minutes (streaming or batch) | Load into `workspace.raw` |
| `dbt snapshot` | Daily (before models) | Capture KYC changes |
| Bronze + Silver models | Hourly | Lightweight views, fast to run |
| Gold models | Hourly or daily | Rebuilt as tables |

---

## 6. Data Quality & Testing

Tests are defined in `tests/dbt_schema.yml`:

| Test | Columns | Models |
|------|---------|--------|
| `unique` + `not_null` | `user_id` | `stg_users` |
| `unique` + `not_null` | `transaction_id` | `stg_transactions`, `int_transactions_enriched`, `fact_transactions` |
| `not_null` | `user_id` | `stg_transactions` |
| `accepted_values` | `status` | `stg_transactions` — values: `completed`, `canceled`, `canceled_by_system` |
| `relationships` | `stg_transactions.user_id` → `stg_users.user_id` | Referential integrity |
| `not_null` | `source_amount`, `destination_amount` | `stg_transactions` |
| `not_null` | `amount_usd` | `int_transactions_enriched`, `fact_transactions` |
| `not_null` | `user_id` | `agg_transactions_*` |

Source freshness check on `combine_raw_rates`:
- **Warn** if not updated in 24 hours
- **Error** if not updated in 48 hours

---

## 7. Security & Governance

* Unity Catalog for access control.
* Table-level, column-level, and row-level permissions.
* Automatic lineage tracking via Databricks + dbt.
* `profiles.yml` excluded from version control via `.gitignore`.

---

## 8. Scalability Considerations

* Auto-scaling clusters for heavy dbt transformations.
* Photon execution for SQL acceleration.
* Delta Lake Z-Ordering for fast reads on large tables.
* Streaming support available for real-time transaction ingestion.
