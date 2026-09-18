-- ===========================================================================
-- Annapurna Stores - Cross-System Federated Query
-- Joins sales files in object storage (MinIO) directly with master tables
-- in PostgreSQL without prior intermediate materialization or bulk replication.
-- ===========================================================================

-- Attach PostgreSQL operational master database
ATTACH IF NOT EXISTS 'dbname=annapurna user=annapurna password=annapurnapassword host=localhost port=5432' AS pg_db (TYPE postgres);

-- Federated Cross-System Query joining MinIO raw sales with PostgreSQL masters
EXPLAIN ANALYZE
SELECT
    s.store_name,
    s.city,
    c.category_name,
    c.department,
    COUNT(DISTINCT f.bill_no) AS total_bills,
    SUM(f.quantity) AS total_quantity,
    ROUND(SUM(f.revenue), 2) AS total_revenue
FROM fact_sales f
JOIN pg_db.stores s
    ON f.store_key = s.store_id
JOIN pg_db.products p
    ON f.product_key = p.product_sk
JOIN pg_db.product_categories c
    ON p.category_id = c.category_id
WHERE f.sale_date >= DATE '2024-10-01'
  AND f.sale_date <  DATE '2024-11-01'
GROUP BY
    s.store_name,
    s.city,
    c.category_name,
    c.department
ORDER BY
    total_revenue DESC
LIMIT 20;
