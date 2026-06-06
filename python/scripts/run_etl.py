"""CLI entrypoint: read CSVs from data/raw/ and upsert into the warehouse."""

from __future__ import annotations

import logging

from src.config import RAW_DIR, configure_logging
from src.db import get_engine
from src.etl import extract, load, transform

log = logging.getLogger(__name__)


def main() -> None:
    configure_logging()
    log.info("Reading raw inputs from %s", RAW_DIR)

    customers = extract.read_customers()
    products = extract.read_products()
    orders = extract.read_orders()
    order_items = extract.read_order_items()
    returns_raw = extract.read_returns()
    returns = transform.transform_returns(returns_raw)

    engine = get_engine()
    # Dimensions first so the returns fact table FKs resolve.
    load.upsert(engine, "customers", customers)
    load.upsert(engine, "products", products)
    # Make fact/dimension loads idempotent to avoid primary-key duplication when rerunning ETL.
    load.upsert(engine, "orders", orders)
    load.upsert(engine, "order_items", order_items)
    load.upsert(engine, "returns", returns)
    log.info("ETL complete")


if __name__ == "__main__":
    main()
