Write-Host "=================================================="
Write-Host "Annapurna Stores — Pipeline Ingestion"
Write-Host "=================================================="
Set-Location -Path $PSScriptRoot\..

Write-Host "Step 1: Landing raw files to MinIO object store..."
py ingestion/scripts/ingest.py

Write-Host "Step 2: Building analytical dataset in DuckDB..."
py ingestion/scripts/build_analytical_dataset.py

Write-Host "Ingestion completed successfully."
