# Python package

## Layout

```
python/
├── src/
│   ├── config.py            Environment / path resolution
│   ├── db.py                SQLAlchemy engine factory
│   ├── etl/                 Extract → Transform → Load
│   ├── features/            Fraud signal engineering
│   └── models/              scikit-learn train + predict
├── scripts/                 CLI entrypoints
├── tests/                   pytest
└── models/artifacts/        Trained model output (gitignored)
```

## Run order

1. `python scripts/generate_dummy_data.py` — writes CSVs to `data/raw/`
2. `python scripts/run_etl.py` — loads them into the warehouse
3. `python scripts/train_model.py` — fits a classifier, writes joblib
4. `python scripts/score_returns.py` — scores unscored returns in the warehouse

## Importing

All application code lives under `src/`. To run a script or test from the repo root:

```bash
PYTHONPATH=python python scripts/run_etl.py
PYTHONPATH=python pytest python/tests
```

Or install the package locally:

```bash
pip install -e python/
```
