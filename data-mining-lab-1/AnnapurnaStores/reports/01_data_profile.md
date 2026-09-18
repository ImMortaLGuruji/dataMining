# Annapurna Stores — Data Profile Report (`01_data_profile.md`)

## 1. Executive Summary
This report documents the exhaustive profiling of the raw dataset provided for Annapurna Stores under `/exam/data`. All figures reported here are measured directly from the supplied data without assumptions or estimations.

---

## 2. Source Inventory & File Count
- **Total sales files discovered**: `4,457`
- **File format distribution**: `4,457` CSV files (100% CSV, 0 Parquet)
- **Directory**: `exam/data/sales/`
- **Date range covered**: `2024-01-01` to `2024-12-31` (Trading year 2024)
- **Stores represented**: 12 stores (`S01` through `S12`)

### Store File Distribution
| Store ID | Store Name | File Count |
| :--- | :--- | :--- |
| `S01` | Annapurna Jayanagar | 370 |
| `S02` | Annapurna Koramangala | 372 |
| `S03` | Annapurna T Nagar | 371 |
| `S04` | Annapurna Kukatpally | 378 |
| `S05` | Annapurna Kochi Marine | 369 |
| `S06` | Annapurna Andheri West | 372 |
| `S07` | Annapurna Baner | 370 |
| `S08` | Annapurna Satellite | 368 |
| `S09` | Annapurna Vaishali | 374 |
| `S10` | Annapurna Rajouri Garden | 374 |
| `S11` | Annapurna Gomti Nagar | 367 |
| `S12` | Annapurna Salt Lake | 372 |
| **Total** | | **4,457** |

---

## 3. Dialects & Schemas
The RetailEdge POS billing vendor exports data under three distinct till generation formats:

### Dialect 1: Stores S01–S05
- **Delimiter**: Comma (`,`)
- **Header**: `bill_no,line_no,product_code,qty,unit_price,line_type,ts`
- **Timestamp**: ISO-8601 string (`YYYY-MM-DDTHH:MM:SS`)
- **Encoding**: Standard UTF-8

### Dialect 2: Stores S06–S09
- **Delimiter**: Semicolon (`;`)
- **Header**: `bill_no;line_no;item_code;quantity;rate;type;txn_time`
- **Timestamp**: Custom European/Indian format (`DD-MM-YYYY HH:MM:SS`)
- **Column Aliases**: `item_code` -> `product_code`, `quantity` -> `qty`, `rate` -> `unit_price`, `type` -> `line_type`

### Dialect 3: Stores S10–S12
- **Delimiter**: Comma (`,`) with leading **UTF-8 Byte Order Mark (BOM)**
- **Header**: `ts,bill_no,line_no,line_type,product_code,unit_price,qty`
- **Timestamp**: Unix epoch timestamp in UTC (seconds since 1970-01-01)
- **Column Ordering**: Altered ordering with `ts` first and `qty` last

---

## 4. Row Counts & Duplicate Analysis
- **Total raw rows across all 4,457 files**: `1,137,585` rows
- **Duplicate rows encountered from re-sends**: `16,661` rows
- **Unique business lines `(bill_no, line_no)`**: `1,120,924` rows
- **Conflicting duplicates**: `0` (100% of re-sent lines are byte-identical copies)

### Re-send Breakdown:
- **Original trading day files**: 4,389 files
- **Full re-sends (`__R1`)**: 60 files
- **Partial re-sends (`__R2` or interrupted mid-roll exports)**: 8 files
- **Deduplication Strategy**: Business key uniqueness constraint on `(bill_no, line_no)`. The newest file strategy cannot be used because partial re-sends contain only a subset of the day's bills.

---

## 5. Line-Type Distribution & Revenue Semantics
The POS writes both item-level details and bill-level summary rows into the same file:

| Line Type | Raw Count | Unique Count | Counts as Revenue? | Explanation |
| :--- | :--- | :--- | :--- | :--- |
| `SALE` | 756,943 | 745,860 | **Yes (+)** | Item purchased, positive quantity |
| `DISCOUNT` | 22,942 | 22,603 | **Yes (-)** | Bill-level promotional discount, negative price |
| `RETURN` | 16,370 | 16,161 | **Yes (-)** | Customer item return, negative quantity |
| `VOID` | 4,952 | 4,892 | **Yes (net 0)** | Cancels corresponding item line on aborted bill |
| `TAX` | 168,189 | 165,704 | **No** | GST tax component (finance excludes GST) |
| `TENDER` | 168,189 | 165,704 | **No** | Total bill payment amount (items - disc + tax) |
| **Total** | **1,137,585** | **1,120,924** | | **Revenue rows: 789,516** |

> [!CAUTION]
> **The October Double-Counting Trap**:
> `TENDER` is the bill total written as a row in the same file. Summing all rows counts each bill roughly twice and includes GST tax. Filtering `line_type IN ('SALE', 'DISCOUNT', 'RETURN', 'VOID')` strictly resolves the true net revenue.

---

## 6. Product-Code Reuse
- Total product rows in `masters.sql`: 1,224
- Unique `product_code` values: 1,200
- **Reissued product codes**: Exactly `24` product codes were retired on `2024-05-31` (`valid_to = '2024-05-31'`, `is_current = FALSE`) and reissued on `2024-06-01` (`valid_from = '2024-06-01'`, `is_current = TRUE`) to completely different products in different categories.
- Joining on `product_code` alone results in Cartesian duplicates. The join must include `sale_date BETWEEN valid_from AND valid_to` to resolve the unambiguous surrogate key `product_sk`.

---

## 7. Data Quality Findings & Known Gaps
1. **Pune Store (S07) Lost Days**: Pune suffered a till server failure on July 9, 10, and 11, 2024. Files `SALES_S07_20240709`, `SALES_S07_20240710`, and `SALES_S07_20240711` do not exist in the export folder. Finance holds these numbers from phoned-in manual totals.
2. **Business Date vs. Calendar Timestamp**: Bills rung up past midnight (between 00:00 and 01:30) have timestamps on the following calendar day, but belong to the business day named in the file contract (`SALES_<store>_<YYYYMMDD>`). The filename date governs analytical date attribution.
