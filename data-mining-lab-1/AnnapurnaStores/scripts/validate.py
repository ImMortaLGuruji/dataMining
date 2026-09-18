#!/usr/bin/env python3
"""
Annapurna Stores - Comprehensive Validation Suite
Validates:
1. Docker container services
2. PostgreSQL connectivity and master tables
3. MinIO connectivity and object counts
4. DuckDB Star Schema tables and row counts
5. Idempotency assertion
6. Data quality checks
7. Finance reconciliation sign-off
Returns exit code 0 on full pass, 1 on failure.
"""

import os
import sys
import subprocess
import duckdb
from minio import Minio

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(BASE_DIR, "annapurna.duckdb")
EVIDENCE_OUT = os.path.join(BASE_DIR, "evidence", "outputs", "validation.txt")


def check_docker():
    print("[1/7] Validating Docker containers...")
    res = subprocess.run(["docker", "compose", "ps"], cwd=BASE_DIR, capture_output=True, text=True)
    if res.returncode != 0:
        print("FAIL: Docker compose ps failed")
        return False
    if "annapurna-postgres" not in res.stdout or "annapurna-minio" not in res.stdout:
        print("FAIL: Required containers are not running")
        return False
    print("PASS: Docker containers are running.")
    return True


def check_postgres():
    print("[2/7] Validating PostgreSQL master tables...")
    res = subprocess.run([
        "docker", "exec", "annapurna-postgres",
        "psql", "-U", "annapurna", "-d", "annapurna", "-t", "-A", "-c",
        "SELECT count(*) FROM stores UNION ALL SELECT count(*) FROM product_categories UNION ALL SELECT count(*) FROM products UNION ALL SELECT count(*) FROM price_revisions;"
    ], capture_output=True, text=True)
    if res.returncode != 0:
        print(f"FAIL: PostgreSQL query failed: {res.stderr}")
        return False
    counts = [int(c) for c in res.stdout.strip().splitlines() if c.isdigit()]
    if counts != [12, 14, 1224, 4320]:
        print(f"FAIL: Unexpected master table row counts: {counts} (expected [12, 14, 1224, 4320])")
        return False
    print(f"PASS: PostgreSQL masters verified: stores=12, categories=14, products=1224, revisions=4320.")
    return True


def check_minio():
    print("[3/7] Validating MinIO object store...")
    try:
        client = Minio("localhost:9000", access_key="annapurna", secret_key="annapurnapassword", secure=False)
        if not client.bucket_exists("annapurna-raw"):
            print("FAIL: MinIO bucket 'annapurna-raw' does not exist")
            return False
        objs = list(client.list_objects("annapurna-raw", prefix="raw/sales/", recursive=True))
        if len(objs) < 4457:
            print(f"FAIL: Incomplete raw files in MinIO: found {len(objs)} (expected 4457)")
            return False
        print(f"PASS: MinIO raw bucket verified with {len(objs)} partitioned sales files.")
        return True
    except Exception as e:
        print(f"FAIL: MinIO validation error: {e}")
        return False


def check_duckdb_schema():
    print("[4/7] Validating DuckDB Star Schema tables...")
    if not os.path.exists(DB_PATH):
        print(f"FAIL: DuckDB database not found at {DB_PATH}")
        return False
    con = duckdb.connect(DB_PATH, read_only=True)
    try:
        tables = dict(con.execute("SELECT table_name, estimated_size FROM duckdb_tables() WHERE schema_name = 'main'").fetchall())
        required_tables = ["dim_store", "dim_category", "dim_product", "dim_date", "fact_sales"]
        for t in required_tables:
            if t not in tables:
                print(f"FAIL: Missing table in Star Schema: {t}")
                return False
        
        # Check counts
        stores_cnt = con.execute("SELECT count(*) FROM dim_store").fetchone()[0]
        cat_cnt = con.execute("SELECT count(*) FROM dim_category").fetchone()[0]
        prod_cnt = con.execute("SELECT count(*) FROM dim_product").fetchone()[0]
        date_cnt = con.execute("SELECT count(*) FROM dim_date").fetchone()[0]
        fact_cnt = con.execute("SELECT count(*) FROM fact_sales").fetchone()[0]

        if stores_cnt != 12 or cat_cnt != 14 or prod_cnt != 1224 or fact_cnt != 789516:
            print(f"FAIL: Row count mismatch: stores={stores_cnt}, cat={cat_cnt}, prod={prod_cnt}, facts={fact_cnt}")
            return False
        print(f"PASS: Star Schema verified. fact_sales={fact_cnt}, dim_product={prod_cnt}, dim_store={stores_cnt}.")
        return True
    finally:
        con.close()


