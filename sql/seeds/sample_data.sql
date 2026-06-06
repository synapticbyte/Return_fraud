-- sample_data.sql
-- Tiny dev seed. For realistic volume, run python/scripts/generate_dummy_data.py.
-- Safe to re-run: uses fixed IDs and ON CONFLICT DO NOTHING.

BEGIN;

INSERT INTO customers (customer_id, email, segment, created_at, lifetime_value, risk_score) VALUES
    (1, 'alice@example.com',  'vip',    '2023-01-15',  4200.00, 0.02),
    (2, 'bob@example.com',    'loyal',  '2023-03-22',  1850.00, 0.05),
    (3, 'carol@example.com',  'casual', '2024-06-01',   120.00, 0.41),
    (4, 'dan@example.com',    'new',    '2025-11-10',    45.00, 0.78)
ON CONFLICT (customer_id) DO NOTHING;

INSERT INTO products (product_id, sku, category, subcategory, unit_price, return_window_days) VALUES
    (101, 'APP-TEE-001', 'apparel',   'tops',     29.99, 30),
    (102, 'APP-JEA-002', 'apparel',   'bottoms',  79.99, 30),
    (103, 'ELE-PHN-003', 'electronics','phones',  899.00, 14),
    (104, 'HOM-LAM-004', 'home',      'lighting',  54.50, 60)
ON CONFLICT (product_id) DO NOTHING;

INSERT INTO orders (order_id, customer_id, order_date, channel, total_amount, shipping_postal_code) VALUES
    (1001, 1, '2025-10-01', 'web',   29.99, '94110'),
    (1002, 2, '2025-10-15', 'mobile', 79.99, '10001'),
    (1003, 3, '2025-12-20', 'bopis', 899.00, '60601'),
    (1004, 4, '2025-12-22', 'web',    54.50, '94110')
ON CONFLICT (order_id) DO NOTHING;

INSERT INTO order_items (order_item_id, order_id, product_id, quantity, unit_price, discount_amount) VALUES
    (5001, 1001, 101, 1, 29.99, 0),
    (5002, 1002, 102, 1, 79.99, 0),
    (5003, 1003, 103, 1, 899.00, 0),
    (5004, 1004, 104, 1, 54.50, 0)
ON CONFLICT (order_item_id) DO NOTHING;

INSERT INTO returns (return_id, order_item_id, customer_id, return_date, return_reason, return_channel,
                     condition_received, disposition, refund_amount, restocking_fee, processing_cost,
                     recovered_value, cycle_time_hours, fraud_flagged) VALUES
    (9001, 5001, 1, '2025-10-05', 'changed_mind',     'mail',     'new_unopened',  'restock',  29.99, 0, 3.50, 26.49, 72, FALSE),
    (9002, 5002, 2, '2025-10-25', 'wrong_size',       'in_store', 'opened_unused', 'restock',  79.99, 0, 5.00, 74.99,  6, FALSE),
    (9003, 5003, 3, '2025-12-22', 'not_as_described', 'pickup',   'used',          'refurbish', 899.00, 0, 35.00, 600.00, 48, FALSE),
    (9004, 5004, 4, '2025-12-23', 'defective',        'mail',     'damaged',       'destroy',  54.50, 0, 8.00, 0, 96, TRUE)
ON CONFLICT (return_id) DO NOTHING;

COMMIT;
