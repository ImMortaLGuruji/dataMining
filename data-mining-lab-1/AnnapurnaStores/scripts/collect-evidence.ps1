Set-Location -Path $PSScriptRoot\..
py scripts/collect-evidence.py
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
