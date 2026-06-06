"""Normalization, type coercion, and dedup for raw warehouse inputs.

Pure functions over DataFrames. No DB access here.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

REASON_ALIASES = {
    "defective": "defective",
    "broken": "defective",
    "damaged": "defective",
    "wrong size": "wrong_size",
    "wrong_size": "wrong_size",
    "sizing": "wrong_size",
    "not as described": "not_as_described",
    "not_as_described": "not_as_described",
    "misrepresented": "not_as_described",
    "changed mind": "changed_mind",
    "changed_mind": "changed_mind",
    "buyer remorse": "changed_mind",
    "late": "late_delivery",
    "late_delivery": "late_delivery",
    "duplicate": "duplicate",
}

CONDITION_ALIASES = {
    "new": "new_unopened",
    "sealed": "new_unopened",
    "unopened": "new_unopened",
    "opened": "opened_unused",
    "lightly used": "used",
    "used": "used",
    "broken": "damaged",
    "damaged": "damaged",
}


def normalize_reason(series: pd.Series) -> pd.Series:
    """Lowercase + alias-map free-text return reasons to the canonical enum."""
    return (
        series.fillna("other")
        .astype(str)
        .str.strip()
        .str.lower()
        .map(lambda v: REASON_ALIASES.get(v, "other"))
    )


def normalize_condition(series: pd.Series) -> pd.Series:
    return (
        series.fillna("used")
        .astype(str)
        .str.strip()
        .str.lower()
        .map(lambda v: CONDITION_ALIASES.get(v, "used"))
    )


def coerce_money(series: pd.Series) -> pd.Series:
    """Round to 2 dp and NaN -> 0.0 to match NUMERIC(12,2)."""
    return pd.to_numeric(series, errors="coerce").fillna(0.0).round(2)


def dedupe_returns(df: pd.DataFrame) -> pd.DataFrame:
    """Keep the latest record per return_id (later row wins)."""
    return (
        df.sort_values("return_date")
        .drop_duplicates(subset="return_id", keep="last")
        .reset_index(drop=True)
    )


def transform_returns(raw: pd.DataFrame) -> pd.DataFrame:
    """Full normalize pipeline for the returns fact table."""
    df = raw.copy()
    df["return_reason"] = normalize_reason(df["return_reason"])
    df["condition_received"] = normalize_condition(df["condition_received"])
    for col in ("refund_amount", "restocking_fee", "processing_cost", "recovered_value"):
        if col in df.columns:
            df[col] = coerce_money(df[col])
    df["fraud_flagged"] = df.get("fraud_flagged", False).fillna(False).astype(bool)
    # Ensure disposition column exists (nullable in schema)
    if "disposition" not in df.columns:
        df["disposition"] = None
    return dedupe_returns(df)
