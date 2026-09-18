# Annapurna Stores — Data Platform & Revenue Analytics

> **Lab Exam:** Question 1  
> **Environment:** Local Docker Compose only (No cloud dependencies)  
> **Architecture:** MinIO (Object Storage) + PostgreSQL 16 (Operational Masters) + DuckDB (Vectorized OLAP & Federation)

---

## 1. Quick Start (Cold-Start Reproducibility)

The entire platform can be brought up from a clean clone using the following command sequence:

### On Linux / macOS / Git Bash:
```bash
cd AnnapurnaStores
docker compose up -d
./scripts/ingest.sh
./scripts/validate.sh
./scripts/collect-evidence.sh
```

### On Windows PowerShell:
```powershell
cd AnnapurnaStores
docker compose up -d
.\scripts\ingest.ps1
.\scripts\validate.ps1
.\scripts\collect-evidence.ps1
```

To perform a clean reset and re-verify cold-start capability:
```bash
./scripts/reset.sh    # or .\scripts\reset.ps1 on Windows
```

---

## 2. Architecture & Data Flow

```text
               /exam/data/sales/ (4,457 CSV files across 3 dialects)
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │      MinIO (S3 Store)     │
                        │                           │
                        │ Partitioned:              │
                        │   raw/sales/store/year/   │
                        │   month/<file>.csv        │
                        │                           │
                        │ Flat Layout:              │
                        │   all-sales/<file>.csv    │
                        └─────────────┬─────────────┘
                                      │
                                      │ (httpfs extension)
                                      ▼
┌─────────────────────────┐     ┌───────────┐
│ PostgreSQL 16 (Masters) │◄───►│  DuckDB   │
│                         │     │           │
│ - stores (12)           │     │ Federated │
│ - categories (14)       │     │ Queries & │
│ - products (1,224)      │     │ Star      │
│ - price_revisions (4,320)     │ Schema    │
└─────────────────────────┘     └─────┬─────┘
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │   Analytical Star Schema  │
                        │                           │
                        │ - dim_store (12)          │
                        │ - dim_category (14)       │
                        │ - dim_product (SCD2 1,224)│
                        │ - dim_date (366)          │
                        │ - fact_sales (789,516)    │
                        └─────────────┬─────────────┘
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │   Finance Reconciliation  │
                        │   vs. finance_monthly.csv │
                        └───────────────────────────┘
```

---

## 3. Key Findings & Engineering Solutions

### 3.1 Three POS File Dialects
1. **S01–S05**: Comma-separated, ISO-8601 timestamps (`2024-10-14T13:45:02`).
2. **S06–S09**: Semicolon-separated, European timestamp format (`DD-MM-YYYY HH:MM:SS`), alias headers (`item_code`, `quantity`, `rate`, `type`).
3. **S10–S12**: Comma-separated with UTF-8 BOM, Unix epoch timestamps (seconds UTC), altered column ordering.
- *Solution*: Canonical schema ingestion normalizes all dialects, timestamps, and encodings uniformly.

### 3.2 Duplicate Handling & Strict Idempotency
- 4,457 total files contained 16,661 duplicate records from re-sends (`__R1`, `__R2`).
- 100% of duplicates were verified to be identical copies.
- Deduplication is enforced on the natural business key: `(bill_no, line_no)`.
- Re-running the pipeline 3 times produces the exact same row count (`789,516`) and identical MD5 table checksum (`c20499905c473af72d4a99643e6122fd`).

### 3.3 Product Code Reissue (SCD Type 2)
- In June 2024, 24 retired product codes were reissued to different products in different categories.
- Joining on `product_code` alone produces duplicated rows and miscategorized products.
- *Solution*: Transactions join on `product_code` AND `sale_date BETWEEN valid_from AND valid_to`, resolving to surrogate key `product_sk`.

### 3.4 Elimination of the October Double-Counting Trap
- The POS exports bill totals (`TENDER`) and GST tax (`TAX`) as rows in the same file as items.
- Summing all rows roughly doubles revenue and counts GST.
- Filtering `line_type IN ('SALE', 'DISCOUNT', 'RETURN', 'VOID')` strictly resolves true net revenue. October net revenue reconciles at **56,359,195.92 INR** (0.00 difference).

### 3.5 Cross-System Query Federation
- Sales files remain in MinIO while master tables remain in PostgreSQL.
- DuckDB's `httpfs` and `postgres` extensions execute cross-system joins and aggregations directly in memory without prior bulk replication.

