# Annapurna Stores — Federated Query Report (`06_federated_query.md`)

## 1. Architectural Objective
A core requirement of the lab exam is that sales data remains in object storage (MinIO) while master reference data remains in PostgreSQL. The system must execute cross-system queries joining both platforms on-the-fly without pre-replicating or bulk materializing one platform's dataset into the other.

---

## 2. Federated Implementation
DuckDB serves as the embedded analytical query engine, employing its native `httpfs` extension to read raw CSV files over S3 from MinIO and its `postgres` extension to read master tables from PostgreSQL.

### Execution Query:
```sql
SELECT
    s.store_name,
    s.city,
    c.category_name,
    c.department,
    COUNT(DISTINCT raw_sales.column0) AS total_bills,
    SUM(CAST(raw_sales.column3 AS DECIMAL(12,2))) AS total_quantity,
    ROUND(SUM(CAST(raw_sales.column3 AS DECIMAL(12,2)) * CAST(raw_sales.column4 AS DECIMAL(12,2))), 2) AS total_revenue
FROM read_csv('s3://annapurna-raw/raw/sales/store=S01/year=2024/month=03/*.csv', header=True, ...) AS raw_sales
JOIN pg_db.stores s
    ON s.store_id = 'S01'
JOIN pg_db.products p
    ON raw_sales.column2 = p.product_code
   AND DATE '2024-03-15' >= p.valid_from
   AND DATE '2024-03-15' <= p.valid_to
JOIN pg_db.product_categories c
    ON p.category_id = c.category_id
WHERE raw_sales.column5 IN ('SALE', 'DISCOUNT', 'RETURN', 'VOID')
GROUP BY s.store_name, s.city, c.category_name, c.department
ORDER BY total_revenue DESC;
```

---

## 3. Physical Execution Plan Analysis
The engine execution plan was captured via `EXPLAIN ANALYZE` (stored in `evidence/query-plans/federated-plan.txt`):

### Observed Operators & Execution Locations:
1. **Object Store Scan (`READ_CSV`)**:
   - Location: MinIO S3 endpoint (`s3://annapurna-raw/raw/sales/store=S01/year=2024/month=03/*.csv`).
   - Operation: DuckDB streams 31 CSV objects over HTTP, parsing and filtering valid line types on-the-fly without landing data to disk.
2. **PostgreSQL Scans (`POSTGRES_SCAN`)**:
   - Location: Local PostgreSQL container (`annapurna-postgres`).
   - Operation: Pushes predicate `store_id = 'S01'` down to PostgreSQL `stores` table; scans reference tables `products` and `product_categories`.
3. **Cross-System Join (`HASH_JOIN`)**:
   - Location: DuckDB memory engine.
   - Operation: Builds hash tables on PostgreSQL dimensions and probes with streamed rows from MinIO S3.
4. **Aggregation (`HASH_GROUP_BY`) & Sorting (`ORDER_BY`)**:
   - Location: DuckDB vectorized pipeline.
   - Operation: Groups revenue by store, city, and category, producing the final analytical result set.

---

## 4. Evidence
- Output Evidence: `AnnapurnaStores/evidence/outputs/federated-query.txt`
- Query Plan Evidence: `AnnapurnaStores/evidence/query-plans/federated-plan.txt`
- Runner Script: `AnnapurnaStores/ingestion/scripts/run_federated_query.py`
