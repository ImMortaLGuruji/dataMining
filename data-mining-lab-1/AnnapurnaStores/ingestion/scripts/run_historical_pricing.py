#!/usr/bin/env python3
"""
Annapurna Stores - Historical Pricing Evaluation
Runs the parameterized canonical revenue query for:
1. March 2024
2. Recent Period (November - December 2024)
Demonstrating that historical price revisions are resolved dynamically by reporting period.
Outputs evidence to evidence/outputs/historical-pricing.txt
"""

import os
import sys
import duckdb

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(BASE_DIR, "annapurna.duckdb")
EVIDENCE_PATH = os.path.join(BASE_DIR, "evidence", "outputs", "historical-pricing.txt")


def evaluate_pricing():
    con = duckdb.connect(DB_PATH, read_only=True)
    try:
        # Query A: March 2024
        query_march = """
            SELECT
                d.year,
                d.month,
                COUNT(DISTINCT f.bill_no) AS total_bills,
                COUNT(*) AS total_sales_lines,
                ROUND(SUM(f.quantity * f.unit_price), 2) AS till_revenue,
                ROUND(SUM(f.quantity * COALESCE(f.historical_price, f.unit_price)), 2) AS catalog_price_revenue,
                ROUND(SUM(f.revenue), 2) AS net_revenue
            FROM fact_sales f
            JOIN dim_date d ON f.date_key = d.date_key
            WHERE f.sale_date >= DATE '2024-03-01'
              AND f.sale_date <  DATE '2024-04-01'
            GROUP BY d.year, d.month;
        """
        march_res = con.execute(query_march).fetchall()[0]

        # Query B: Recent Period (Nov - Dec 2024)
        query_recent = """
            SELECT
                d.year,
                d.month,
                COUNT(DISTINCT f.bill_no) AS total_bills,
                COUNT(*) AS total_sales_lines,
                ROUND(SUM(f.quantity * f.unit_price), 2) AS till_revenue,
                ROUND(SUM(f.quantity * COALESCE(f.historical_price, f.unit_price)), 2) AS catalog_price_revenue,
                ROUND(SUM(f.revenue), 2) AS net_revenue
            FROM fact_sales f
            JOIN dim_date d ON f.date_key = d.date_key
            WHERE f.sale_date >= DATE '2024-11-01'
              AND f.sale_date <  DATE '2025-01-01'
            GROUP BY d.year, d.month
            ORDER BY d.year, d.month;
        """
        recent_res = con.execute(query_recent).fetchall()

        # Sample price revision comparison for products whose prices changed between March and Nov 2024
        price_diff_query = """
            SELECT
                p.product_code,
                p.product_name,
                pr_mar.selling_price AS price_march_2024,
                pr_nov.selling_price AS price_nov_2024,
                ROUND(pr_nov.selling_price - pr_mar.selling_price, 2) AS price_delta
            FROM dim_product p
            JOIN dim_price_revisions pr_mar
                ON p.product_key = pr_mar.product_sk
               AND DATE '2024-03-15' >= pr_mar.effective_from
               AND DATE '2024-03-15' <= pr_mar.effective_to
            JOIN dim_price_revisions pr_nov
                ON p.product_key = pr_nov.product_sk
               AND DATE '2024-11-15' >= pr_nov.effective_from
               AND DATE '2024-11-15' <= pr_nov.effective_to
            WHERE pr_nov.selling_price <> pr_mar.selling_price
            ORDER BY ABS(pr_nov.selling_price - pr_mar.selling_price) DESC
            LIMIT 10;
        """
        price_diffs = con.execute(price_diff_query).fetchall()

        os.makedirs(os.path.dirname(EVIDENCE_PATH), exist_ok=True)
        with open(EVIDENCE_PATH, "w", encoding="utf-8") as f:
            f.write("==================================================\n")
            f.write("ANNAPURNA STORES — HISTORICAL PRICING EVIDENCE\n")
            f.write("==================================================\n\n")

            f.write("QUERY A: MARCH 2024\n")
            f.write("Reporting Period: 2024-03-01 to 2024-04-01\n")
            f.write(f"Total Bills: {march_res[2]}\n")
            f.write(f"Sales Lines: {march_res[3]}\n")
            f.write(f"Till Revenue (INR): {march_res[4]}\n")
            f.write(f"Authoritative Catalog Revenue (INR): {march_res[5]}\n")
            f.write(f"Net Revenue (INR): {march_res[6]}\n\n")

            f.write("QUERY B: RECENT TWO-MONTH PERIOD (NOV - DEC 2024)\n")
            f.write("Reporting Period: 2024-11-01 to 2025-01-01\n")
            for r in recent_res:
                f.write(f"Month {r[0]}-{r[1]:02d}: Bills={r[2]}, Lines={r[3]}, Net Revenue={r[6]} INR\n")
            f.write("\n")

            f.write("SAMPLE PRICE REVISIONS (MARCH 2024 vs NOVEMBER 2024):\n")
            f.write(f"{'Code':<10} | {'March Price':<12} | {'Nov Price':<12} | {'Delta':<8} | {'Product Name'}\n")
            f.write("-" * 75 + "\n")
            for p in price_diffs:
                f.write(f"{p[0]:<10} | {p[2]:<12.2f} | {p[3]:<12.2f} | {p[4]:<8.2f} | {p[1]}\n")

        print(f"[Pricing] Evidence successfully generated at {EVIDENCE_PATH}")
    finally:
        con.close()


if __name__ == "__main__":
    evaluate_pricing()
