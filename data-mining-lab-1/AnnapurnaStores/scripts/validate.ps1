Set-Location -Path $PSScriptRoot\..
py scripts/validate.py
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
