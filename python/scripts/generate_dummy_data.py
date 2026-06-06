"""Generate realistic-ish dummy data for dev.

Writes customers.csv, orders.csv, order_items.csv, returns.csv into
`data/raw/`. Idempotent: overwrites previous files. Use this to exercise the
ETL and training scripts without needing real upstream systems.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import RAW_DIR, configure_logging

N_CUSTOMERS = 500
N_ORDERS = 4000
N_RETURNS = 1200
FRAUD_RATE = 0.08

CATEGORIES = {
    "apparel": (("tops", "bottoms", "dresses"), (20.0, 90.0)),
    "electronics": (("phones", "laptops", "accessories"), (50.0, 1100.0)),
    "home": (("lighting", "kitchen", "decor"), (15.0, 250.0)),
    "beauty": (("skincare", "makeup", "fragrance"), (10.0, 120.0)),
}
RETURN_REASONS = ["defective", "wrong_size", "not_as_described", "changed_mind", "late_delivery", "duplicate"]
CHANNELS = ["web", "mobile", "bopis", "store"]
CONDITIONS = ["new_unopened", "opened_unused", "used", "damaged"]
DISPOSITIONS = ["restock", "refurbish", "liquidate", "donate", "destroy"]


def _make_products() -> pd.DataFrame:
    rows = []
    pid = 1000
    for cat, (subs, (lo, hi)) in CATEGORIES.items():
        for sub in subs:
            for _ in range(8):
                pid += 1
                rows.append(
                    {
                        "product_id": pid,
                        "sku": f"{cat[:3].upper()}-{sub[:3].upper()}-{pid:04d}",
                        "category": cat,
                        "subcategory": sub,
                        "unit_price": round(random.uniform(lo, hi), 2),
                        "return_window_days": random.choice([14, 30, 60]),
                    }
                )
    return pd.DataFrame(rows)


def _make_customers(products: pd.DataFrame) -> pd.DataFrame:
    base = datetime(2023, 1, 1)
    rows = []
    for cid in range(1, N_CUSTOMERS + 1):
        rows.append(
            {
                "customer_id": cid,
                "email": f"user{cid}@example.com",
                "segment": random.choices(["new", "casual", "loyal", "vip"], weights=[3, 5, 3, 1])[0],
                "created_at": base + timedelta(days=random.randint(0, 900)),
                "lifetime_value": round(random.uniform(0, 5000), 2),
                "risk_score": round(random.betavariate(2, 20), 3),
            }
        )
    return pd.DataFrame(rows)


def _make_orders_and_returns(products: pd.DataFrame, customers: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    orders = []
    items = []
    returns = []
    base = datetime(2024, 1, 1)
    end = datetime(2026, 1, 1)

    for oid in range(1000, 1000 + N_ORDERS):
        cust = customers.sample(1).iloc[0]
        order_dt = base + timedelta(days=random.randint(0, (end - base).days))
        channel = random.choices(CHANNELS, weights=[5, 4, 2, 2])[0]
        n_items = random.choices([1, 2, 3], weights=[7, 2, 1])[0]
        item_rows = []
        for _ in range(n_items):
            prod = products.sample(1).iloc[0]
            qty = random.choices([1, 2, 3], weights=[8, 1, 1])[0]
            item_rows.append(
                {
                    "order_item_id": len(items) + 1,
                    "order_id": oid,
                    "product_id": int(prod["product_id"]),
                    "quantity": qty,
                    "unit_price": float(prod["unit_price"]),
                    "discount_amount": 0.0,
                }
            )
        total = sum(r["quantity"] * r["unit_price"] for r in item_rows)
        orders.append(
            {
                "order_id": oid,
                "customer_id": int(cust["customer_id"]),
                "order_date": order_dt,
                "channel": channel,
                "total_amount": round(total, 2),
                "shipping_postal_code": f"{random.randint(10000, 99999)}",
            }
        )
        items.extend(item_rows)

        # Decide whether this order has a return
        if random.random() < 0.30:
            picked = random.choice(item_rows)
            is_fraud = random.random() < FRAUD_RATE
            days_to_return = random.randint(1, 7) if is_fraud else random.randint(2, 45)
            return_dt = order_dt + timedelta(days=days_to_return)
            if return_dt >= end:
                continue
            reason = "changed_mind" if not is_fraud else random.choice(["changed_mind", "not_as_described", "duplicate"])
            condition = "new_unopened" if not is_fraud else random.choices(
                ["opened_unused", "used", "damaged"], weights=[2, 3, 1]
            )[0]
            disp = "restock" if not is_fraud else random.choices(DISPOSITIONS, weights=[1, 1, 2, 1, 1])[0]
            refund = picked["unit_price"] * picked["quantity"]
            recovered = refund * (0.7 if disp == "restock" else 0.4 if disp == "refurbish" else 0.1)
            returns.append(
                {
                    "return_id": 9000 + len(returns) + 1,
                    "order_item_id": picked["order_item_id"],
                    "customer_id": int(cust["customer_id"]),
                    "return_date": return_dt,
                    "return_reason": reason,
                    "return_channel": random.choice(CHANNELS),
                    "condition_received": condition,
                    "disposition": disp,
                    "refund_amount": round(refund, 2),
                    "restocking_fee": 0.0,
                    "processing_cost": round(random.uniform(3, 25), 2),
                    "recovered_value": round(recovered, 2),
                    "cycle_time_hours": random.randint(6, 168),
                    "fraud_flagged": is_fraud,
                }
            )
    return pd.DataFrame(orders), pd.DataFrame(items), pd.DataFrame(returns)


def main() -> None:
    configure_logging()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    products = _make_products()
    customers = _make_customers(products)
    orders, items, returns = _make_orders_and_returns(products, customers)

    products.to_csv(RAW_DIR / "products.csv", index=False)
    customers.to_csv(RAW_DIR / "customers.csv", index=False)
    orders.to_csv(RAW_DIR / "orders.csv", index=False)
    items.to_csv(RAW_DIR / "order_items.csv", index=False)
    returns.to_csv(RAW_DIR / "returns.csv", index=False)
    print(
        f"Wrote {len(products)} products, {len(customers)} customers, "
        f"{len(orders)} orders, {len(items)} items, {len(returns)} returns to {RAW_DIR}"
    )


if __name__ == "__main__":
    main()
