"""Tests for the fraud feature engineering functions."""

from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
import pytest

from src.features import fraud_features as ff


def _returns_fixture() -> pd.DataFrame:
    base = datetime(2025, 1, 1)
    rows = []
    for i in range(7):
        rows.append(
            {
                "return_id": 100 + i,
                "customer_id": 1,
                "return_date": base + timedelta(days=i),
                "return_reason": "changed_mind",
                "return_channel": "web",
                "refund_amount": 50.0,
                "unit_price": 50.0,
            }
        )
    return pd.DataFrame(rows)


def test_serial_returner_flags_high_volume_customer() -> None:
    df = _returns_fixture()
    out = ff.detect_serial_returners(df)
    assert not out.empty
    assert (out["signal_type"] == "serial_returner").all()
    assert set(out["severity"]).issubset({"medium", "high"})


def test_value_mismatch_flags_refund_above_price() -> None:
    df = pd.DataFrame(
        [
            {"return_id": 1, "customer_id": 1, "return_date": datetime(2025, 1, 1),
             "return_reason": "defective", "return_channel": "web",
             "refund_amount": 200.0, "unit_price": 100.0},
            {"return_id": 2, "customer_id": 1, "return_date": datetime(2025, 1, 2),
             "return_reason": "defective", "return_channel": "web",
             "refund_amount": 50.0, "unit_price": 50.0},
        ]
    )
    out = ff.detect_value_mismatch(df)
    assert out["return_id"].tolist() == [1]


def test_late_night_detection_picks_off_hours() -> None:
    df = pd.DataFrame(
        {
            "return_id": [1, 2, 3],
            "return_date": [
                datetime(2025, 1, 1, 2, 0),
                datetime(2025, 1, 1, 12, 0),
                datetime(2025, 1, 1, 23, 30),
            ],
        }
    )
    out = ff.detect_late_night_returns(df)
    assert sorted(out["return_id"].tolist()) == [1, 3]


def test_compute_all_signals_concatenates() -> None:
    df = _returns_fixture()
    df["unit_price"] = 50.0
    df["days_since_purchase"] = 2
    out = ff.compute_all_signals(df)
    assert "model_version" in out.columns
    assert out["model_version"].iloc[0] == "rules_v1"
