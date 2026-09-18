#!/usr/bin/env bash
set -e
echo "=================================================="
echo "Annapurna Stores — Pipeline Ingestion"
echo "=================================================="
cd "$(dirname "$0")/.."

echo "Step 1: Landing raw files to MinIO object store..."
python3 ingestion/scripts/ingest.py || python ingestion/scripts/ingest.py || py ingestion/scripts/ingest.py

echo "Step 2: Building analytical dataset in DuckDB..."
python3 ingestion/scripts/build_analytical_dataset.py || python ingestion/scripts/build_analytical_dataset.py || py ingestion/scripts/build_analytical_dataset.py

echo "Ingestion completed successfully."
