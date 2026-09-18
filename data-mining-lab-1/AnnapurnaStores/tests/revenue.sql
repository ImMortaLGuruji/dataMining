-- ===========================================================================
-- Annapurna Stores - Revenue Model Tests
-- Verifies monthly revenue computations and absence of TAX/TENDER double counting.
-- ===========================================================================

-- 1. Verify no TAX or TENDER rows leaked into fact_sales
SELECT line_type, COUNT(*) AS count
FROM fact_sales
WHERE line_type IN ('TAX', 'TENDER')
GROUP BY line_type;

-- 2. Monthly Revenue Distribution Check
SELECT
    d.year,
    d.month,
    COUNT(*) AS sales_lines,
    ROUND(SUM(f.revenue), 2) AS monthly_net_revenue
FROM fact_sales f
JOIN dim_date d ON f.date_key = d.date_key
GROUP BY d.year, d.month
ORDER BY d.year, d.month;
