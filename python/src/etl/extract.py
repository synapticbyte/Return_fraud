"""Read raw returns/orders/customers CSVs from data/raw/ into DataFrames.

Each function returns a typed DataFrame. No business logic here — just IO.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ..config import RAW_DIR

REQUIRED_RETURN_COLUMNS = [
    "return_id",
    "order_item_id",
    "customer_id",
    "return_date",
    "return_reason",
    "return_channel",
    "condition_received",
    "refund_amount",
]


def read_returns(path: Path | None = None) -> pd.DataFrame:
    """Read returns.csv. Raises if required columns are missing."""
    csv_path = path or (RAW_DIR / "returns.csv")
    df = pd.read_csv(csv_path, parse_dates=["return_date"])
    missing = set(REQUIRED_RETURN_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"returns.csv missing required columns: {sorted(missing)}")
    return df


def read_customers(path: Path | None = None) -> pd.DataFrame:
    return pd.read_csv(path or (RAW_DIR / "customers.csv"), parse_dates=["created_at"])


def read_orders(path: Path | None = None) -> pd.DataFrame:
    return pd.read_csv(path or (RAW_DIR / "orders.csv"), parse_dates=["order_date"])


def read_order_items(path: Path | None = None) -> pd.DataFrame:
    return pd.read_csv(path or (RAW_DIR / "order_items.csv"))


def read_products(path: Path | None = None) -> pd.DataFrame:
    return pd.read_csv(path or (RAW_DIR / "products.csv"))
