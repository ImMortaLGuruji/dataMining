#!/usr/bin/env python3
"""
Annapurna Stores - Federated Cross-System Query
Executes a query joining sales files in MinIO (S3) directly with master tables
in PostgreSQL via DuckDB's httpfs and postgres extensions.
Captures EXPLAIN and EXPLAIN ANALYZE execution plans and writes evidence.
"""

import os
import sys
import duckdb

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EVIDENCE_OUTPUT = os.path.join(BASE_DIR, "evidence", "outputs", "federated-query.txt")
EVIDENCE_PLAN = os.path.join(BASE_DIR, "evidence", "query-plans", "federated-plan.txt")


def run_federation():
    con = duckdb.connect()  # in-memory DuckDB instance to ensure no local tables are pre-materialized
    try:
        print("[Federation] Initializing httpfs and postgres extensions...")
        con.execute("INSTALL httpfs; LOAD httpfs;")
        con.execute("INSTALL postgres; LOAD postgres;")

        con.execute("""
            SET s3_endpoint='localhost:9000';
            SET s3_access_key_id='annapurna';
            SET s3_secret_access_key='annapurnapassword';
            SET s3_use_ssl=false;
            SET s3_url_style='path';
        """)

        print("[Federation] Attaching operational PostgreSQL masters...")
        con.execute("ATTACH 'dbname=annapurna user=annapurna password=annapurnapassword host=localhost port=5432' AS pg_db (TYPE postgres);")

        federated_sql = """
            SELECT
                s.store_name,
                s.city,
                c.category_name,
                c.department,
                COUNT(DISTINCT raw_sales.column0) AS total_bills,
                SUM(CAST(raw_sales.column3 AS DECIMAL(12,2))) AS total_quantity,
                ROUND(SUM(CAST(raw_sales.column3 AS DECIMAL(12,2)) * CAST(raw_sales.column4 AS DECIMAL(12,2))), 2) AS total_revenue
            FROM read_csv('s3://annapurna-raw/raw/sales/store=S01/year=2024/month=03/*.csv',
                header=True,
                columns={
                    'column0': 'VARCHAR',
                    'column1': 'INTEGER',
                    'column2': 'VARCHAR',
                    'column3': 'VARCHAR',
                    'column4': 'VARCHAR',
                    'column5': 'VARCHAR',
                    'column6': 'VARCHAR'
                }
            ) AS raw_sales
            JOIN pg_db.stores s
                ON s.store_id = 'S01'
            JOIN pg_db.products p
                ON raw_sales.column2 = p.product_code
               AND DATE '2024-03-15' >= p.valid_from
               AND DATE '2024-03-15' <= p.valid_to
            JOIN pg_db.product_categories c
                ON p.category_id = c.category_id
            WHERE raw_sales.column5 IN ('SALE', 'DISCOUNT', 'RETURN', 'VOID')
            GROUP BY
                s.store_name,
                s.city,
                c.category_name,
                c.department
            ORDER BY total_revenue DESC;
        """

        print("[Federation] Capturing EXPLAIN plan...")
        explain_res = con.execute("EXPLAIN " + federated_sql).fetchall()
        explain_text = "\n".join([f"{r[0]}: {r[1]}" for r in explain_res])

        print("[Federation] Capturing EXPLAIN ANALYZE plan...")
        analyze_res = con.execute("EXPLAIN ANALYZE " + federated_sql).fetchall()
        analyze_text = "\n".join([f"{r[0]}: {r[1]}" for r in analyze_res])

        print("[Federation] Executing federated query...")
        query_results = con.execute(federated_sql).fetchall()

        # Write output evidence
        os.makedirs(os.path.dirname(EVIDENCE_OUTPUT), exist_ok=True)
        with open(EVIDENCE_OUTPUT, "w", encoding="utf-8") as f:
            f.write("==================================================\n")
            f.write("ANNAPURNA STORES — FEDERATED CROSS-SYSTEM QUERY\n")
            f.write("==================================================\n\n")
            f.write("QUERY EXECUTED:\n")
            f.write(federated_sql.strip() + "\n\n")
            f.write("SOURCES JOINED DYNAMICALLY:\n")
            f.write("1. MinIO Object Store: s3://annapurna-raw/raw/sales/store=S01/year=2024/month=03/*.csv\n")
            f.write("2. PostgreSQL Masters: pg_db.stores, pg_db.products, pg_db.product_categories\n\n")
            f.write("RESULTS (Store S01 - March 2024 Category Revenue):\n")
            f.write(f"{'Store':<22} | {'Category':<22} | {'Department':<10} | {'Quantity':<10} | {'Revenue (INR)'}\n")
            f.write("-" * 85 + "\n")
            for r in query_results:
                f.write(f"{r[0]:<22} | {r[2]:<22} | {r[3]:<10} | {r[5]:<10.2f} | {r[6]:<12.2f}\n")

        # Write query plan evidence
        os.makedirs(os.path.dirname(EVIDENCE_PLAN), exist_ok=True)
        with open(EVIDENCE_PLAN, "w", encoding="utf-8") as f:
            f.write("==================================================\n")
            f.write("FEDERATED QUERY EXECUTION PLAN (EXPLAIN)\n")
            f.write("==================================================\n\n")
            f.write(explain_text + "\n\n")
            f.write("==================================================\n")
            f.write("FEDERATED QUERY EXECUTION PLAN (EXPLAIN ANALYZE)\n")
            f.write("==================================================\n\n")
            f.write(analyze_text + "\n")

        print(f"[Federation] Saved output to {EVIDENCE_OUTPUT}")
        print(f"[Federation] Saved plan to {EVIDENCE_PLAN}")

    finally:
        con.close()


if __name__ == "__main__":
    run_federation()
