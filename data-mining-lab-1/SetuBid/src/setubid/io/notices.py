"""Notice dataset I/O module.

Supports reading notice batches from CSV or Parquet files into DuckDB
or Python dicts/DataFrames.
"""

from __future__ import annotations
import glob
import os
from typing import Dict, List, Optional, Any
import duckdb
import pandas as pd


def get_notice_files(notices_dir: str) -> List[str]:
    """Find all CSV or Parquet notice files in the target directory."""
    if not os.path.exists(notices_dir):
        raise FileNotFoundError(f"Notices directory does not exist: {notices_dir}")

    # Check for parquet first, then csv
    files = glob.glob(os.path.join(notices_dir, "*.parquet"))
    if not files:
        files = glob.glob(os.path.join(notices_dir, "*.csv"))
    files.sort()
    return files


def load_notices_table(conn: duckdb.DuckDBPyConnection, notices_dir: str, table_name: str = "raw_notices") -> int:
    """Load all notices from directory into a DuckDB table."""
    files = get_notice_files(notices_dir)
    if not files:
        raise FileNotFoundError(f"No parquet or csv notice files found in {notices_dir}")

    # Normalize path separators for DuckDB
    norm_files = [f.replace("\\", "/") for f in files]

    if norm_files[0].endswith(".parquet"):
        query = f"""
            CREATE OR REPLACE TABLE {table_name} AS 
            SELECT * FROM read_parquet({norm_files})
        """
    else:
        query = f"""
            CREATE OR REPLACE TABLE {table_name} AS 
            SELECT 
                notice_id::VARCHAR as notice_id,
                portal_id::VARCHAR as portal_id,
                published_at::VARCHAR as published_at,
                title::VARCHAR as title,
                body::VARCHAR as body,
                estimated_value::VARCHAR as estimated_value,
                closing_date::VARCHAR as closing_date
            FROM read_csv_auto({norm_files}, all_varchar=true)
        """
    conn.execute(query)
    count = conn.execute(f"SELECT count(*) FROM {table_name}").fetchone()[0]
    return count


def load_notices_dict(notices_dir: str) -> Dict[str, Dict[str, Any]]:
    """Load all notices into a dictionary indexed by notice_id."""
    conn = duckdb.connect()
    load_notices_table(conn, notices_dir, "temp_notices")
    df = conn.execute("SELECT * FROM temp_notices").fetchdf()
    conn.close()

    result = {}
    for row in df.itertuples(index=False):
        result[row.notice_id] = {
            "notice_id": row.notice_id,
            "portal_id": row.portal_id,
            "published_at": row.published_at,
            "title": row.title or "",
            "body": row.body or "",
            "estimated_value": row.estimated_value,
            "closing_date": row.closing_date
        }
    return result
