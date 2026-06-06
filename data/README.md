# Data

Local-only data is intentionally gitignored. The three subdirectories serve different roles:

- `raw/`     — upstream CSV drops (returns, orders, customers). Never edited by hand; written by upstream systems or `generate_dummy_data.py`.
- `processed/` — cleaned/normalized parquet or CSV intermediate files. Optional scratch space for ad-hoc analysis.
- `exports/` — one-off exports for stakeholders (CSV snapshots, monthly packs).

Nothing in this directory should be committed. The schema in `sql/schema/` is the source of truth.