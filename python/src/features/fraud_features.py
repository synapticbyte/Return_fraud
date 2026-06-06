"""Per-return fraud feature engineering.

Each function takes a DataFrame of returns joined to orders/order_items and
returns a DataFrame of (return_id, feature_name, score, evidence) tuples that
the loader writes into `fraud_signals`. Keep these as pure functions — easy to
unit test, easy to recompute when logic changes.
"""

from __future__ import annotations

import json
from datetime import timedelta

import numpy as np
import pandas as pd

SERIAL_RETURNER_THRESHOLD = 5   # returns in the rolling window
SERIAL_WINDOW_DAYS = 90
WARDROBING_MIN_DAYS = 1         # returned within N days = suspicious
WARDROBING_MAX_DAYS = 3
LATE_NIGHT_RETURN_HOUR_START = 23
LATE_NIGHT_RETURN_HOUR_END = 4


def _window_returns(returns: pd.DataFrame, customer_id: int, ref_date: pd.Timestamp, days: int) -> pd.DataFrame:
    start = ref_date - timedelta(days=days)
    mask = (
        (returns["customer_id"] == customer_id)
        & (returns["return_date"] >= start)
        & (returns["return_date"] < ref_date)
    )
    return returns.loc[mask]


def detect_serial_returners(returns: pd.DataFrame) -> pd.DataFrame:
    """Customers with > SERIAL_RETURNER_THRESHOLD returns in the last SERIAL_WINDOW_DAYS."""
    out = []
    for _, r in returns.iterrows():
        history = _window_returns(returns, r["customer_id"], r["return_date"], SERIAL_WINDOW_DAYS)
        count = len(history)
        if count > SERIAL_RETURNER_THRESHOLD:
            out.append(
                {
                    "return_id": r["return_id"],
                    "signal_type": "serial_returner",
                    "severity": "high" if count > SERIAL_RETURNER_THRESHOLD * 2 else "medium",
                    "score": min(1.0, count / (SERIAL_RETURNER_THRESHOLD * 3)),
                    "evidence": {"returns_in_window": int(count), "window_days": SERIAL_WINDOW_DAYS},
                }
            )
    return pd.DataFrame(out)


def detect_wardrobing(returns: pd.DataFrame) -> pd.DataFrame:
    """Returns filed 1-3 days after purchase with 'changed_mind' / 'not_as_described'.

    Caller must pre-join `days_since_purchase` (computed in `models/train.py`).
    """
    if "days_since_purchase" not in returns.columns:
        return pd.DataFrame(columns=["return_id", "signal_type", "severity", "score", "evidence"])
    mask = (
        (returns["days_since_purchase"] >= WARDROBING_MIN_DAYS)
        & (returns["days_since_purchase"] <= WARDROBING_MAX_DAYS)
        & (returns["return_reason"].isin(["changed_mind", "not_as_described"]))
    )
    suspicious = returns.loc[mask]
    out = []
    for _, r in suspicious.iterrows():
        out.append(
            {
                "return_id": r["return_id"],
                "signal_type": "wardrobing",
                "severity": "high",
                "score": 0.85,
                "evidence": {"days_since_purchase": int(r["days_since_purchase"])},
            }
        )
    return pd.DataFrame(out)


def detect_late_night_returns(returns: pd.DataFrame) -> pd.DataFrame:
    """Returns logged between 23:00 and 04:00 local — common in scripted fraud."""
    hour = pd.to_datetime(returns["return_date"]).dt.hour
    mask = ((hour >= LATE_NIGHT_RETURN_HOUR_START) | (hour < LATE_NIGHT_RETURN_HOUR_END))
    out = returns.loc[mask, ["return_id"]].copy()
    out["signal_type"] = "time_anomaly"
    out["severity"] = "low"
    out["score"] = 0.35
    out["evidence"] = returns.loc[mask, "return_date"].astype(str).apply(lambda v: {"return_date": v})
    return out


def detect_value_mismatch(returns: pd.DataFrame) -> pd.DataFrame:
    """Refund amount > original unit price (refund > what they paid = bad signal)."""
    if "unit_price" not in returns.columns:
        return pd.DataFrame(columns=["return_id", "signal_type", "severity", "score", "evidence"])
    mask = returns["refund_amount"] > returns["unit_price"]
    out = []
    for _, r in returns.loc[mask].iterrows():
        out.append(
            {
                "return_id": r["return_id"],
                "signal_type": "value_mismatch",
                "severity": "high",
                "score": 0.95,
                "evidence": {
                    "refund_amount": float(r["refund_amount"]),
                    "unit_price": float(r["unit_price"]),
                },
            }
        )
    return pd.DataFrame(out)


def compute_all_signals(returns: pd.DataFrame) -> pd.DataFrame:
    """Run every detector and concatenate. Each row is a (return, signal) tuple."""
    frames = [
        detect_serial_returners(returns),
        detect_wardrobing(returns),
        detect_late_night_returns(returns),
        detect_value_mismatch(returns),
    ]
    df = pd.concat([f for f in frames if not f.empty], ignore_index=True)
    if df.empty:
        return df
    df["model_version"] = "rules_v1"
    return df
