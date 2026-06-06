-- disposition_optimization.sql
-- Net value recovered per disposition per category.
-- Negative net_value = we're losing money on returns in that bucket → investigate routing.

SELECT
    p.category,
    r.disposition,
    COUNT(*)                                AS units,
    SUM(r.recovered_value)                  AS recovered_revenue,
    SUM(r.processing_cost)                  AS processing_cost,
    SUM(r.recovered_value) - SUM(r.processing_cost) AS net_value,
    AVG(r.cycle_time_hours)                 AS avg_cycle_hours
FROM returns r
JOIN order_items oi ON oi.order_item_id = r.order_item_id
JOIN products    p  ON p.product_id     = oi.product_id
WHERE r.disposition IS NOT NULL
  AND r.return_date >= DATE_TRUNC('month', NOW() - INTERVAL '6 months')
GROUP BY p.category, r.disposition
ORDER BY p.category, net_value DESC;
