-- ===========================================================================
-- Annapurna Stores - Storage Layout Performance Comparison
-- Measures partition pruning efficiency: Layout A (Partitioned) vs Layout B (Flat)
-- ===========================================================================

-- Layout A: Partitioned Store/Year/Month Scan
-- Target: Store S01 for March 2024
EXPLAIN ANALYZE
SELECT
    COUNT(*) AS row_count,
    ROUND(SUM(qty * unit_price), 2) AS estimated_revenue
FROM read_csv_auto('http://localhost:9000/annapurna-raw/raw/sales/store=S01/year=2024/month=03/*.csv', header=True)
WHERE line_type IN ('SALE', 'DISCOUNT', 'RETURN', 'VOID');

-- Layout B: Flat Unpartitioned Scan
-- Must inspect all files to filter for Store S01 and March 2024
EXPLAIN ANALYZE
SELECT
    COUNT(*) AS row_count,
    ROUND(SUM(qty * unit_price), 2) AS estimated_revenue
FROM read_csv_auto('http://localhost:9000/annapurna-raw/all-sales/SALES_S01_202403*.csv', header=True)
WHERE line_type IN ('SALE', 'DISCOUNT', 'RETURN', 'VOID');
