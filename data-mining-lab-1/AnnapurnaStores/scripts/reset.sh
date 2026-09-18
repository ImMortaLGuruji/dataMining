#!/usr/bin/env bash
set -e
echo "=================================================="
echo "Annapurna Stores — Full Platform Reset"
echo "=================================================="
cd "$(dirname "$0")/.."

echo "Stopping containers and removing volumes..."
docker compose down -v

echo "Rebuilding and restarting stack..."
docker compose up -d

echo "Waiting for services to become healthy..."
sleep 10

echo "Running ingestion..."
python3 ingestion/scripts/ingest.py || python ingestion/scripts/ingest.py || py ingestion/scripts/ingest.py
python3 ingestion/scripts/build_analytical_dataset.py || python ingestion/scripts/build_analytical_dataset.py || py ingestion/scripts/build_analytical_dataset.py

echo "Running validation suite..."
python3 scripts/validate.py || python scripts/validate.py || py scripts/validate.py

echo "Platform reset and validation complete."
