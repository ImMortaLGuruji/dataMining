# Annapurna Stores — Historical Pricing Report (`05_historical_pricing.md`)

## 1. Problem Context
Supermarket products experience periodic price revisions due to inflation, supplier renegotiations, and promotional pricing. The billing vendor noted that store tills occasionally run with outdated price lists (approx. 1 in 70 transactions). Furthermore, historical revenue reports must reflect the prices that were officially in effect during that reporting period, rather than current prices or uncalibrated printed prices.

---

## 2. Price Revision Semantics & Temporal Join
The operational database provides `price_revisions` containing `4,320` historical price brackets:
- `revision_id`: Primary key
- `product_sk`: Surrogate key of the product
- `mrp`: Maximum Retail Price
- `selling_price`: Authoritative selling price
- `effective_from`: Start date of price bracket
- `effective_to`: End date of price bracket (`9999-12-31` for active price)

### Temporal Join Logic:
A transaction on `sale_date` resolves to the authoritative price via:
```sql
JOIN price_revisions pr
  ON p.product_key = pr.product_sk
 AND s.sale_date >= pr.effective_from
 AND s.sale_date <= pr.effective_to
```
This avoids current-price leakage (joining only on product code and using today's price) and provides reproducible historical pricing.

---

## 3. Parameterized Query Demonstration
The same canonical query structure was evaluated across two distinct reporting windows without modifying the query transformation logic:

### Query A: March 2024
- **Parameters**: `sale_date >= '2024-03-01' AND sale_date < '2024-04-01'`
- **Total Bills**: `13,602`
- **Sales Lines**: `64,507`
- **Till Printed Revenue**: `41,971,649.09 INR`
- **Authoritative Catalog Revenue**: `41,971,885.88 INR`
- **Net Revenue**: `41,971,649.09 INR`

### Query B: Recent Two-Month Period (November – December 2024)
- **Parameters**: `sale_date >= '2024-11-01' AND sale_date < '2025-01-01'`
- **November 2024**: `16,089` bills, `76,712` lines, Net Revenue: `51,583,838.47 INR`
- **December 2024**: `15,605` bills, `74,511` lines, Net Revenue: `50,745,259.48 INR`

---

## 4. Observed Price Evolution
Comparing effective prices between March 2024 and November 2024 reveals substantial revisions:
| Product Code | Product Name | March Price (INR) | Nov Price (INR) | Price Delta (INR) |
| :--- | :--- | :--- | :--- | :--- |
| `P106486` | Mamypoko Diapers XL | 1,342.57 | 1,837.06 | +494.49 |
| `P102139` | Dhara Mustard Oil 5L | 1,231.60 | 1,710.06 | +478.46 |
| `P100035` | Huggies Diapers Small | 1,456.57 | 1,810.38 | +353.81 |
| `P104469` | Huggies Baby Wipes XL | 1,383.23 | 1,631.11 | +247.88 |
| `P102181` | 24 Mantra Poha 5kg | 1,394.08 | 1,615.15 | +221.07 |

- Evidence File: `AnnapurnaStores/evidence/outputs/historical-pricing.txt`
- Evaluation Script: `AnnapurnaStores/ingestion/scripts/run_historical_pricing.py`
