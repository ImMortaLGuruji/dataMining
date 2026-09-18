-- ===========================================================================
-- Annapurna Stores - End-to-End Integration Verification
-- Joins fact_sales across all dimensions to verify full star-schema integrity.
-- ===========================================================================

SELECT
    s.region,
    s.store_name,
    c.department,
    c.category_name,
    d.year,
    d.month,
    COUNT(DISTINCT f.bill_no) AS bill_count,
    SUM(f.quantity) AS units_sold,
    ROUND(SUM(f.revenue), 2) AS total_revenue
FROM fact_sales f
JOIN dim_store s ON f.store_key = s.store_key
JOIN dim_product p ON f.product_key = p.product_key
JOIN dim_category c ON p.category_id = c.category_id
JOIN dim_date d ON f.date_key = d.date_key
GROUP BY
    s.region,
    s.store_name,
    c.department,
    c.category_name,
    d.year,
    d.month
ORDER BY
    d.year,
    d.month,
    total_revenue DESC
LIMIT 20;
