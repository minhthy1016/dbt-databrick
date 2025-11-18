
# README.md

## Project Overview

This project builds a **Bronze → Silver → Gold ETL pipeline** on **Databricks Delta Lake** using **dbt**.

**Purpose:**

* Provide a **Single Source of Truth** for crypto transaction data.
* Enable analytics on:

  * Daily/monthly/quarterly transaction volumes in USD
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
│   ├── staging/       # Bronze → cleaning, type cast, renaming
│   ├── int/           # Silver → enriched transactions, KYC snapshot joins
│   └── marts/         # Gold → fact tables and aggregates
├── snapshots/         # Historical KYC levels (SCD Type 2)
├── tests/             # Data quality tests
└── architecture.md
├── dbt_project.yml
└── readme.md
```

---

## How to Run

### 1️⃣ Set up environment in Databricks

* Create a `.dbt` folder in your workspace:

```bash
mkdir -p /Workspace/Users/<your-email>/.dbt
```

* Add `profiles.yml` (replace `<host>`, `<http_path>`, `<token>`):

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

---

### 2️⃣ Run dbt Commands

* **Test connection:**

```bash
dbt debug --profiles-dir /Workspace/Users/<your-email>/.dbt
```

* **Run snapshots (historical KYC):**

```bash
dbt snapshot --profiles-dir /Workspace/Users/<your-email>/.dbt
```

* **Run all models:**

```bash
dbt run --profiles-dir /Workspace/Users/<your-email>/.dbt
```

* **Run tests:**

```bash
dbt test --profiles-dir /Workspace/Users/<your-email>/.dbt
```

* **Generate docs (optional):**

```bash
dbt docs generate --profiles-dir /Workspace/Users/<your-email>/.dbt
dbt docs serve --profiles-dir /Workspace/Users/<your-email>/.dbt
```

---

### 3️⃣ Notes

* **Incremental models** are used for large tables (transactions, fact tables) to save compute.
* **Snapshots** ensure historical KYC levels are preserved for analytics.
* **Tests** validate critical columns: unique IDs, not null fields, valid KYC levels.
* Use **Airflow or dbt Cloud** to orchestrate daily runs.

---

