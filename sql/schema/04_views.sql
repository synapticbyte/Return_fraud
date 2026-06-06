-- 04_views.sql
-- KPI views. Tableau reads ONLY from these — never from base tables.

-- Monthly headline metrics: return volume, refund dollars, fraud rate, recovery.
CREATE OR REPLACE VIEW v_monthly_return_metrics AS
SELECT
    DATE_TRUNC('month', r.return_date)                         AS month,
    COUNT(*)                                                   AS total_returns,
    SUM(r.refund_amount)                                       AS total_refunds,
    AVG(r.cycle_time_hours)                                    AS avg_cycle_hours,
    SUM(CASE WHEN r.fraud_flagged THEN 1 ELSE 0 END)::NUMERIC
        / NULLIF(COUNT(*), 0)                                  AS fraud_rate,
    SUM(r.recovered_value)                                     AS total_recovered,
    SUM(r.processing_cost)                                     AS total_processing_cost
FROM returns r
GROUP BY 1;

-- Return reasons broken down by category — for the "why are we getting these back?" view.
CREATE OR REPLACE VIEW v_return_reasons_by_category AS
SELECT
    p.category,
    r.return_reason,
    DATE_TRUNC('month', r.return_date) AS month,
    COUNT(*)                           AS return_count,
    SUM(r.refund_amount)               AS refund_amount
FROM returns r
JOIN order_items oi ON oi.order_item_id = r.order_item_id
JOIN products    p  ON p.product_id     = oi.product_id
GROUP BY 1, 2, 3;

-- Disposition outcomes — for reverse-logistics optimization.
-- Shows where value is being recovered vs. destroyed, by category.
CREATE OR REPLACE VIEW v_disposition_outcomes AS
SELECT
    p.category,
    r.disposition,
    COUNT(*)                                AS disposition_count,
    SUM(r.recovered_value)                  AS recovered_value,
    SUM(r.processing_cost)                  AS processing_cost,
    SUM(r.recovered_value) - SUM(r.processing_cost) AS net_value
FROM returns r
JOIN order_items oi ON oi.order_item_id = r.order_item_id
JOIN products    p  ON p.product_id     = oi.product_id
WHERE r.disposition IS NOT NULL
GROUP BY 1, 2;

-- Customer-level return behavior — fuel for serial-returner fraud signals.
CREATE OR REPLACE VIEW v_customer_return_summary AS
SELECT
    c.customer_id,
    c.segment,
    COUNT(r.return_id)                                       AS lifetime_returns,
    SUM(r.refund_amount)                                     AS lifetime_refunds,
    SUM(CASE WHEN r.fraud_flagged THEN 1 ELSE 0 END)         AS flagged_returns,
    MAX(r.return_date)                                       AS last_return_date
FROM customers c
LEFT JOIN returns r ON r.customer_id = c.customer_id
GROUP BY c.customer_id, c.segment;

-- High-risk returns for the fraud-investigation dashboard.
CREATE OR REPLACE VIEW v_high_risk_returns AS
SELECT
    r.return_id,
    r.return_date,
    r.customer_id,
    c.segment,
    r.refund_amount,
    r.return_reason,
    r.return_channel,
    r.fraud_score,
    r.fraud_flagged
FROM returns r
JOIN customers c ON c.customer_id = r.customer_id
WHERE r.fraud_flagged = TRUE
   OR r.fraud_score >= 0.7;
