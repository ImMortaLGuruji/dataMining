Write-Host "=================================================="
Write-Host "Annapurna Stores — Full Platform Reset"
Write-Host "=================================================="
Set-Location -Path $PSScriptRoot\..

Write-Host "Stopping containers and removing volumes..."
docker compose down -v

Write-Host "Rebuilding and restarting stack..."
docker compose up -d

Write-Host "Waiting for services to become healthy..."
Start-Sleep -Seconds 10

Write-Host "Running ingestion..."
py ingestion/scripts/ingest.py
py ingestion/scripts/build_analytical_dataset.py

Write-Host "Running validation suite..."
py scripts/validate.py

Write-Host "Platform reset and validation complete."
