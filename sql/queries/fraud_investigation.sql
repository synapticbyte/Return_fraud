-- fraud_investigation.sql
-- Pulls every signal behind a high-risk return so an analyst can investigate.
-- Run with a return_id parameter (replace :return_id at runtime, or use psql -v).

SELECT
    r.return_id,
    r.return_date,
    r.refund_amount,
    r.return_reason,
    r.return_channel,
    r.condition_received,
    r.fraud_score,
    fs.signal_type,
    fs.severity,
    fs.score    AS signal_score,
    fs.evidence
FROM returns r
LEFT JOIN fraud_signals fs ON fs.return_id = r.return_id
WHERE r.return_id = :return_id
ORDER BY fs.signal_type;
