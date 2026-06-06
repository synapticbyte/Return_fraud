-- return_reasons_breakdown.sql
-- "What's coming back and why?" — break returns down by reason, category, and month.
-- Use to spot categories where a specific reason dominates (e.g. sizing issues in apparel).

SELECT
    DATE_TRUNC('month', r.return_date) AS month,
    p.category,
    r.return_reason,
    COUNT(*)                           AS return_count,
    SUM(r.refund_amount)               AS refund_dollars,
    AVG(r.cycle_time_hours)            AS avg_cycle_hours
FROM returns r
JOIN order_items oi ON oi.order_item_id = r.order_item_id
JOIN products    p  ON p.product_id     = oi.product_id
WHERE r.return_date >= DATE_TRUNC('month', NOW() - INTERVAL '12 months')
GROUP BY 1, 2, 3
ORDER BY 1 DESC, return_count DESC;
