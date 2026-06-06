"""Idempotent loads into the warehouse.

Writes go through pandas.DataFrame.to_sql with `if_exists='append'`.
For tables that need upsert semantics, use the `upsert_*` helpers below which
rely on a unique key and `INSERT ... ON CONFLICT DO UPDATE`.
"""

from __future__ import annotations

import logging
from typing import Iterable

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

log = logging.getLogger(__name__)

UPSERT_TEMPLATES = {
    "customers": """
        INSERT INTO customers
            (customer_id, email, segment, created_at, lifetime_value, risk_score)
        VALUES
            (:customer_id, :email, :segment, :created_at, :lifetime_value, :risk_score)
        ON CONFLICT (customer_id) DO UPDATE SET
            email          = EXCLUDED.email,
            segment        = EXCLUDED.segment,
            lifetime_value = EXCLUDED.lifetime_value,
            risk_score     = EXCLUDED.risk_score
    """,
    "products": """
        INSERT INTO products
            (product_id, sku, category, subcategory, unit_price, return_window_days)
        VALUES
            (:product_id, :sku, :category, :subcategory, :unit_price, :return_window_days)
        ON CONFLICT (product_id) DO UPDATE SET
            sku                = EXCLUDED.sku,
            category           = EXCLUDED.category,
            subcategory        = EXCLUDED.subcategory,
            unit_price         = EXCLUDED.unit_price,
            return_window_days = EXCLUDED.return_window_days
    """,
    "orders": """
        INSERT INTO orders
            (order_id, customer_id, order_date, channel, total_amount, shipping_postal_code)
        VALUES
            (:order_id, :customer_id, :order_date, :channel, :total_amount, :shipping_postal_code)
        ON CONFLICT (order_id) DO UPDATE SET
            customer_id            = EXCLUDED.customer_id,
            order_date             = EXCLUDED.order_date,
            channel                = EXCLUDED.channel,
            total_amount          = EXCLUDED.total_amount,
            shipping_postal_code  = EXCLUDED.shipping_postal_code
    """,
    "order_items": """
        INSERT INTO order_items
            (order_item_id, order_id, product_id, quantity, unit_price, discount_amount)
        VALUES
            (:order_item_id, :order_id, :product_id, :quantity, :unit_price, :discount_amount)
        ON CONFLICT (order_item_id) DO UPDATE SET
            order_id         = EXCLUDED.order_id,
            product_id       = EXCLUDED.product_id,
            quantity         = EXCLUDED.quantity,
            unit_price       = EXCLUDED.unit_price,
            discount_amount  = EXCLUDED.discount_amount
    """,
    "returns": """
        INSERT INTO returns
            (return_id, order_item_id, customer_id, return_date, return_reason,
             return_channel, condition_received, disposition, refund_amount, restocking_fee,
             processing_cost, recovered_value, cycle_time_hours, fraud_flagged)
        VALUES
            (:return_id, :order_item_id, :customer_id, :return_date, :return_reason,
             :return_channel, :condition_received, :disposition, :refund_amount, :restocking_fee,
             :processing_cost, :recovered_value, :cycle_time_hours, :fraud_flagged)
        ON CONFLICT (return_id) DO UPDATE SET
            condition_received = EXCLUDED.condition_received,
            disposition        = EXCLUDED.disposition,
            refund_amount      = EXCLUDED.refund_amount,
            processing_cost    = EXCLUDED.processing_cost,
            recovered_value    = EXCLUDED.recovered_value,
            cycle_time_hours   = EXCLUDED.cycle_time_hours,
            fraud_flagged      = EXCLUDED.fraud_flagged
    """,
}


def _chunks(rows: list[dict], size: int) -> Iterable[list[dict]]:
    for i in range(0, len(rows), size):
        yield rows[i : i + size]


def upsert(engine: Engine, table: str, df: pd.DataFrame, chunk_size: int = 1000) -> int:
    """Upsert a DataFrame into `table` using the project's ON CONFLICT templates.

    Returns the number of rows written.
    """
    if table not in UPSERT_TEMPLATES:
        raise ValueError(f"No upsert template registered for table '{table}'")
    rows = df.to_dict(orient="records")
    written = 0
    with engine.begin() as conn:
        for batch in _chunks(rows, chunk_size):
            conn.execute(text(UPSERT_TEMPLATES[table]), batch)
            written += len(batch)
    log.info("Upserted %d rows into %s", written, table)
    return written
