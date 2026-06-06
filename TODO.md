# TODO - Fix scripts/ETL errors

- [x] Inspect relevant ETL/load scripts and identify why `order_items` upsert is failing with duplicate `order_item_id`.
- [x] Create a safe upsert or idempotent load for `orders` and `order_items` (currently uses `to_sql(..., if_exists="append")`).
- [x] Fix module execution/import errors by making scripts runnable via `python -m` from the repo root.
- [ ] Implement code changes and run `generate_dummy_data.py` + `python -m scripts.run_etl` / `python -m scripts.generate_dummy_data` to verify.
- [ ] Add/adjust minimal tests if needed.


