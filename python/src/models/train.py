"""Train a fraud classifier.

Reads labeled returns from the warehouse, fits a logistic-regression model over
the engineered feature set, and writes a joblib artifact to
`config.DEFAULT_MODEL_PATH`. Predict scores are written by `predict.py`.
"""

from __future__ import annotations

import logging
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from ..config import DEFAULT_MODEL_PATH, configure_logging
from ..db import get_engine

log = logging.getLogger(__name__)

NUMERIC_FEATURES = [
    "refund_amount",
    "restocking_fee",
    "cycle_time_hours",
    "customer_lifetime_returns",
    "days_since_purchase",
]
CATEGORICAL_FEATURES = [
    "return_reason",
    "return_channel",
    "condition_received",
]


def _load_training_frame() -> pd.DataFrame:
    """Pull labeled returns joined to orders for feature computation."""
    sql = """
        SELECT
            r.return_id,
            r.fraud_flagged            AS label,
            r.refund_amount,
            r.restocking_fee,
            r.cycle_time_hours,
            r.return_reason,
            r.return_channel,
            r.condition_received,
            EXTRACT(EPOCH FROM r.return_date - o.order_date) / 86400.0 AS days_since_purchase,
            COALESCE(cust.lifetime_returns, 0) AS customer_lifetime_returns
        FROM returns r
        JOIN orders o         ON o.order_id  = (SELECT order_id FROM order_items WHERE order_item_id = r.order_item_id)
        LEFT JOIN v_customer_return_summary cust ON cust.customer_id = r.customer_id
        WHERE r.fraud_flagged IS NOT NULL
    """
    return pd.read_sql(sql, get_engine())


def build_pipeline() -> Pipeline:
    """scikit-learn pipeline: preprocess -> logistic regression."""
    preprocess = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
        ]
    )
    return Pipeline(
        steps=[
            ("preprocess", preprocess),
            ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ]
    )


def train(output_path: Path | None = None) -> Path:
    configure_logging()
    output_path = Path(output_path or DEFAULT_MODEL_PATH)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = _load_training_frame()
    if df.empty:
        raise RuntimeError("No labeled returns found. Populate returns.fraud_flagged first.")

    log.info("Training on %d labeled returns", len(df))
    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y = df["label"].astype(int)

    pipe = build_pipeline()
    pipe.fit(X, y)
    joblib.dump(pipe, output_path)
    log.info("Wrote model to %s", output_path)
    return output_path
