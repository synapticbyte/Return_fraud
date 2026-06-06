# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

Analytics + ML project for **return fraud detection** and **reverse logistics optimization**. Three layers:

1. **SQL warehouse** (`sql/`) — Postgres-flavored schema for customers, orders, returns, and fraud signals, plus KPI views that Tableau consumes directly.
2. **Python pipeline** (`python/`) — ETL that ingests raw returns, fraud feature engineering, and a scikit-learn fraud classifier.
3. **Tableau** (`tableau/`) — analyst dashboards built on the SQL views, never on base tables.

## Build, run, test

All commands assume the repo root. Use a virtualenv.

```bash
# Install
pip install -r requirements.txt

# Apply schema (run in order — files are numbered)
psql "$DATABASE_URL" -f sql/schema/01_customers_products.sql
psql "$DATABASE_URL" -f sql/schema/02_orders.sql
psql "$DATABASE_URL" -f sql/schema/03_returns.sql
psql "$DATABASE_URL" -f sql/schema/04_views.sql

# Optional seed for dev
psql "$DATABASE_URL" -f sql/seeds/sample_data.sql

# Pipeline
python python/scripts/generate_dummy_data.py   # writes CSV to data/raw/
python python/scripts/run_etl.py                # raw -> warehouse
python python/scripts/train_model.py            # produces joblib artifact
python python/scripts/score_returns.py          # writes fraud_score to returns

# Tests
pytest python/tests
```

## Architecture notes

### Schema conventions (`sql/schema/`)
- Numbered prefix (`01_…`, `04_views.sql`) is load order. Apply in order; views depend on tables.
- All money columns are `NUMERIC(12,2)` — never `FLOAT`.
- `returns` is the central fact table. Everything in `04_views.sql` reads from it.
- `fraud_signals` is an append-only audit trail — one row per (return, signal_type). ML scores land in `returns.fraud_score`; signals stay granular for explainability.

### Python module layout (`python/src/`)
- `db.py` — single `get_engine()` factory that reads `DATABASE_URL` via `python-dotenv`. All DB access goes through SQLAlchemy; no raw `psycopg2` calls outside this module.
- `etl/extract.py` — reads CSVs from `data/raw/`, returns DataFrames.
- `etl/transform.py` — normalization, type coercion, deduplication, joining to dim tables. No DB writes.
- `etl/load.py` — idempotent upserts into the warehouse (prefer `INSERT … ON CONFLICT` over truncate/reload).
- `features/fraud_features.py` — per-return features: time-since-purchase, return-rate-per-customer rolling windows, channel mismatch, item-condition expectations. Pure functions over DataFrames.
- `models/train.py` / `models/predict.py` — scikit-learn pipeline. `train` reads labeled returns, fits, writes joblib to `FRAUD_MODEL_PATH`. `predict` loads and writes scores back to `returns.fraud_score`.
- `scripts/` are thin CLI wrappers — keep business logic in `src/`, scripts are entrypoints only.

### Where new work goes
- **New table or column?** Update `sql/schema/` AND `docs/data_dictionary.md`. Bump the schema file number if it changes load order.
- **New KPI for Tableau?** Add a view in `sql/schema/04_views.sql`, then document it in `tableau/README.md`. Do not let Tableau point at base tables.
- **New fraud signal?** Implement in `python/src/features/fraud_features.py` AND have it write rows to `fraud_signals` so analysts can see why a return was flagged.
- **New ML model version?** Write to `python/models/artifacts/<name>.joblib`; do not overwrite the previous artifact.

## Conventions
- SQL keywords in UPPERCASE, identifiers in `snake_case`.
- Python: type hints on public functions, docstrings only where the *why* is non-obvious.
- No `print()` in `src/` — use the `logging` module. Scripts may log to stdout.
- Don't commit data files, `.env`, or `.joblib` artifacts (all in `.gitignore`).

## Common pitfalls
- Applying schema files out of order — views in `04_views.sql` will fail if base tables don't exist.
- Pointing Tableau at base tables instead of views — schema changes will break dashboards. Always use views.
- Overwriting a trained model artifact — train a new versioned file instead.
- Writing `fraud_score` directly from a notebook — go through `scripts/score_returns.py` so the run is reproducible.
