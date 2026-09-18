Write-Host "Stopping Annapurna Stores Platform..."
Set-Location -Path $PSScriptRoot\..
docker compose stop
Write-Host "Platform stopped."
