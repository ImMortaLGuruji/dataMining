#!/usr/bin/env python3
"""
Annapurna Stores - Idempotency Verification
Runs the analytical pipeline 3 times and measures:
- Row count
- Deterministic MD5 checksum across canonical ordered records
Outputs the exact measurements to evidence/checksums/idempotency.txt
"""

import os
import sys
import hashlib
import duckdb

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EVIDENCE_PATH = os.path.join(BASE_DIR, "evidence", "checksums", "idempotency.txt")
BUILD_SCRIPT = os.path.join(BASE_DIR, "ingestion", "scripts", "build_analytical_dataset.py")
DB_PATH = os.path.join(BASE_DIR, "annapurna.duckdb")


def compute_table_checksum(db_path):
    con = duckdb.connect(db_path, read_only=True)
    try:
        # Row count
        row_count = con.execute("SELECT count(*) FROM fact_sales").fetchone()[0]

        # Deterministic MD5 Checksum
        # Ordered by bill_no, line_no (stable unique business key)
        query = """
            SELECT md5(string_agg(
                concat_ws('|',
                    bill_no,
                    CAST(line_no AS TEXT),
                    store_key,
                    CAST(product_key AS TEXT),
                    CAST(sale_date AS TEXT),
                    CAST(ROUND(quantity, 2) AS TEXT),
                    CAST(ROUND(unit_price, 2) AS TEXT),
                    CAST(ROUND(revenue, 2) AS TEXT),
                    line_type
                ),
                chr(10)
                ORDER BY bill_no, line_no
            )) AS table_checksum
            FROM fact_sales;
        """
        checksum = con.execute(query).fetchone()[0]
        return row_count, checksum
    finally:
        con.close()


def run_pipeline():
    # Import and run the build script
    import subprocess
    cmd = [sys.executable, BUILD_SCRIPT]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error running pipeline: {res.stderr}")
        raise RuntimeError("Pipeline failed to execute")


def main():
    print("==================================================")
    print("ANNAPURNA STORES — IDEMPOTENCY VERIFICATION")
    print("==================================================")

    runs = []
    for i in range(1, 4):
        print(f"\n--- RUN {i} ---")
        print("Executing pipeline...")
        run_pipeline()
        row_count, checksum = compute_table_checksum(DB_PATH)
        print(f"Run {i} Row count: {row_count}")
        print(f"Run {i} Checksum : {checksum}")
        runs.append((row_count, checksum))

    rc1, cs1 = runs[0]
    rc2, cs2 = runs[1]
    rc3, cs3 = runs[2]

    rc_identical = (rc1 == rc2 == rc3)
    cs_identical = (cs1 == cs2 == cs3)

    print("\n--- COMPARISON ---")
    print(f"Row counts identical: {'YES' if rc_identical else 'NO'}")
    print(f"Checksums identical : {'YES' if cs_identical else 'NO'}")

    # Write evidence file
    os.makedirs(os.path.dirname(EVIDENCE_PATH), exist_ok=True)
    with open(EVIDENCE_PATH, "w", encoding="utf-8") as f:
        f.write("==================================================\n")
        f.write("ANNAPURNA STORES — IDEMPOTENCY TEST\n")
        f.write("==================================================\n\n")

        f.write("RUN 1\n")
        f.write(f"Command:\n{sys.executable} {BUILD_SCRIPT}\n\n")
        f.write(f"Row count:\n{rc1}\n\n")
        f.write(f"Checksum:\n{cs1}\n\n\n")

        f.write("RUN 2\n")
        f.write(f"Command:\n{sys.executable} {BUILD_SCRIPT}\n\n")
        f.write(f"Row count:\n{rc2}\n\n")
        f.write(f"Checksum:\n{cs2}\n\n\n")

        f.write("RUN 3\n")
        f.write(f"Command:\n{sys.executable} {BUILD_SCRIPT}\n\n")
        f.write(f"Row count:\n{rc3}\n\n")
        f.write(f"Checksum:\n{cs3}\n\n\n")

        f.write("COMPARISON\n")
        f.write("----------\n\n")
        f.write(f"Row counts identical:\n{'YES' if rc_identical else 'NO'}\n\n")
        f.write(f"Checksums identical:\n{'YES' if cs_identical else 'NO'}\n")

    print(f"\nSaved idempotency evidence to {EVIDENCE_PATH}")


if __name__ == "__main__":
    main()
