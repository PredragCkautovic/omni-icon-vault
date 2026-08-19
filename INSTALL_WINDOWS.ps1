$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 install.py @args
    exit $LASTEXITCODE
}
if (Get-Command python -ErrorAction SilentlyContinue) {
    & python install.py @args
    exit $LASTEXITCODE
}
Write-Error "Python 3.10+ is required. Install Python, then rerun this script."
