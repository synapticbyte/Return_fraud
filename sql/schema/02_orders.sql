-- 02_orders.sql
-- Order header and line-item tables.
-- Apply after 01_customers_products.sql, before 03_returns.sql.

BEGIN;

CREATE TABLE IF NOT EXISTS orders (
    order_id              BIGINT PRIMARY KEY,
    customer_id           BIGINT NOT NULL REFERENCES customers(customer_id),
    order_date            TIMESTAMP NOT NULL,
    channel               TEXT NOT NULL,        -- 'web' | 'mobile' | 'bopis' | 'store'
    total_amount          NUMERIC(12,2) NOT NULL,
    shipping_postal_code  TEXT
);

CREATE INDEX IF NOT EXISTS idx_orders_customer    ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_order_date  ON orders(order_date);

CREATE TABLE IF NOT EXISTS order_items (
    order_item_id     BIGINT PRIMARY KEY,
    order_id          BIGINT NOT NULL REFERENCES orders(order_id),
    product_id        BIGINT NOT NULL REFERENCES products(product_id),
    quantity          INT NOT NULL,
    unit_price        NUMERIC(10,2) NOT NULL,
    discount_amount   NUMERIC(10,2) DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_order_items_order   ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product ON order_items(product_id);

COMMIT;
