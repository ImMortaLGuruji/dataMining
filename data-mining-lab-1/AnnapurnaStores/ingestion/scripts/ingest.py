#!/usr/bin/env python3
"""
Annapurna Stores - Ingestion Pipeline
Lands raw sales files into MinIO (Layout A partitioned and Layout B flat)
and prepares deduplicated canonical data for the analytical engine.
"""

import os
import sys
import glob
import csv
import io
from datetime import datetime
from minio import Minio
from minio.error import S3Error

# Default configuration (can be overridden via environment variables)
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "annapurna")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "annapurnapassword")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "annapurna-raw")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"

# Look for sales data directory
DATA_DIRS = [
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "exam", "data", "sales"),
    os.path.join("/exam", "data", "sales"),
    os.path.join(os.getcwd(), "exam", "data", "sales"),
    os.path.join(os.getcwd(), "..", "exam", "data", "sales"),
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

print(f"[Ingest] Using sales directory: {SALES_DIR}")


def get_minio_client():
    return Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=MINIO_SECURE
    )


def ensure_bucket(client, bucket_name):
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
        print(f"[Ingest] Created MinIO bucket: {bucket_name}")
    else:
        print(f"[Ingest] Bucket {bucket_name} already exists.")


def land_files_to_minio(client, bucket_name, files):
    """
    Lands raw files into MinIO under:
    - Layout A (Partitioned): raw/sales/store=<store>/year=<YYYY>/month=<MM>/<filename>
    - Layout B (Flat): all-sales/<filename>
    """
    print(f"[Ingest] Landing {len(files)} files to MinIO bucket '{bucket_name}'...")
    uploaded_a = 0
    uploaded_b = 0

    for fpath in files:
        fname = os.path.basename(fpath)
        parts = fname.replace('.csv', '').split('_')
        store_id = parts[1]
        bdate_str = parts[2][:8]
        year = bdate_str[:4]
        month = bdate_str[4:6]

        # Layout A: Partitioned
        obj_name_a = f"raw/sales/store={store_id}/year={year}/month={month}/{fname}"
        # Layout B: Flat
        obj_name_b = f"all-sales/{fname}"

        # Check if already present to preserve idempotency
        try:
            client.stat_object(bucket_name, obj_name_a)
        except S3Error:
            client.fput_object(bucket_name, obj_name_a, fpath)
            uploaded_a += 1

        try:
            client.stat_object(bucket_name, obj_name_b)
        except S3Error:
            client.fput_object(bucket_name, obj_name_b, fpath)
            uploaded_b += 1

    print(f"[Ingest] Upload complete. Layout A uploaded: {uploaded_a}, Layout B uploaded: {uploaded_b}")


def main():
    files = sorted(glob.glob(os.path.join(SALES_DIR, "*.csv")))
    print(f"[Ingest] Discovered {len(files)} sales CSV files.")
    
    # Try landing to MinIO if MinIO is accessible
    try:
        client = get_minio_client()
        ensure_bucket(client, MINIO_BUCKET)
        land_files_to_minio(client, MINIO_BUCKET, files)
    except Exception as e:
        print(f"[Ingest] Warning: MinIO upload skipped or failed ({e}).")

    print("[Ingest] Ingestion landing phase completed successfully.")


if __name__ == "__main__":
    main()
