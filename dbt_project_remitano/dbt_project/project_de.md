# Project Notes

## Running dbt on Databricks

- Configure `profiles.yml` and place it at `/Workspace/Users/<your_email>/.dbt/profiles.yml`. Do not commit this file — it is listed in `.gitignore`.
- All scripts in `run_dbt/` (`Ingest.py`, `Setup.py`, `test_dbt.py`) can be run via the Databricks notebook panel.

## Screenshots

Architecture diagram and Unity Catalog layout in Databricks after a full run:

![Architecture diagram](https://github.com/user-attachments/assets/e0527224-c81d-4eb7-9240-61776c774959)

![Unity Catalog layout](https://github.com/user-attachments/assets/60bd5860-caeb-4395-81b9-49b499defe0b)
