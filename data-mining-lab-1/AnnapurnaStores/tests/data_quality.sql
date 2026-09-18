-- ===========================================================================
-- Annapurna Stores - Data Quality Assertions
-- Verifies referential integrity, null constraints, and valid line types.
-- ===========================================================================

-- 1. Check for orphaned stores
SELECT COUNT(*) AS orphaned_store_records
FROM fact_sales f
LEFT JOIN dim_store s ON f.store_key = s.store_key
WHERE s.store_key IS NULL;

-- 2. Check for orphaned products
SELECT COUNT(*) AS orphaned_product_records
FROM fact_sales f
LEFT JOIN dim_product p ON f.product_key = p.product_key
WHERE p.product_key IS NULL;

-- 3. Check for orphaned dates
SELECT COUNT(*) AS orphaned_date_records
FROM fact_sales f
LEFT JOIN dim_date d ON f.date_key = d.date_key
WHERE d.date_key IS NULL;

-- 4. Check for invalid line types
SELECT COUNT(*) AS invalid_line_type_records
FROM fact_sales
WHERE line_type NOT IN ('SALE', 'DISCOUNT', 'RETURN', 'VOID');

-- 5. Check for null revenue or quantity
SELECT COUNT(*) AS null_measures_records
FROM fact_sales
WHERE quantity IS NULL OR unit_price IS NULL OR revenue IS NULL;
