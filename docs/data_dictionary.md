# Data dictionary

## customers

| Column         | Type            | Description                                                |
|----------------|-----------------|------------------------------------------------------------|
| customer_id    | BIGINT PK       | Surrogate key, source system customer identifier.          |
| email          | TEXT            | Customer email; may be null for guest checkouts.           |
| segment        | TEXT            | `new` / `casual` / `loyal` / `vip`.                        |
| created_at     | TIMESTAMP       | First order date.                                          |
| lifetime_value | NUMERIC(12,2)   | Sum of net order revenue, all-time.                        |
| risk_score     | NUMERIC(4,3)    | 0.000–1.000 customer-level fraud risk, recomputed nightly. |

## products

| Column             | Type          | Description                                       |
|--------------------|---------------|---------------------------------------------------|
| product_id         | BIGINT PK     |                                                   |
| sku                | TEXT UNIQUE   | Stock-keeping unit, business-facing identifier.   |
| category           | TEXT          | `apparel` / `electronics` / `home` / `beauty`.   |
| subcategory        | TEXT          | Free-form within category.                        |
| unit_price         | NUMERIC(10,2) | List price at time of catalog snapshot.           |
| return_window_days | INT           | Days after delivery a return is accepted.         |

## orders

| Column                | Type          | Description                                    |
|-----------------------|---------------|------------------------------------------------|
| order_id              | BIGINT PK     |                                                |
| customer_id           | BIGINT FK     |                                                |
| order_date            | TIMESTAMP     |                                                |
| channel               | TEXT          | `web` / `mobile` / `bopis` / `store`.          |
| total_amount          | NUMERIC(12,2) | Sum of order_items.                            |
| shipping_postal_code  | TEXT          | Used for regional disposition routing.         |

## order_items

| Column          | Type          | Description                                  |
|-----------------|---------------|----------------------------------------------|
| order_item_id   | BIGINT PK     |                                              |
| order_id        | BIGINT FK     |                                              |
| product_id      | BIGINT FK     |                                              |
| quantity        | INT           |                                              |
| unit_price      | NUMERIC(10,2) | Price at time of order (after discount).     |
| discount_amount | NUMERIC(10,2) | Per-line discount applied.                   |

## returns

| Column              | Type          | Description                                                                          |
|---------------------|---------------|--------------------------------------------------------------------------------------|
| return_id           | BIGINT PK     |                                                                                      |
| order_item_id       | BIGINT FK     |                                                                                      |
| customer_id         | BIGINT FK     |                                                                                      |
| return_date         | TIMESTAMP     |                                                                                      |
| return_reason       | TEXT          | `defective` / `wrong_size` / `not_as_described` / `changed_mind` / `late_delivery` / `duplicate` / `other`. |
| return_channel      | TEXT          | `mail` / `in_store` / `pickup`.                                                      |
| condition_received  | TEXT          | `new_unopened` / `opened_unused` / `used` / `damaged` / `missing_parts`.             |
| disposition         | TEXT          | `restock` / `refurbish` / `liquidate` / `donate` / `destroy`.                        |
| refund_amount       | NUMERIC(10,2) |                                                                                      |
| restocking_fee      | NUMERIC(10,2) |                                                                                      |
| processing_cost     | NUMERIC(10,2) | Receiving + grading + routing.                                                       |
| recovered_value     | NUMERIC(10,2) | Resale or liquidation value of the returned unit.                                   |
| cycle_time_hours    | INT           | From `return_date` to disposition completion.                                        |
| fraud_flagged       | BOOLEAN       | Set by `score_returns.py` if score ≥ 0.7.                                            |
| fraud_score         | NUMERIC(4,3)  | 0.000–1.000, written by `score_returns.py`.                                          |
| created_at          | TIMESTAMP     | Row insert time.                                                                     |

## fraud_signals

Append-only log. Multiple rows per `return_id` are expected.

| Column        | Type          | Description                                                                              |
|---------------|---------------|------------------------------------------------------------------------------------------|
| signal_id     | BIGSERIAL PK  |                                                                                          |
| return_id     | BIGINT FK     |                                                                                          |
| signal_type   | TEXT          | `serial_returner` / `wardrobing` / `bopis_not_returned` / `time_anomaly` / `value_mismatch` / `condition_mismatch`. |
| severity      | TEXT          | `low` / `medium` / `high`.                                                               |
| score         | NUMERIC(4,3)  | Signal-level score.                                                                      |
| evidence      | JSONB         | Raw numbers behind the signal (counts, timestamps, ratios).                              |
| model_version | TEXT          | Versioning tag — `rules_v1` for the current rule-based detectors.                        |
| created_at    | TIMESTAMP     |                                                                                          |

## Signal taxonomy

- **serial_returner** — more than 5 returns in the trailing 90 days for the same `customer_id`.
- **wardrobing** — return filed 1–3 days after order with reason `changed_mind` or `not_as_described`.
- **bopis_not_returned** — BOPIS order where the pickup scan was logged but the return never arrived.
- **time_anomaly** — return logged between 23:00 and 04:00 local.
- **value_mismatch** — `refund_amount` exceeds the original `unit_price`.
- **condition_mismatch** — `condition_received` is worse than expected for an unopened-delivery return.

## KPI definitions

- **Return rate** — `COUNT(returns) / COUNT(order_items)` over a chosen window.
- **Fraud rate** — `SUM(fraud_flagged) / COUNT(*)` over `returns`.
- **Recovery rate** — `SUM(recovered_value) / SUM(refund_amount)`.
- **Net return cost** — `SUM(refund_amount + processing_cost - recovered_value)`.
- **Cycle time** — average of `cycle_time_hours` for returns with a non-null disposition.
