-- 01_customers_products.sql
-- Dimension tables for customers and products.
-- Apply before 02_orders.sql.

BEGIN;

CREATE TABLE IF NOT EXISTS customers (
    customer_id        BIGINT PRIMARY KEY,
    email              TEXT,
    segment            TEXT NOT NULL,           -- 'new' | 'casual' | 'loyal' | 'vip'
    created_at         TIMESTAMP NOT NULL,
    lifetime_value     NUMERIC(12,2) DEFAULT 0,
    risk_score         NUMERIC(4,3)             -- customer-level fraud risk, 0.000-1.000
);

CREATE INDEX IF NOT EXISTS idx_customers_segment ON customers(segment);

CREATE TABLE IF NOT EXISTS products (
    product_id         BIGINT PRIMARY KEY,
    sku                TEXT NOT NULL UNIQUE,
    category           TEXT NOT NULL,
    subcategory        TEXT,
    unit_price         NUMERIC(10,2) NOT NULL,
    return_window_days INT DEFAULT 30
);

CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);

COMMIT;
