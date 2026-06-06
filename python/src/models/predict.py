"""Score unscored returns using the trained model artifact."""

from __future__ import annotations

import logging
from pathlib import Path

import joblib
import pandas as pd
from sqlalchemy import text

from ..config import DEFAULT_MODEL_PATH, configure_logging
from ..db import get_engine
from .train import CATEGORICAL_FEATURES, NUMERIC_FEATURES

log = logging.getLogger(__name__)

HIGH_RISK_THRESHOLD = 0.7


def _load_unscored() -> pd.DataFrame:
    sql = """
        SELECT
            r.return_id,
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
        WHERE r.fraud_score IS NULL
    """
    return pd.read_sql(sql, get_engine())


def predict(model_path: Path | None = None) -> int:
    configure_logging()
    model_path = Path(model_path or DEFAULT_MODEL_PATH)
    if not model_path.exists():
        raise FileNotFoundError(f"Model artifact not found at {model_path}. Run train_model.py first.")

    pipe = joblib.load(model_path)
    df = _load_unscored()
    if df.empty:
        log.info("No unscored returns; nothing to do.")
        return 0

    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    scores = pipe.predict_proba(X)[:, 1]

    engine = get_engine()
    rows = [
        {
            "return_id": int(rid),
            "fraud_score": round(float(s), 3),
            "fraud_flagged": bool(s >= HIGH_RISK_THRESHOLD),
        }
        for rid, s in zip(df["return_id"], scores)
    ]
    with engine.begin() as conn:
        for r in rows:
            conn.execute(
                text(
                    "UPDATE returns SET fraud_score = :fraud_score, fraud_flagged = :fraud_flagged "
                    "WHERE return_id = :return_id"
                ),
                r,
            )
    log.info("Scored %d returns", len(rows))
    return len(rows)