def check_idempotency():
    print("[5/7] Validating uniqueness and idempotency constraints...")
    con = duckdb.connect(DB_PATH, read_only=True)
    try:
        dups = con.execute("SELECT count(*) FROM (SELECT bill_no, line_no, count(*) FROM fact_sales GROUP BY bill_no, line_no HAVING count(*) > 1)").fetchone()[0]
        if dups != 0:
            print(f"FAIL: Found {dups} duplicate (bill_no, line_no) rows in fact_sales")
            return False
        print("PASS: Uniqueness constraint verified: 0 duplicates in fact_sales.")
        return True
    finally:
        con.close()


def check_data_quality():
    print("[6/7] Validating Data Quality rules...")
    con = duckdb.connect(DB_PATH, read_only=True)
    try:
        orphaned_stores = con.execute("SELECT count(*) FROM fact_sales f LEFT JOIN dim_store s ON f.store_key = s.store_key WHERE s.store_key IS NULL").fetchone()[0]
        invalid_types = con.execute("SELECT count(*) FROM fact_sales WHERE line_type NOT IN ('SALE', 'DISCOUNT', 'RETURN', 'VOID')").fetchone()[0]
        leaked_tender = con.execute("SELECT count(*) FROM fact_sales WHERE line_type IN ('TAX', 'TENDER')").fetchone()[0]

        if orphaned_stores != 0:
            print(f"FAIL: Found {orphaned_stores} orphaned store records")
            return False
        if invalid_types != 0 or leaked_tender != 0:
            print(f"FAIL: Invalid or leaked line types detected in fact_sales")
            return False
        print("PASS: Referential integrity and line-type filters verified.")
        return True
    finally:
        con.close()


def check_reconciliation():
    print("[7/7] Validating Finance Reconciliation...")
    con = duckdb.connect(DB_PATH, read_only=True)
    try:
        oct_rev = con.execute("SELECT ROUND(SUM(revenue), 2) FROM fact_sales WHERE sale_date >= '2024-10-01' AND sale_date < '2024-11-01'").fetchone()[0]
        if float(oct_rev) != 56359195.92:
            print(f"FAIL: October revenue is {oct_rev} (expected 56359195.92)")
            return False
        print(f"PASS: October revenue strictly reconciles at {oct_rev:.2f} INR.")
        return True
    finally:
        con.close()


def main():
    print("==================================================")
    print("ANNAPURNA STORES — SYSTEM VALIDATION SUITE")
    print("==================================================")
    checks = [
        check_docker(),
        check_postgres(),
        check_minio(),
        check_duckdb_schema(),
        check_idempotency(),
        check_data_quality(),
        check_reconciliation()
    ]
    all_passed = all(checks)
    os.makedirs(os.path.dirname(EVIDENCE_OUT), exist_ok=True)
    with open(EVIDENCE_OUT, "w", encoding="utf-8") as f:
        f.write("==================================================\n")
        f.write("ANNAPURNA STORES — VALIDATION OUTPUT\n")
        f.write("==================================================\n\n")
        f.write("Status: " + ("ALL TESTS PASSED" if all_passed else "VALIDATION FAILED") + "\n\n")
        f.write("Checks:\n")
        f.write(f"1. Docker Services        : {'PASS' if checks[0] else 'FAIL'}\n")
        f.write(f"2. PostgreSQL Masters     : {'PASS' if checks[1] else 'FAIL'}\n")
        f.write(f"3. MinIO Object Store     : {'PASS' if checks[2] else 'FAIL'}\n")
        f.write(f"4. DuckDB Star Schema     : {'PASS' if checks[3] else 'FAIL'}\n")
        f.write(f"5. Idempotency/Uniqueness : {'PASS' if checks[4] else 'FAIL'}\n")
        f.write(f"6. Data Quality           : {'PASS' if checks[5] else 'FAIL'}\n")
        f.write(f"7. Finance Reconciliation : {'PASS' if checks[6] else 'FAIL'}\n")

    print("\n==================================================")
    if all_passed:
        print("RESULT: ALL VALIDATION CHECKS PASSED (EXIT CODE 0)")
        print(f"Saved validation log to {EVIDENCE_OUT}")
        sys.exit(0)
    else:
        print("RESULT: ONE OR MORE CHECKS FAILED (EXIT CODE 1)")
        sys.exit(1)


if __name__ == "__main__":
    main()
