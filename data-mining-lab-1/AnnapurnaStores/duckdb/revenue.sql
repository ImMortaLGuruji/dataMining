-- ===========================================================================
-- Annapurna Stores - Canonical Revenue Query
-- Parameterized analytical revenue query supporting store, category, and date slicing.
-- ===========================================================================

-- 1. Monthly Revenue by Store & Category
SELECT
    d.year,
    d.month,
    s.store_name,
    c.category_name,
    COUNT(DISTINCT f.bill_no) AS transaction_count,
    SUM(f.quantity) AS total_units_sold,
    ROUND(SUM(f.revenue), 2) AS net_revenue
FROM fact_sales f
JOIN dim_date d
    ON f.date_key = d.date_key
JOIN dim_store s
    ON f.store_key = s.store_key
JOIN dim_product p
    ON f.product_key = p.product_key
JOIN dim_category c
    ON p.category_id = c.category_id
WHERE f.sale_date >= DATE '2024-03-01'
  AND f.sale_date <  DATE '2024-04-01'
GROUP BY
    d.year,
    d.month,
    s.store_name,
    c.category_name
ORDER BY
    net_revenue DESC;

-- 2. Monthly Total Net Revenue (Finance Reconciliation Grain)
SELECT
    d.year,
    d.month,
    COUNT(DISTINCT f.bill_no) AS total_bills,
    COUNT(*) AS total_sales_lines,
    ROUND(SUM(f.revenue), 2) AS monthly_net_revenue
FROM fact_sales f
JOIN dim_date d
    ON f.date_key = d.date_key
GROUP BY
    d.year,
    d.month
ORDER BY
    d.year,
    d.month;
