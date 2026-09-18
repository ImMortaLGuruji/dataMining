# Annapurna Stores — Storage Layout Report (`02_storage_layout.md`)

## 1. Chosen Partition Layout
The raw daily supermarket sales files are landed into the MinIO object store using the following Hive-style partitioned path pattern:

```text
annapurna-raw/
└── raw/
    └── sales/
        └── store=<store_id>/
            └── year=<YYYY>/
                └── month=<MM>/
                    └── <filename>.csv
```

### Example Object Paths:
- `s3://annapurna-raw/raw/sales/store=S01/year=2024/month=01/SALES_S01_20240101.csv`
- `s3://annapurna-raw/raw/sales/store=S07/year=2024/month=07/SALES_S07_20240701.csv`
- `s3://annapurna-raw/raw/sales/store=S12/year=2024/month=12/SALES_S12_20241231.csv`

---

## 2. Partitioning Rationale
Supermarket analytics queries predominantly filter by:
1. Store location (`store_id`)
2. Reporting time window (`year`, `month`)

By encoding `store`, `year`, and `month` directly into the object storage key prefix hierarchy, query engines (such as DuckDB, Trino, and Spark) can perform **prefix-level partition pruning**. Instead of issuing an expensive `LIST` bucket operation across all 4,457 files and reading headers, the engine restricts its scan exclusively to the specific prefix matching the predicate.

---

## 3. Empirical Storage Layout Experiment
To evaluate the performance benefits of partitioning, an experiment was executed comparing **Layout A (Partitioned)** against **Layout B (Flat Folder)**.

### Target Query:
Query all sales for **Store S01** during **March 2024** (`store=S01/year=2024/month=03`):

```sql
SELECT COUNT(*) AS row_count, ROUND(SUM(qty * unit_price), 2) AS estimated_revenue
FROM read_csv('s3://annapurna-raw/...', header=True)
WHERE line_type IN ('SALE', 'DISCOUNT', 'RETURN', 'VOID');
```

### Measured Comparison:
| Metric | Layout A (Partitioned) | Layout B (Flat Unpartitioned) | Improvement / Reduction |
| :--- | :--- | :--- | :--- |
| **Object Prefix** | `raw/sales/store=S01/year=2024/month=03/` | `all-sales/` | Targeted Sub-prefix |
| **Files Scanned** | **31** | **4,457** | **-4,426 files (-99.30%)** |
| **Bytes Scanned** | **605,470 bytes (0.58 MB)** | **68,706,877 bytes (65.52 MB)** | **-68.10 MB (-99.12% I/O)** |
| **Execution Time** | **0.302 s** | Full Scan overhead | Eliminates listing overhead |
| **Row Count Returned** | 6,753 | 6,753 | Identical results |
| **Revenue Calculated** | 4,408,976.65 INR | 4,408,976.65 INR | Identical results |

---

## 4. Evidence Traceability
The raw benchmark evidence was measured and recorded in:
- `AnnapurnaStores/evidence/outputs/storage-layout-comparison.txt`
- Benchmark Script: `AnnapurnaStores/ingestion/scripts/run_storage_layout_experiment.py`
