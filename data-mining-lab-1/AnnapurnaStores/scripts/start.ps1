Write-Host "Starting Annapurna Stores Platform..."
Set-Location -Path $PSScriptRoot\..
docker compose up -d
Write-Host "Checking service status..."
docker compose ps
Write-Host "Platform started successfully."
