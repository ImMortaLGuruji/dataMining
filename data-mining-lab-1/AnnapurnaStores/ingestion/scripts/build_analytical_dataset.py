#!/usr/bin/env python3
"""
Annapurna Stores - Analytical Dataset Builder
Builds the analytical DuckDB database containing the Star Schema:
- dim_store
- dim_category
- dim_product (SCD Type 2 preserving historical product-code reuse)
- dim_date
- fact_sales (grain: 1 sales line, deduplicated on (bill_no, line_no))
Resolves historical pricing from price_revisions.
"""

import os
import sys
import glob
import csv
from datetime import datetime, timezone
import duckdb

# Paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(BASE_DIR, "annapurna.duckdb")
CURATED_CSV = os.path.join(BASE_DIR, "curated_sales_raw.csv")

DATA_DIRS = [
    os.path.join(BASE_DIR, "..", "exam", "data", "sales"),
    os.path.join("/exam", "data", "sales"),
    os.path.join(os.getcwd(), "exam", "data", "sales"),
]

SALES_DIR = None
for d in DATA_DIRS:
    abs_d = os.path.abspath(d)
    if os.path.isdir(abs_d):
        SALES_DIR = abs_d
        break

if not SALES_DIR:
    print(f"Error: Could not find sales directory in {DATA_DIRS}")
    sys.exit(1)


def normalize_ts(ts_raw, store_id):
    ts_raw = ts_raw.strip()
    if store_id in ['S01', 'S02', 'S03', 'S04', 'S05']:
        # ISO-8601 e.g. 2024-01-01T14:19:31
        return ts_raw.replace('T', ' ')
    elif store_id in ['S06', 'S07', 'S08', 'S09']:
        # dd-mm-yyyy HH:MM:SS
        try:
            parts = ts_raw.split(' ')
            dp = parts[0].split('-')
            return f"{dp[2]}-{dp[1]}-{dp[0]} {parts[1]}"
        except Exception:
            return ts_raw
    elif store_id in ['S10', 'S11', 'S12']:
        # Unix epoch seconds UTC
        try:
            epoch = int(ts_raw)
            dt = datetime.fromtimestamp(epoch, tz=timezone.utc)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            return ts_raw
    return ts_raw


def build_star_schema(con):
    print("[Build] Attaching PostgreSQL operational masters...")
    con.execute("INSTALL postgres; LOAD postgres;")
    con.execute("ATTACH IF NOT EXISTS 'dbname=annapurna user=annapurna password=annapurnapassword host=localhost port=5432' AS pg_db (TYPE postgres);")

    print("[Build] Creating dim_store...")
    con.execute("""
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
    """)

    print("[Build] Creating dim_category...")
    con.execute("""
        CREATE OR REPLACE TABLE dim_category AS
        SELECT
            category_id AS category_key,
            category_id,
            category_name,
            department,
            gst_rate
        FROM pg_db.product_categories;
    """)

    print("[Build] Creating dim_product (preserving historical SCD2 identity)...")
    con.execute("""
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
    """)

    print("[Build] Creating dim_price_revisions...")
    con.execute("""
        CREATE OR REPLACE TABLE dim_price_revisions AS
        SELECT
            revision_id,
            product_sk,
            mrp,
            selling_price,
            effective_from,
            effective_to
        FROM pg_db.price_revisions;
    """)

    print("[Build] Creating dim_date...")
    con.execute("""
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
    """)


