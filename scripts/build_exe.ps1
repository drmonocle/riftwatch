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

# 2. Ensure multi-resolution app.ico exists
Write-Host "[*] Generating / verifying app.ico..." -ForegroundColor Yellow
py -3.12 -c "
from PIL import Image, ImageDraw
def make_icon():
    img = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((8, 8, 247, 247), fill=(9, 20, 40, 255), outline=(200, 170, 110, 255), width=16)
    d.ellipse((24, 24, 231, 231), outline=(30, 42, 56, 255), width=4)
    diamond = [(128, 48), (208, 128), (128, 208), (48, 128)]
    d.polygon(diamond, outline=(10, 200, 185, 255), width=16)
    d.ellipse((104, 104, 152, 152), fill=(200, 170, 110, 255), outline=(240, 230, 210, 255), width=4)
    return img

icon = make_icon()
icon.save('app.ico', format='ICO', sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
"

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
