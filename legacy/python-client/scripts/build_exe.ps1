# Builds a single-file Windows executable for GitHub Releases.
# Usage (from repo root):  powershell -ExecutionPolicy Bypass -File scripts\build_exe.ps1
$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "             Building RiftWatch.exe Standalone            " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Run test suite
Write-Host "[*] Running test suite pre-flight..." -ForegroundColor Yellow
py -3.12 -m pytest -q
if ($LASTEXITCODE -ne 0) {
    Write-Error "Test suite failed! Aborting build."
    exit 1
}

# 2. Ensure multi-resolution Vector Rift Herald app.ico exists
Write-Host "[*] Verifying multi-resolution Vector Rift Herald app.ico..." -ForegroundColor Yellow
py -3.12 -c "
import os
from PIL import Image

assert os.path.exists('app.ico'), 'app.ico missing!'
img = Image.open('app.ico')
sizes = img.info.get('sizes', set())
print(f'Verified app.ico with sizes: {sorted(list(sizes))}')
assert (256, 256) in sizes and (16, 16) in sizes, 'app.ico missing required resolutions!'
"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Vector Rift Herald app.ico verification failed! Aborting build."
    exit 1
}

# 3. Clean previous build artifacts
Write-Host "[*] Cleaning previous build artifacts..." -ForegroundColor Yellow
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist\RiftWatch.exe") { Remove-Item -Force "dist\RiftWatch.exe" }

# 4. Run PyInstaller
Write-Host "[*] Invoking PyInstaller..." -ForegroundColor Yellow
py -3.12 -m PyInstaller --noconfirm RiftWatch.spec

$exe = "dist\RiftWatch.exe"
if (-not (Test-Path $exe)) {
    Write-Error "Build failed: $exe was not generated."
    exit 1
}

# 5. Generate SHA-256 Checksum
Write-Host "[*] Calculating SHA-256 checksum..." -ForegroundColor Yellow
$hash = (Get-FileHash $exe -Algorithm SHA256).Hash
"$hash  RiftWatch.exe" | Out-File -Encoding ascii "dist\SHA256SUMS.txt"

$sizeMb = [math]::Round((Get-Item $exe).Length / 1MB, 2)
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "Successfully built: $exe ($sizeMb MB)" -ForegroundColor Green
Write-Host "SHA-256: $hash" -ForegroundColor Green
Write-Host "Checksum file: dist\SHA256SUMS.txt" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
