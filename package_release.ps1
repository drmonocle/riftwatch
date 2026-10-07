Set-ExecutionPolicy -Scope Process Bypass -Force
$xwinBin = "C:\Users\TV\.xwin\bin"
$cargoPath = "C:\Users\TV\.cargo\bin"
$nodePath = "C:\Users\TV\AppData\Local\Microsoft\WinGet\Packages\OpenJS.NodeJS.LTS_Microsoft.Winget.Source_8wekyb3d8bbwe\node-v24.19.0-win-x64"
$llvmPath = "C:\Users\TV\AppData\Local\Microsoft\WinGet\Packages\MartinStorsjo.LLVM-MinGW.UCRT_Microsoft.Winget.Source_8wekyb3d8bbwe\llvm-mingw-20260616-ucrt-x86_64\bin"
$env:Path = "$xwinBin;$cargoPath;$nodePath;$llvmPath;$env:Path"

Write-Host "1. Killing running RiftWatch processes..."
Get-Process -Name "RiftWatch*", "riftwatch*" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Milliseconds 500

Write-Host "2. Building Tauri binary with cargo release..."
Push-Location "C:\Users\TV\Documents\antigravity\quirky-pascal\rift-scout\src-tauri"
cargo build --release
if ($LASTEXITCODE -ne 0) {
    Pop-Location
    Write-Error "Cargo build failed!"
    exit 1
}
Pop-Location

$srcExe = "C:\Users\TV\Documents\antigravity\quirky-pascal\rift-scout\src-tauri\target\release\riftwatch-tauri.exe"
if (-not (Test-Path $srcExe)) {
    Write-Error "Binary not found at $srcExe"
    exit 1
}

$fileSizeMb = [math]::Round(((Get-Item $srcExe).Length / 1MB), 2)
Write-Host "Binary built successfully! Size: $fileSizeMb MB"

Write-Host "3. Deploying binaries..."
Copy-Item -Path $srcExe -Destination "C:\Users\TV\Documents\antigravity\quirky-pascal\rift-scout\RiftWatch.exe" -Force
if (-not (Test-Path "C:\Users\TV\Documents\antigravity\quirky-pascal\rift-scout\release")) {
    New-Item -ItemType Directory -Path "C:\Users\TV\Documents\antigravity\quirky-pascal\rift-scout\release" -Force
}
Copy-Item -Path $srcExe -Destination "C:\Users\TV\Documents\antigravity\quirky-pascal\rift-scout\release\RiftWatch.exe" -Force
Copy-Item -Path $srcExe -Destination "C:\Users\TV\Desktop\RiftWatch.exe" -Force

Write-Host "4. Creating release zip..."
Compress-Archive -Path $srcExe -DestinationPath "C:\Users\TV\Documents\antigravity\quirky-pascal\rift-scout\RiftWatch-v0.3.6-windows-x64.zip" -Force

Write-Host "5. Launching updated RiftWatch on Desktop..."
Start-Process "C:\Users\TV\Desktop\RiftWatch.exe"
Start-Sleep -Seconds 2

$proc = Get-Process -Name "RiftWatch" -ErrorAction SilentlyContinue
if ($proc) {
    $wsMb = [math]::Round($proc.WorkingSet64 / 1MB, 2)
    Write-Host "RiftWatch running! PID: $($proc.Id), Memory: $wsMb MB"
} else {
    Write-Warning "Process check did not find RiftWatch running"
}