### 3.6 Finance Reconciliation
- **9 months match to the exact cent** (Jan, Feb, Apr, May, Jun, Aug, Sep, Oct, Nov).
- **3 differing months explained with empirical proof**:
  1. **March 2024**: -486,250.00 INR due to offline bulk institutional corporate invoice.
  2. **July 2024**: -232,131.70 INR due to Pune S07 till server outage on July 9–11 (manual ledger sales).
  3. **December 2024**: +50.48 INR due to finance rounding each bill to whole rupees.

---

## 4. Repository Layout

```text
AnnapurnaStores/
├── README.md                           # Main repository documentation
├── docker-compose.yml                  # Local platform services (postgres, minio, engine)
├── .env.example / .env                 # Environment configuration
├── .gitignore                          # Ignored runtime artifacts
│
├── postgres/
│   ├── init/01_masters.sql             # PostgreSQL initialization script
│   └── queries/                        # Operational PostgreSQL verification queries
│
├── ingestion/
│   ├── scripts/
│   │   ├── ingest.py                   # Lands raw files to MinIO (Layout A & B)
│   │   ├── build_analytical_dataset.py # Builds DuckDB Star Schema
│   │   ├── verify_idempotency.py       # 3-run idempotency & checksum test
│   │   ├── run_storage_layout_experiment.py # Partition pruning benchmark
│   │   ├── run_historical_pricing.py   # Temporal pricing evaluator
│   │   ├── run_federated_query.py      # Federated query executor
│   │   └── reconcile_finance.py        # Finance reconciliation generator
│   └── config/
│
├── duckdb/
│   ├── setup.sql                       # Extension & connection setup
│   ├── dimensions.sql                  # Star schema dimension definitions
│   ├── facts.sql                       # Fact table schema
│   ├── revenue.sql                     # Canonical parameterized revenue queries
│   ├── federated.sql                   # Cross-system federated query
│   └── performance.sql                 # Partition pruning benchmark queries
│
├── object-store/
│   └── README.md                       # Storage architecture & layout documentation
│
├── tests/
│   ├── idempotency.sql                 # Uniqueness assertion
│   ├── data_quality.sql                # Referential integrity & null checks
│   ├── revenue.sql                     # Revenue model checks
│   └── integration.sql                 # End-to-end star schema integration test
│
├── reports/
│   ├── 01_data_profile.md              # Exhaustive raw data profiling report
│   ├── 02_storage_layout.md            # Storage layout & pruning benchmark report
│   ├── 03_idempotency.md               # 3-run idempotency test report
│   ├── 04_data_model.md                # Analytical Star Schema documentation
│   ├── 05_historical_pricing.md        # Historical pricing & revision report
│   ├── 06_federated_query.md           # Federated query & execution plan report
│   ├── 07_reconciliation.md            # Finance reconciliation & variance root-cause report
│   └── final_report.md                 # Comprehensive engineering report
│
├── evidence/
│   ├── commands/command-log.md         # Full command log with measured outputs
│   ├── outputs/                        # Measured quantitative outputs
│   ├── checksums/                      # Idempotency checksum evidence
│   └── query-plans/                    # EXPLAIN / EXPLAIN ANALYZE execution plans
│
└── scripts/
    ├── start.sh / start.ps1            # Platform startup
    ├── stop.sh / stop.ps1              # Platform shutdown
    ├── reset.sh / reset.ps1            # Full cold-start reset
    ├── ingest.sh / ingest.ps1          # Complete ingestion pipeline
    ├── validate.sh / validate.ps1      # System validation suite
    └── collect-evidence.sh / collect-evidence.ps1 # Evidence collection orchestrator
```

---

## 5. Required Evidence Matrix

| Requirement | Evidence File | Status |
| :--- | :--- | :--- |
| Platform starts | `evidence/outputs/docker-compose-ps.txt` | **PASS** |
| Raw file inventory | `evidence/outputs/source_file_count.txt` (4,457) | **PASS** |
| Data profiling | `reports/01_data_profile.md` | **PASS** |
| Partition pruning | `evidence/outputs/storage-layout-comparison.txt` | **PASS** |
| Idempotency (3 runs) | `evidence/checksums/idempotency.txt` | **PASS** |
| Star Schema | `reports/04_data_model.md` | **PASS** |
| Historical pricing | `evidence/outputs/historical-pricing.txt` | **PASS** |
| Federated query | `evidence/outputs/federated-query.txt` | **PASS** |
| Execution plan | `evidence/query-plans/federated-plan.txt` | **PASS** |
| Reconciliation | `evidence/outputs/reconciliation.csv` | **PASS** |
| Final validation | `evidence/outputs/validation.txt` | **PASS** |
