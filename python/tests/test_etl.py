"""Tests for the transform pipeline (pure functions, no DB)."""

from __future__ import annotations

import pandas as pd

from src.etl import transform


def test_normalize_reason_maps_aliases() -> None:
    s = pd.Series(["Broken", "wrong size", "Buyer Remorse", "weird thing"])
    out = transform.normalize_reason(s)
    assert out.tolist() == ["defective", "wrong_size", "changed_mind", "other"]


def test_normalize_condition_maps_aliases() -> None:
    s = pd.Series(["New", "opened", "lightly used", "BROKEN"])
    out = transform.normalize_condition(s)
    assert out.tolist() == ["new_unopened", "opened_unused", "used", "damaged"]


def test_coerce_money_rounds_and_fills() -> None:
    s = pd.Series(["10.555", None, "oops"])
    out = transform.coerce_money(s)
    assert out.tolist() == [10.56, 0.0, 0.0]


def test_dedupe_returns_keeps_latest() -> None:
    df = pd.DataFrame(
        {
            "return_id": [1, 1, 2],
            "return_date": pd.to_datetime(["2025-01-01", "2025-01-05", "2025-01-02"]),
        }
    )
    out = transform.dedupe_returns(df)
    assert len(out) == 2
    row = out.loc[out["return_id"] == 1].iloc[0]
    assert row["return_date"] == pd.Timestamp("2025-01-05")
