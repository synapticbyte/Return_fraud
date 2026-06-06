# Tableau workbooks

This directory holds the analyst-facing dashboards. Workbook files (`.twb` / `.twbx`) are binary and **not** stored in git — they live in the team's shared Tableau environment.

## Connection rule

**All workbooks connect to views, never to base tables.** The Tableau data source for any workbook should be one or more of:

| View                          | Purpose                                                   |
|-------------------------------|-----------------------------------------------------------|
| `v_monthly_return_metrics`    | Headline KPIs: volume, refunds, fraud rate, recovery.     |
| `v_return_reasons_by_category`| Return reasons broken down by category and month.         |
| `v_disposition_outcomes`      | Net value recovered per (category, disposition).          |
| `v_customer_return_summary`   | Customer-level lifetime return behavior.                  |
| `v_high_risk_returns`         | Returns flagged as fraud or scoring above 0.7.            |

Base tables (`returns`, `customers`, `fraud_signals`, etc.) may change schema during development. Pointing dashboards at views insulates them from churn.

## Workbook map

| Workbook                | Primary view                | Audience                |
|-------------------------|-----------------------------|-------------------------|
| Reverse Logistics Ops   | `v_disposition_outcomes`    | Ops / Supply Chain team |
| Fraud Investigation     | `v_high_risk_returns` + `fraud_signals` | Loss-prevention analysts |
| Customer Health         | `v_customer_return_summary`| CX / Marketing          |
| Monthly Returns Review  | `v_monthly_return_metrics`  | Executive              |

## Refresh cadence

- Daily at 06:00 UTC for everything except `fraud_signals`, which is hourly.
- `fraud_score` on `returns` is overwritten by `score_returns.py` — refresh workbooks after the model run completes.

## Adding a new workbook

1. Add a new view in `sql/schema/04_views.sql` if needed.
2. Build the workbook against that view (not base tables).
3. Add a row to the workbook map above.
4. Document any new calculations or filters in this file.
