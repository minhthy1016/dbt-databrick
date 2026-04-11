# CLAUDE.md — dbt_project (Remitano / Databricks)

## Project Overview

Crypto transaction analytics warehouse for the Remitano exchange platform.
Built on **Databricks Delta Lake + Unity Catalog** using **dbt**.

- **Catalog:** `workspace`
- **Schemas:** `raw` (sources) → `bronze` → `silver` → `gold`
- **dbt project name:** `databricks_warehouse`
- **dbt profile:** `databricks_dwh` (defined externally in `~/.dbt/profiles.yml`)

---

## Model Inventory

| Model | Layer | Materialization | Schema |
|-------|-------|-----------------|--------|
| `stg_users` | Bronze | view | `workspace.bronze` |
| `stg_transactions` | Bronze | view | `workspace.bronze` |
| `stg_rates` | Bronze | view | `workspace.bronze` |
| `kyc_users` | Silver (snapshot) | snapshot | `workspace.silver` |
| `int_transactions_enriched` | Silver | view | `workspace.silver` |
| `fact_transactions` | Gold | table | `workspace.gold` |
| `agg_transactions_daily` | Gold | table | `workspace.gold` |
| `agg_transactions_monthly` | Gold | table | `workspace.gold` |
| `agg_transactions_quarterly` | Gold | table | `workspace.gold` |

---

## Naming Conventions

| Prefix | Layer | Example |
|--------|-------|---------|
| `stg_` | Staging (Bronze) | `stg_transactions` |
| `int_` | Intermediate (Silver) | `int_transactions_enriched` |
| `fact_` | Fact table (Gold) | `fact_transactions` |
| `agg_` | Aggregate (Gold) | `agg_transactions_daily` |

- Snapshots live in `snapshots/` and are named without a prefix (e.g., `kyc_users`).
- Source tables are referenced via `{{ source('raw', 'table_name') }}`.
- All other model references use `{{ ref('model_name') }}`.

---

## Data Lineage

```
raw_users ──────────────────────────────────────► stg_users ──► kyc_users (snapshot)
                                                                       │
raw_transactions ──► stg_transactions ──► int_transactions_enriched ──► fact_transactions ──► agg_transactions_daily
                                                    │                                     ──► agg_transactions_monthly
raw_rates ──────────► stg_rates ────────────────────┘                                    ──► agg_transactions_quarterly
```

**Critical:** `kyc_users` snapshot must exist before `int_transactions_enriched` can run.
Always run `dbt snapshot` before `dbt run`.

---

## Materialization Rules

- **Staging:** always `view` — lightweight cleaning only, no persistence.
- **Intermediate:** always `view` — do NOT add `is_incremental()` logic to a view-materialized model.
- **Gold fact/aggregates:** always `table` — rebuilt on each run for BI query performance.
- **Snapshots:** use `strategy='timestamp'` with `unique_key='user_id'` and `updated_at='updated_at'`.

---

## Key Commands

Run all commands from this directory (`dbt_project_remitano/dbt_project/`).

```bash
# 1. Snapshots first (always)
dbt snapshot --profiles-dir /Workspace/Users/<email>/.dbt

# 2. Run all models
dbt run --profiles-dir /Workspace/Users/<email>/.dbt

# 3. Run a specific layer
dbt run --select staging --profiles-dir /Workspace/Users/<email>/.dbt
dbt run --select int --profiles-dir /Workspace/Users/<email>/.dbt
dbt run --select marts --profiles-dir /Workspace/Users/<email>/.dbt

# 4. Run a single model and its upstream dependencies
dbt run --select +fact_transactions --profiles-dir /Workspace/Users/<email>/.dbt

# 5. Tests
dbt test --profiles-dir /Workspace/Users/<email>/.dbt
dbt test --select stg_transactions --profiles-dir /Workspace/Users/<email>/.dbt

# 6. Source freshness
dbt source freshness --profiles-dir /Workspace/Users/<email>/.dbt

# 7. Generate and serve docs
dbt docs generate --profiles-dir /Workspace/Users/<email>/.dbt
dbt docs serve --profiles-dir /Workspace/Users/<email>/.dbt
```

