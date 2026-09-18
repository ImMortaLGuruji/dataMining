# Annapurna Stores — Idempotency Report (`03_idempotency.md`)

## 1. Pipeline Design & Duplicate Handling
The ingestion pipeline ensures strict idempotency through deterministic deduplication on the natural business key:
`Key = (bill_no, line_no)`

### Why "Take Newest File" Fails:
The vendor billing documentation explicitly highlights that re-sent files (`__R1`, `__R2`) are sometimes generated mid-roll while the till is committing transactions. In such cases, the re-sent export only contains the committed subset of the day's bills. Discarding older files in favor of newer ones causes silent data loss. Instead, all files are processed and deduplicated at the individual transaction line level.

---

## 2. Checksum Strategy
To prove that the analytical state is deterministic and idempotent across runs, a global MD5 checksum is computed across canonical representations of all records in `fact_sales`:

```sql
SELECT md5(string_agg(
    concat_ws('|',
        bill_no,
        CAST(line_no AS TEXT),
        store_key,
        CAST(product_key AS TEXT),
        CAST(sale_date AS TEXT),
        CAST(ROUND(quantity, 2) AS TEXT),
        CAST(ROUND(unit_price, 2) AS TEXT),
        CAST(ROUND(revenue, 2) AS TEXT),
        line_type
    ),
    chr(10)
    ORDER BY bill_no, line_no
)) AS table_checksum
FROM fact_sales;
```

---

## 3. Idempotency Test Execution & Results
The pipeline was executed three consecutive times from scratch on the full dataset of 4,457 files.

### Empirical Measurements:
| Run Execution | Command | Measured Row Count | Measured MD5 Checksum |
| :--- | :--- | :--- | :--- |
| **RUN 1** | `python ingestion/scripts/build_analytical_dataset.py` | **789,516** | `c20499905c473af72d4a99643e6122fd` |
| **RUN 2** | `python ingestion/scripts/build_analytical_dataset.py` | **789,516** | `c20499905c473af72d4a99643e6122fd` |
| **RUN 3** | `python ingestion/scripts/build_analytical_dataset.py` | **789,516** | `c20499905c473af72d4a99643e6122fd` |

### Comparison:
- **Row counts identical across all 3 runs**: **YES** (`row_count_1 = row_count_2 = row_count_3 = 789,516`)
- **Checksums identical across all 3 runs**: **YES** (`checksum_1 = checksum_2 = checksum_3 = c20499905c473af72d4a99643e6122fd`)

---

## 4. Conclusion
The ingestion pipeline is completely idempotent. Running the ingestion once, twice, or three times produces the exact same analytical state down to the byte level without duplicate accumulation or state corruption.

- Verified Evidence File: `AnnapurnaStores/evidence/checksums/idempotency.txt`
- Runner Script: `AnnapurnaStores/ingestion/scripts/verify_idempotency.py`
