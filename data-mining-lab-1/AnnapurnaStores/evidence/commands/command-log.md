# Annapurna Stores — Command Execution Log

## 1. Environment Verification

### Command
```bash
docker --version
docker compose version
py --version
duckdb --version
```

### Measured Output
```text
Docker version 29.8.0, build 88096ef
Docker Compose version v5.5.1
Python 3.13.1
DuckDB v1.5.5 (Variegata) d8cdaa33fd
```

### Purpose
Verify that Docker, Docker Compose, Python, and DuckDB runtime environments are present locally.

---

## 2. Infrastructure Startup

### Command
```bash
cd AnnapurnaStores
docker compose up -d
```

### Measured Output
```text
Container annapurna-postgres Started (healthy)
Container annapurna-minio Started (healthy)
Container annapurna-engine Started
```

### Purpose
Start the local platform services (PostgreSQL 16, MinIO, Python analytical environment).

---

## 3. Master Data Verification in PostgreSQL

### Command
```bash
docker exec annapurna-postgres psql -U annapurna -d annapurna -c "
SELECT 'stores' as tbl, count(*) from stores
UNION ALL SELECT 'product_categories', count(*) from product_categories
UNION ALL SELECT 'products', count(*) from products
UNION ALL SELECT 'price_revisions', count(*) from price_revisions;
"
```

### Measured Output
```text
        tbl         | count 
--------------------+-------
 stores             |    12
 product_categories |    14
 products           |  1224
 price_revisions    |  4320
(4 rows)
```

### Purpose
Verify that operational master tables are loaded into PostgreSQL via `postgres/init/01_masters.sql`.

---

## 4. Raw Sales Landing to MinIO Object Storage

### Command
```bash
py ingestion/scripts/ingest.py
```

### Measured Output
```text
[Ingest] Using sales directory: ...\exam\data\sales
[Ingest] Discovered 4457 sales CSV files.
[Ingest] Created MinIO bucket: annapurna-raw
[Ingest] Landing 4457 files to MinIO bucket 'annapurna-raw'...
[Ingest] Upload complete. Layout A uploaded: 4457, Layout B uploaded: 4457
[Ingest] Ingestion landing phase completed successfully.
```

### Purpose
Upload all 4,457 raw sales CSV files into MinIO under both Partitioned (Layout A) and Flat (Layout B) layouts.

---

## 5. Idempotent Ingestion & Analytical Dataset Build

### Command
```bash
py ingestion/scripts/verify_idempotency.py
```

### Measured Output
```text
--- RUN 1 ---
Run 1 Row count: 789516
Run 1 Checksum : c20499905c473af72d4a99643e6122fd

--- RUN 2 ---
Run 2 Row count: 789516
Run 2 Checksum : c20499905c473af72d4a99643e6122fd

--- RUN 3 ---
Run 3 Row count: 789516
Run 3 Checksum : c20499905c473af72d4a99643e6122fd

--- COMPARISON ---
Row counts identical: YES
Checksums identical : YES
```

### Purpose
Validate strict idempotency across 3 runs on business key `(bill_no, line_no)` with identical row counts and MD5 checksums.

---

## 6. Storage Layout Experiment

### Command
```bash
py ingestion/scripts/run_storage_layout_experiment.py
```

### Measured Output
```text
LAYOUT A: PARTITIONED (store=S01/year=2024/month=03/)
Files scanned/opened: 31
Bytes scanned/opened: 605,470 bytes (0.58 MB)

LAYOUT B: FLAT UNPARTITIONED (all-sales/)
Total objects in bucket directory: 4457
Total directory size: 68,706,877 bytes (65.52 MB)

EFFICIENCY & PRUNING ANALYSIS:
Files eliminated by prefix pruning: 4426 files (99.30% reduction)
Bytes eliminated by prefix pruning: 68,101,407 bytes (99.12% I/O reduction)
```

### Purpose
Demonstrate empirical prefix partition pruning benefits between Layout A and Layout B.

---

## 7. Historical Pricing Evaluation

### Command
```bash
py ingestion/scripts/run_historical_pricing.py
```

### Measured Output
```text
QUERY A: MARCH 2024
Total Bills: 13602, Sales Lines: 64507, Net Revenue (INR): 41971649.09

QUERY B: RECENT TWO-MONTH PERIOD (NOV - DEC 2024)
Month 2024-11: Bills=16089, Lines=76712, Net Revenue=51583838.47 INR
Month 2024-12: Bills=15605, Lines=74511, Net Revenue=50745259.48 INR
```

### Purpose
Prove dynamic historical price resolution from `price_revisions` without query rewriting.

---

## 8. Federated Cross-System Query

### Command
```bash
py ingestion/scripts/run_federated_query.py
```

### Measured Output
```text
[Federation] Initializing httpfs and postgres extensions...
[Federation] Attaching operational PostgreSQL masters...
[Federation] Capturing EXPLAIN plan...
[Federation] Capturing EXPLAIN ANALYZE plan...
[Federation] Executing federated query...
Saved output to evidence/outputs/federated-query.txt
Saved plan to evidence/query-plans/federated-plan.txt
```

### Purpose
Demonstrate cross-system query joining MinIO S3 raw files with PostgreSQL tables on-the-fly with execution plan proof.

---

## 9. Finance Reconciliation

### Command
```bash
py ingestion/scripts/reconcile_finance.py
```

### Measured Output
```text
Month      | Pipeline Rev    | Finance Rev     | Diff         | Status     | Root Cause
-----------------------------------------------------------------------------------------------
2024-01    | 38446071.33     | 38446071.33     | 0.00         | MATCH      | Exact Match
2024-02    | 34887085.55     | 34887085.55     | 0.00         | MATCH      | Exact Match
2024-03    | 41971649.09     | 42457899.09     | -486250.00   | VARIANCE   | Scope difference: bulk invoice
2024-04    | 37958457.37     | 37958457.37     | 0.00         | MATCH      | Exact Match
2024-05    | 41764716.40     | 41764716.40     | 0.00         | MATCH      | Exact Match
2024-06    | 38987082.82     | 38987082.82     | 0.00         | MATCH      | Exact Match
2024-07    | 40295160.11     | 40527291.81     | -232131.70   | VARIANCE   | Source data: Pune outage
2024-08    | 45252181.75     | 45252181.75     | 0.00         | MATCH      | Exact Match
2024-09    | 44615037.46     | 44615037.46     | 0.00         | MATCH      | Exact Match
2024-10    | 56359195.92     | 56359195.92     | 0.00         | MATCH      | Exact Match
2024-11    | 51583838.47     | 51583838.47     | 0.00         | MATCH      | Exact Match
2024-12    | 50745259.48     | 50745209.00     | 50.48        | VARIANCE   | Definition: rupee rounding
```

### Purpose
Reconcile calculated pipeline revenue against `finance_monthly.csv` with full classification of variances.

---

## 10. System Validation Suite

### Command
```bash
py scripts/validate.py
```

### Measured Output
```text
[1/7] Validating Docker containers...           PASS
[2/7] Validating PostgreSQL master tables...     PASS
[3/7] Validating MinIO object store...           PASS
[4/7] Validating DuckDB Star Schema tables...    PASS
[5/7] Validating uniqueness and idempotency...   PASS
[6/7] Validating Data Quality rules...           PASS
[7/7] Validating Finance Reconciliation...       PASS
RESULT: ALL VALIDATION CHECKS PASSED (EXIT CODE 0)
```

### Purpose
Comprehensive gatekeeper checking infrastructure, data landing, star schema, data quality, and finance sign-off.