---

## Testing Conventions

Tests are defined in `tests/dbt_schema.yml`.

### Required tests for every new model

| Column type | Required tests |
|-------------|---------------|
| Primary key (e.g., `transaction_id`, `user_id`) | `unique` + `not_null` |
| Foreign key (e.g., `user_id` in transactions) | `not_null` + `relationships` |
| Status / enum column | `accepted_values` |
| Amount / financial column | `not_null` |

### Severity
- All tests use the default severity `error` (set globally in `dbt_project.yml`).
- Do NOT downgrade to `warn` for primary key uniqueness — duplicates must fail the pipeline.

### Relationship test pattern
```yaml
- name: column_name
  tests:
    - relationships:
        to: ref('parent_model')
        field: column_name
```

---

## Adding a New Model

1. Place the file in the correct layer folder (`staging/`, `int/`, or `marts/`).
2. Use the correct naming prefix (`stg_`, `int_`, `fact_`, `agg_`).
3. Do NOT set `materialized` in the model file — it is inherited from `dbt_project.yml` by layer.
4. Add tests in `tests/dbt_schema.yml` following the conventions above.
5. If the model introduces a new source table, add it to `models/marts/src.yml`.

---

## Adding a New Aggregate Model

Aggregates must match the SELECT expressions in GROUP BY exactly:

```sql
-- Daily
select
    user_id,
    date(transaction_date) as day,          -- expression applied
    count(*) as num_transactions,
    sum(amount_usd) as total_amount_usd,
    kyc_level_at_transaction
from {{ ref('fact_transactions') }}
group by user_id, date(transaction_date), kyc_level_at_transaction  -- same expression here
```

```sql
-- Monthly
group by user_id, date_trunc('month', transaction_date), kyc_level_at_transaction

-- Quarterly
group by user_id, date_trunc('quarter', transaction_date), kyc_level_at_transaction
```

Do NOT group by the raw `transaction_date` column when the SELECT uses a truncation function.

---

## Source Definitions (`models/marts/src.yml`)

Sources are under `workspace.raw`. To add a new source table:

```yaml
- name: new_table_name
  # Add freshness if the table is time-sensitive:
  loaded_at_field: updated_at
  freshness:
    warn_after: {count: 24, period: hour}
    error_after: {count: 48, period: hour}
```

---

## Ingestion Scripts (`run_dbt/`)

These Python notebooks run on Databricks (not locally):

| Script | Purpose |
|--------|---------|
| `Ingest.py` | Fetches Binance OHLCV klines for all destination currencies and writes to `workspace.raw.combine_raw_rates` as a Delta table |
| `Setup.py` | Creates volumes, streams CSV files into Bronze Delta tables via Auto Loader |
| `test_dbt.py` | Test / validation notebook |

Raw data paths in Databricks Volumes:
- Transactions: `/Volumes/workspace/raw/rawvolume/rawdata/transactions/`
- Users: `/Volumes/workspace/raw/rawvolume/rawdata/users/`
- Rates output: `/Volumes/workspace/raw/rawvolume/rawdata/raw_rates/output`

---

## What NOT to Do

- Do NOT add `is_incremental()` blocks to `view`-materialized models — the block will never execute.
- Do NOT commit `profiles.yml` — it is gitignored and contains credentials.
- Do NOT commit the `target/`, `logs/`, or `dbt_packages/` directories — they are gitignored.
- Do NOT alias `destination_currency` to `currency` or any other name that loses semantic meaning.
- Do NOT use `severity: warn` on `unique` tests for primary key columns.
- Do NOT run `dbt run` before `dbt snapshot` — `int_transactions_enriched` will fail if `kyc_users` does not exist.
- Do NOT group aggregates by the raw timestamp column when the SELECT applies `date()` or `date_trunc()`.
