# Annapurna Stores — Finance Reconciliation Report (`07_reconciliation.md`)

## 1. Reconciliation Overview
The analytical pipeline's calculated monthly net revenue was compared directly against the official financial sign-off target (`/exam/data/finance_monthly.csv`, signed off by A. Krishnan, Finance Controller).

---

## 2. Monthly Comparison Matrix
| Month | Pipeline Revenue (INR) | Finance Revenue (INR) | Difference (INR) | Variance % | Classification |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **2024-01** | 38,446,071.33 | 38,446,071.33 | **0.00** | 0.0000% | **Exact Match** |
| **2024-02** | 34,887,085.55 | 34,887,085.55 | **0.00** | 0.0000% | **Exact Match** |
| **2024-03** | 41,971,649.09 | 42,457,899.09 | **-486,250.00** | -1.1453% | **Scope Difference** |
| **2024-04** | 37,958,457.37 | 37,958,457.37 | **0.00** | 0.0000% | **Exact Match** |
| **2024-05** | 41,764,716.40 | 41,764,716.40 | **0.00** | 0.0000% | **Exact Match** |
| **2024-06** | 38,987,082.82 | 38,987,082.82 | **0.00** | 0.0000% | **Exact Match** |
| **2024-07** | 40,295,160.11 | 40,527,291.81 | **-232,131.70** | -0.5728% | **Source Data Issue** |
| **2024-08** | 45,252,181.75 | 45,252,181.75 | **0.00** | 0.0000% | **Exact Match** |
| **2024-09** | 44,615,037.46 | 44,615,037.46 | **0.00** | 0.0000% | **Exact Match** |
| **2024-10** | 56,359,195.92 | 56,359,195.92 | **0.00** | 0.0000% | **Exact Match** |
| **2024-11** | 51,583,838.47 | 51,583,838.47 | **0.00** | 0.0000% | **Exact Match** |
| **2024-12** | 50,745,259.48 | 50,745,209.00 | **+50.48** | +0.0001% | **Definition Difference** |

---

## 3. Root Cause Analysis for Differing Months

### Month 1: March 2024 (-486,250.00 INR)
- **Classification**: **Scope Difference**
- **Root Cause**: The operational till exports represent retail POS till transactions. In March 2024, finance included an institutional bulk corporate order invoiced offline directly from headquarters (`march_bulk_invoice = 486,250.00 INR`).
- **Proof**: `41,971,649.09 (till revenue) + 486,250.00 (bulk order) = 42,457,899.09 INR (finance total)`.
- **Finance Communication**: "The retail data platform captures 100% of in-store POS transactions. The 486,250.00 INR variance corresponds precisely to offline institutional Invoice #CORP-2024-03. To achieve parity, an offline enterprise invoice stream should be ingested into the warehouse."

### Month 2: July 2024 (-232,131.70 INR)
- **Classification**: **Source Data Issue**
- **Root Cause**: Pune Baner (`S07`) experienced an operational till server outage between July 9 and July 11, 2024. Export files `SALES_S07_20240709`, `SALES_S07_20240710`, and `SALES_S07_20240711` were never generated. Finance holds these numbers because the branch manager phoned in daily cash register tallies.
- **Proof**: Total revenue for the existing July export files equals exactly `40,295,160.11 INR`. Adding the phoned-in Pune sales of `232,131.70 INR` equals finance's signed-off `40,527,291.81 INR`.
- **Finance Communication**: "Digital export files for Pune S07 on July 9–11 do not exist due to a local hardware failure. The missing 232,131.70 INR represents manual ledger tallies. We recommend creating an audit adjustments table in the warehouse for ledger entries."

### Month 3: December 2024 (+50.48 INR)
- **Classification**: **Revenue Definition Difference**
- **Root Cause**: Finance rounds each customer bill total to the nearest whole rupee before accounting for monthly revenue. In contrast, the data warehouse preserves exact decimal sums (`ROUND(SUM(qty * unit_price), 2)`). Across 15,605 customer bills in December, fractional paisa rounding differences accumulated to `+50.48 INR` (a negligible 0.000099% variance).
- **Proof**: Rounding individual bill totals in the warehouse reproduces `50,745,209.00 INR` with 0.00 discrepancy.
- **Finance Communication**: "The pipeline and finance match within 0.0001%. The 50.48 INR difference is caused by bill-level rupee truncation. The data warehouse preserves decimal precision. An optional view `v_finance_rounded_revenue` can be supplied to simulate legacy rupee truncation."

---

## 4. Evidence Traceability
- Reconciliation CSV: `AnnapurnaStores/evidence/outputs/reconciliation.csv`
- Script: `AnnapurnaStores/ingestion/scripts/reconcile_finance.py`
