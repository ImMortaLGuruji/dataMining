# Annapurna Stores — Final Engineering Report (`final_report.md`)

## 1. Executive Summary
This report presents the complete end-to-end data platform built for Annapurna Stores (Question 1 of LabExam1). The objective was to engineer a reproducible, cold-start, locally runnable data platform using Docker Compose, MinIO, PostgreSQL, and DuckDB to transform messy daily retail sales files into historically accurate revenue analytics that reconcile with financial records.

The platform was built and verified from a clean environment without cloud dependencies. Every numerical claim in this report is backed by reproducible commands, measured outputs, and execution evidence.

---

## 2. Problem Understanding
Annapurna Stores operates 12 supermarkets across India. The retail billing systems produce daily transaction files in a shared export location. Over trading year 2024, ~4,457 files were generated across three distinct till software generations. 

Key technical challenges addressed:
1. **Dialect Heterogeneity**: Varying delimiters (comma vs. semicolon), timestamp encodings (ISO-8601 vs. custom European vs. Unix epoch), and UTF-8 BOM prefixes.
2. **Retransmission & Incomplete Duplicates**: Till servers re-sent exports (`__R1`, `__R2`), some of which were partial exports generated mid-roll.
3. **Double Counting**: The vendor till exports both item lines and bill-level summary lines (`TENDER`, `TAX`) in the same file. Summing all rows roughly doubles revenue.
4. **Product Code Reissue (SCD Type 2)**: In June 2024, 24 product codes were reissued to different products, requiring temporal joins to preserve historical product identity.
5. **Historical Pricing**: Prices fluctuate over time. Historical reporting must use prices applicable during the reporting period, not current prices or outdated till prices.
6. **Cross-System Federation**: Sales must reside in object storage (MinIO) while master data remains in PostgreSQL, requiring federated query execution.

---

## 3. Source Data Investigation & Profiling
- **Total sales files**: 4,457 CSV files across 12 stores (`S01` to `S12`).
- **Total raw lines**: 1,137,585 lines.
- **Duplicates**: 16,661 duplicate lines from re-sends. 100% of duplicates were verified to be identical copies.
- **Unique lines**: 1,120,924 lines.
- **Revenue lines**: 789,516 lines (`SALE` 745,860, `DISCOUNT` 22,603, `RETURN` 16,161, `VOID` 4,892).
- **Non-revenue lines**: 331,408 lines (`TAX` 165,704, `TENDER` 165,704).
- **Known gaps**: Pune (`S07`) lost its till server for 3 days in July 2024 (July 9–11).

---

## 4. Architecture
The system is orchestrated via Docker Compose:
- **Relational Masters (PostgreSQL 16)**: Hosts operational master tables (`stores`, `product_categories`, `products`, `price_revisions`) initialized via `/docker-entrypoint-initdb.d/`.
- **Object Storage (MinIO S3)**: Hosts raw daily sales files in partitioned and flat layouts under bucket `annapurna-raw`.
- **Vectorized Analytical Engine (DuckDB)**: Embedded query engine providing cross-system federation (`httpfs`, `postgres`), dimensional modeling, and OLAP analytics.

---

## 5. Storage Layout & Partition Pruning
- **Layout A (Partitioned)**: `raw/sales/store=<store_id>/year=<YYYY>/month=<MM>/<filename>.csv`
- **Layout B (Flat)**: `all-sales/<filename>.csv`
- **Benchmark Result**: In querying Store S01 for March 2024, Layout A restricted scanning to 31 files (605 KB), eliminating 4,426 files and 68.10 MB of I/O (99.12% I/O reduction) compared to the unpartitioned layout.

---

## 6. Idempotent Ingestion
The ingestion pipeline uses deterministic deduplication on the composite business key `(bill_no, line_no)`:
- Executed 3 consecutive times from scratch on the full dataset.
- Row counts for all 3 runs: **789,516** (identical).
- MD5 table checksums for all 3 runs: `c20499905c473af72d4a99643e6122fd` (identical).
- Idempotency verified: YES.

---

## 7. Analytical Data Model (Star Schema)
Implemented in DuckDB:
- **`dim_store`**: 12 stores with physical attributes and regions.
- **`dim_category`**: 14 categories with department and GST rates.
- **`dim_product`**: 1,224 rows preserving historical product versions across the 24 reissued codes.
- **`dim_date`**: 366 days in 2024 with calendar attributes and weekend flags.
- **`fact_sales`**: 789,516 rows at the grain of 1 valid sales line item (`bill_no, line_no`).

---

## 8. Historical Pricing
- Evaluated against `price_revisions` (4,320 records) using temporal join:
  `p.product_key = pr.product_sk AND s.sale_date BETWEEN pr.effective_from AND pr.effective_to`
- Parameterized queries evaluated for March 2024 (Bills=13,602, Revenue=41,971,649.09 INR) and November–December 2024 (Bills=31,694, Revenue=102,329,097.95 INR) without rewriting query logic.

---

## 9. Federated Query
- Joins MinIO raw CSVs with PostgreSQL master tables directly in DuckDB memory.
- `EXPLAIN ANALYZE` confirmed:
  - `POSTGRES_SCAN` pushed down to PostgreSQL container for stores, products, categories.
  - `READ_CSV` streamed directly from MinIO S3 over HTTP.
  - `HASH_JOIN` and `HASH_GROUP_BY` executed inside DuckDB without full table replication.

---

## 10. Revenue Definition
- **Included**: `SALE` (+), `RETURN` (-), `DISCOUNT` (-), `VOID` (cancels corresponding sale line, nets to zero).
- **Excluded**: `TAX` (excluded by finance policy), `TENDER` (bill payment duplicate).

---

## 11. Finance Reconciliation
Comparing pipeline monthly revenue against `finance_monthly.csv`:
- **9 months match to the exact cent** (January, February, April, May, June, August, September, October, November).
- **October Warning**: October strictly reconciles at **56,359,195.92 INR** (0.00 difference), proving that double-counting of TENDER and TAX was completely eliminated.
- **3 differing months explained with proof**:
  1. **March 2024**: -486,250.00 INR due to offline corporate institutional order outside till.
  2. **July 2024**: -232,131.70 INR due to 3 missing Pune S07 days from local hardware outage.
  3. **December 2024**: +50.48 INR due to finance rounding each bill to whole rupees.

---

## 12. Evidence Standards
All claims are backed by reproducible evidence in `evidence/`:
- `docker-compose-ps.txt`: Container runtime state.
- `source_file_count.txt`: Exactly 4,457 files measured.
- `storage-layout-comparison.txt`: Partition pruning benchmark.
- `idempotency.txt`: 3-run row count and checksum comparison.
- `historical-pricing.txt`: Temporal pricing query outputs.
- `federated-query.txt` & `federated-plan.txt`: Cross-system query and EXPLAIN ANALYZE plan.
- `reconciliation.csv`: 12-month reconciliation matrix.
- `validation.txt`: Full validation suite pass (7/7 checks passed).

---

## 13. Limitations
- Institutional orders (e.g. March bulk invoice) are not captured in retail till exports and require a separate enterprise ingestion feed.
- Stores lacking till exports due to hardware failure (Pune July 9–11) require an explicit adjustments table for ledger imports.

---

## 14. Final Conclusion
The Annapurna Stores data platform fulfills all functional, architectural, performance, and evidence requirements of Question 1. The platform is completely reproducible from cold start (`docker compose up -d`), eliminates manual spreadsheet aggregation, handles POS dialect heterogeneity, resolves historical product reissues, and guarantees mathematical accuracy across the 2024 trading year.
