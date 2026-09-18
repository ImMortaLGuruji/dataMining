-- ===========================================================================
-- Annapurna Stores - Analytical Dimension Tables
-- Star Schema dimensions sourced from PostgreSQL master tables & calendar
-- ===========================================================================

-- 1. Store Dimension
CREATE OR REPLACE TABLE dim_store AS
SELECT
    store_id AS store_key,
    store_id,
    store_name,
    address_line,
    city,
    state,
    region,
    floor_area_sqft,
    opened_on
FROM pg_db.stores;

-- 2. Category Dimension
CREATE OR REPLACE TABLE dim_category AS
SELECT
    category_id AS category_key,
    category_id,
    category_name,
    department,
    gst_rate
FROM pg_db.product_categories;

-- 3. Product Dimension (SCD Type 2 preserving historical product-code reuse)
CREATE OR REPLACE TABLE dim_product AS
SELECT
    product_sk AS product_key,
    product_code,
    product_name,
    category_id,
    brand,
    pack_size,
    uom,
    valid_from,
    valid_to,
    is_current
FROM pg_db.products;

-- 4. Date Dimension
CREATE OR REPLACE TABLE dim_date AS
WITH date_series AS (
    SELECT CAST('2024-01-01' AS DATE) + INTERVAL (d) DAY AS cal_date
    FROM range(0, 366) t(d)
)
SELECT
    CAST(strftime(cal_date, '%Y%m%d') AS INTEGER) AS date_key,
    cal_date AS calendar_date,
    CAST(strftime(cal_date, '%Y') AS INTEGER) AS year,
    CAST(strftime(cal_date, '%m') AS INTEGER) AS month,
    strftime(cal_date, '%B') AS month_name,
    CAST(strftime(cal_date, '%d') AS INTEGER) AS day,
    dayofweek(cal_date) AS day_of_week,
    strftime(cal_date, '%A') AS day_of_week_name,
    week(cal_date) AS week,
    CASE WHEN dayofweek(cal_date) IN (0, 6) THEN TRUE ELSE FALSE END AS is_weekend
FROM date_series;
