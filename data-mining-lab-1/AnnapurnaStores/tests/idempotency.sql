-- ===========================================================================
-- Annapurna Stores - Idempotency & Uniqueness Test
-- Asserts that business key (bill_no, line_no) is strictly unique in fact_sales.
-- ===========================================================================

SELECT
    bill_no,
    line_no,
    COUNT(*) AS duplicate_count
FROM fact_sales
GROUP BY bill_no, line_no
HAVING COUNT(*) > 1;
-- Expected output: 0 rows (no duplicates)
