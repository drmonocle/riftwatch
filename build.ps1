# Builds the Vite frontend. Run from anywhere; paths are relative to this script.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "Building Vite frontend..."
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Error "Vite build failed!"
    exit 1
}

Write-Host "Vite build succeeded!"
