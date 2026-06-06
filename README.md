# Return Fraud & Reverse Logistics Optimization

Detects fraudulent returns and optimizes the reverse-logistics pipeline (receiving → grading → disposition → recovery). The stack is SQL for the warehouse, Python for ETL and modeling, and Tableau for analyst-facing dashboards.

## Layout

```
suppchain/
├── sql/             Warehouse schema, seed data, and analytical queries
├── python/          ETL pipeline, fraud features, ML model, scripts, tests
├── tableau/         Workbook documentation (data sources, sheets, owners)
├── data/            Local-only data — raw, processed, exports (gitignored)
├── docs/            Data dictionary and methodology notes
└── .github/         CI workflow
```

## Quick start

1. **Set up the warehouse.** Create a Postgres database and apply the schema:
   ```bash
   psql $DATABASE_URL -f sql/schema/01_customers_products.sql
   psql $DATABASE_URL -f sql/schema/02_orders.sql
   psql $DATABASE_URL -f sql/schema/03_returns.sql
   psql $DATABASE_URL -f sql/schema/04_views.sql
   ```
2. **Configure environment.** Copy `.env.example` to `.env` and fill in the connection string.
3. **Install Python deps.**
   ```bash
   pip install -r requirements.txt
   ```
4. **Generate dummy data and run the pipeline.**
   ```bash
   python python/scripts/generate_dummy_data.py
   python python/scripts/run_etl.py
   python python/scripts/train_model.py
   python python/scripts/score_returns.py
   ```
5. **Run tests.**
   ```bash
   pytest python/tests
   ```
6. **Open Tableau.** Connect to the warehouse using the views in `sql/schema/04_views.sql` — see `tableau/README.md` for the workbook map.

## What lives where

- **Schema** (`sql/schema/`) is the source of truth for tables, columns, and KPI views.
- **ETL** (`python/src/etl/`) pulls raw returns from upstream systems, normalizes them, and loads them into the warehouse.
- **Features** (`python/src/features/`) compute fraud signals and reverse-logistics KPIs that aren't easy to express in SQL (e.g. time-since-purchase anomalies, return-rate rolling windows).
- **Models** (`python/src/models/`) train a fraud classifier and emit per-return fraud scores.
- **Tableau** consumes the views in `sql/schema/04_views.sql` directly; do not point workbooks at base tables.

See `CLAUDE.md` for guidance on working in this repo."# Return_fraud" 
