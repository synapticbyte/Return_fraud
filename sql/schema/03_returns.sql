-- 03_returns.sql
-- Return fact table and fraud-signal audit trail.
-- Apply after 02_orders.sql. `returns.fraud_score` is written by score_returns.py.

BEGIN;

CREATE TABLE IF NOT EXISTS returns (
    return_id          BIGINT PRIMARY KEY,
    order_item_id      BIGINT NOT NULL REFERENCES order_items(order_item_id),
    customer_id        BIGINT NOT NULL REFERENCES customers(customer_id),
    return_date        TIMESTAMP NOT NULL,
    return_reason      TEXT NOT NULL,         -- 'defective' | 'wrong_size' | 'not_as_described' | 'changed_mind' | 'late_delivery' | 'duplicate' | 'other'
    return_channel     TEXT NOT NULL,         -- 'mail' | 'in_store' | 'pickup'
    condition_received TEXT,                  -- 'new_unopened' | 'opened_unused' | 'used' | 'damaged' | 'missing_parts'
    disposition        TEXT,                  -- 'restock' | 'refurbish' | 'liquidate' | 'donate' | 'destroy'
    refund_amount      NUMERIC(10,2) NOT NULL,
    restocking_fee     NUMERIC(10,2) DEFAULT 0,
    processing_cost    NUMERIC(10,2) DEFAULT 0,
    recovered_value    NUMERIC(10,2) DEFAULT 0,
    cycle_time_hours   INT,                   -- from return initiation to disposition
    fraud_flagged      BOOLEAN DEFAULT FALSE,
    fraud_score        NUMERIC(4,3),          -- written by python/scripts/score_returns.py
    created_at         TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_returns_customer     ON returns(customer_id);
CREATE INDEX IF NOT EXISTS idx_returns_return_date  ON returns(return_date);
CREATE INDEX IF NOT EXISTS idx_returns_fraud        ON returns(fraud_flagged) WHERE fraud_flagged = TRUE;

-- Append-only signal log. Multiple signals per return are expected and useful.
CREATE TABLE IF NOT EXISTS fraud_signals (
    signal_id      BIGSERIAL PRIMARY KEY,
    return_id      BIGINT NOT NULL REFERENCES returns(return_id),
    signal_type    TEXT NOT NULL,    -- 'serial_returner' | 'wardrobing' | 'bopis_not_returned' | 'time_anomaly' | 'value_mismatch' | 'condition_mismatch'
    severity       TEXT NOT NULL,    -- 'low' | 'medium' | 'high'
    score          NUMERIC(4,3) NOT NULL,
    evidence       JSONB,            -- raw numbers behind the signal (counts, timestamps, ratios)
    model_version  TEXT,
    created_at     TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fraud_signals_return ON fraud_signals(return_id);
CREATE INDEX IF NOT EXISTS idx_fraud_signals_type   ON fraud_signals(signal_type);

COMMIT;