def process_sales_files(con):
    print("[Build] Scanning sales files and normalizing across dialects...")
    files = sorted(glob.glob(os.path.join(SALES_DIR, "*.csv")))
    print(f"[Build] Total files discovered: {len(files)}")

    seen_lines = set()
    total_raw_rows = 0
    duplicate_rows = 0

    with open(CURATED_CSV, "w", newline="", encoding="utf-8") as out_f:
        writer = csv.writer(out_f)

        for fpath in files:
            fname = os.path.basename(fpath)
            parts = fname.replace('.csv', '').split('_')
            store_id = parts[1]
            bdate_str = parts[2][:8]
            bdate = f"{bdate_str[:4]}-{bdate_str[4:6]}-{bdate_str[6:8]}"
            
            sep = ';' if store_id in ['S06', 'S07', 'S08', 'S09'] else ','

            with open(fpath, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f, delimiter=sep)
                header = [c.strip().lower() for c in next(reader)]

                col_map = {}
                for i, c in enumerate(header):
                    if c in ['bill_no']: col_map['bill_no'] = i
                    elif c in ['line_no']: col_map['line_no'] = i
                    elif c in ['product_code', 'item_code']: col_map['product_code'] = i
                    elif c in ['qty', 'quantity']: col_map['qty'] = i
                    elif c in ['unit_price', 'rate']: col_map['unit_price'] = i
                    elif c in ['line_type', 'type']: col_map['line_type'] = i
                    elif c in ['ts', 'txn_time']: col_map['ts'] = i

                for row in reader:
                    if not row:
                        continue
                    total_raw_rows += 1
                    b_no = row[col_map['bill_no']].strip()
                    l_no = int(row[col_map['line_no']].strip())
                    key = (b_no, l_no)
                    if key in seen_lines:
                        duplicate_rows += 1
                        continue
                    seen_lines.add(key)

                    p_code = row[col_map['product_code']].strip()
                    qty = float(row[col_map['qty']].strip())
                    u_price = float(row[col_map['unit_price']].strip())
                    l_type = row[col_map['line_type']].strip().upper()
                    ts = normalize_ts(row[col_map['ts']], store_id)

                    writer.writerow([b_no, l_no, store_id, bdate, p_code, qty, u_price, l_type, ts, fname])

    print(f"[Build] Total raw rows scanned: {total_raw_rows}")
    print(f"[Build] Duplicates skipped: {duplicate_rows}")
    print(f"[Build] Unique lines written to curated CSV: {len(seen_lines)}")

    # Load curated CSV into DuckDB
    csv_path = CURATED_CSV.replace(chr(92), '/')
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE stage_sales_raw AS
        SELECT
            column0 AS bill_no,
            CAST(column1 AS INTEGER) AS line_no,
            column2 AS store_id,
            CAST(column3 AS DATE) AS sale_date,
            column4 AS product_code,
            CAST(column5 AS DECIMAL(12,2)) AS qty,
            CAST(column6 AS DECIMAL(12,2)) AS unit_price,
            column7 AS line_type,
            CAST(column8 AS TIMESTAMP) AS ts,
            column9 AS source_file
        FROM read_csv('{csv_path}',
            header=False,
            columns={{
                'column0': 'VARCHAR',
                'column1': 'INTEGER',
                'column2': 'VARCHAR',
                'column3': 'VARCHAR',
                'column4': 'VARCHAR',
                'column5': 'VARCHAR',
                'column6': 'VARCHAR',
                'column7': 'VARCHAR',
                'column8': 'VARCHAR',
                'column9': 'VARCHAR'
            }}
        );
    """)

    print("[Build] Creating fact_sales with historical product and price resolution...")
    con.execute("""
        CREATE OR REPLACE TABLE fact_sales AS
        SELECT
            md5(concat(s.bill_no, '#', CAST(s.line_no AS TEXT))) AS sales_key,
            s.bill_no,
            s.line_no,
            s.store_id AS store_key,
            p.product_key,
            CAST(strftime(s.sale_date, '%Y%m%d') AS INTEGER) AS date_key,
            s.sale_date,
            s.qty AS quantity,
            s.unit_price,
            pr.selling_price AS historical_price,
            CAST(ROUND(s.qty * s.unit_price, 2) AS DECIMAL(12,2)) AS revenue,
            s.line_type,
            s.source_file,
            s.ts AS txn_time
        FROM stage_sales_raw s
        -- Join product on product_code AND sale_date to resolve reissued codes correctly
        LEFT JOIN dim_product p
            ON s.product_code = p.product_code
           AND s.sale_date >= p.valid_from
           AND s.sale_date <= p.valid_to
        -- Join price revision to resolve authoritative historical selling price
        LEFT JOIN dim_price_revisions pr
            ON p.product_key = pr.product_sk
           AND s.sale_date >= pr.effective_from
           AND s.sale_date <= pr.effective_to
        WHERE s.line_type IN ('SALE', 'DISCOUNT', 'RETURN', 'VOID');
    """)

    # Record count check
    count = con.execute("SELECT count(*) FROM fact_sales").fetchone()[0]
    print(f"[Build] fact_sales created with {count} rows.")


def main():
    print(f"[Build] Opening analytical database at {DB_PATH}...")
    con = duckdb.connect(DB_PATH)
    try:
        build_star_schema(con)
        process_sales_files(con)
        print("[Build] Analytical build completed successfully.")
    finally:
        con.close()


if __name__ == "__main__":
    main()
