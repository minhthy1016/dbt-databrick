# CLAUDE.md — dbt-databrick

This repo contains a dbt + Databricks data warehouse project for the Remitano crypto exchange platform. All dbt code lives in `dbt_project_remitano/dbt_project/`.

## Repo Layout

```
dbt-databrick/
└── dbt_project_remitano/
    └── dbt_project/          ← working directory for all dbt work
        ├── models/
        │   ├── staging/      ← Bronze: stg_* views over raw sources
        │   ├── int/          ← Silver: int_* enrichment views
        │   └── marts/        ← Gold: fact_* and agg_* tables
        ├── snapshots/        ← SCD Type 2: kyc_users
        ├── tests/
        │   └── dbt_schema.yml
        ├── run_dbt/          ← Databricks notebooks (Python): ingestion scripts
        ├── dbt_project.yml
        └── models/marts/src.yml   ← source definitions + freshness checks
```

## Key Commands

All dbt commands must be run from `dbt_project_remitano/dbt_project/` with `--profiles-dir` pointing to the Databricks `.dbt` folder:

```bash
# Always run snapshots first — int_transactions_enriched depends on kyc_users
dbt snapshot --profiles-dir /Workspace/Users/<email>/.dbt

# Run all models
dbt run --profiles-dir /Workspace/Users/<email>/.dbt

# Run a specific layer
dbt run --select staging --profiles-dir /Workspace/Users/<email>/.dbt
dbt run --select int --profiles-dir /Workspace/Users/<email>/.dbt
dbt run --select marts --profiles-dir /Workspace/Users/<email>/.dbt

# Run tests
dbt test --profiles-dir /Workspace/Users/<email>/.dbt

# Check source freshness (rates table)
dbt source freshness --profiles-dir /Workspace/Users/<email>/.dbt
```

See `dbt_project_remitano/dbt_project/CLAUDE.md` for full project conventions and guidelines.
