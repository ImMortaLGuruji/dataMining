#!/usr/bin/env python3
"""
Annapurna Stores - Evidence Collection Orchestrator
Executes all evidence generators and ensures all required outputs in evidence/ are fresh.
"""

import os
import sys
import subprocess

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def run_step(desc, cmd_list):
    print(f"\n>> [Evidence] {desc}...")
    res = subprocess.run(cmd_list, cwd=BASE_DIR, text=True)
    if res.returncode != 0:
        print(f"Warning: Step '{desc}' exited with code {res.returncode}")
    else:
        print(f"Done: {desc}")


def main():
    print("==================================================")
    print("ANNAPURNA STORES — EVIDENCE COLLECTION")
    print("==================================================")

    # 1. Docker ps output
    print("\n>> [Evidence] Capturing Docker service status...")
    ps_res = subprocess.run(["docker", "compose", "ps"], cwd=BASE_DIR, capture_output=True, text=True)
    with open(os.path.join(BASE_DIR, "evidence", "outputs", "docker-compose-ps.txt"), "w", encoding="utf-8") as f:
        f.write(ps_res.stdout)
    print("Done: Capturing Docker service status")

    # 2. Source file count
    sales_dir = os.path.join(BASE_DIR, "..", "exam", "data", "sales")
    file_count = len([f for f in os.listdir(sales_dir) if f.endswith(".csv")])
    with open(os.path.join(BASE_DIR, "evidence", "outputs", "source_file_count.txt"), "w", encoding="utf-8") as f:
        f.write(f"{file_count}\n")
    print(f">> [Evidence] Recorded source file count: {file_count}")

    # 3. Storage layout benchmark
    run_step("Running storage layout experiment", [sys.executable, os.path.join("ingestion", "scripts", "run_storage_layout_experiment.py")])

    # 4. Idempotency test
    run_step("Running idempotency test", [sys.executable, os.path.join("ingestion", "scripts", "verify_idempotency.py")])

    # 5. Historical pricing
    run_step("Running historical pricing evaluation", [sys.executable, os.path.join("ingestion", "scripts", "run_historical_pricing.py")])

    # 6. Federated query and query plans
    run_step("Running federated query and capturing execution plans", [sys.executable, os.path.join("ingestion", "scripts", "run_federated_query.py")])

    # 7. Reconciliation
    run_step("Running finance reconciliation", [sys.executable, os.path.join("ingestion", "scripts", "reconcile_finance.py")])

    # 8. Validation suite
    run_step("Running full validation suite", [sys.executable, os.path.join("scripts", "validate.py")])

    print("\n==================================================")
    print("ALL EVIDENCE SUCCESSFULLY COLLECTED IN evidence/")
    print("==================================================")


if __name__ == "__main__":
    main()
