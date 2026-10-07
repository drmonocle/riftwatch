<#
.SYNOPSIS
    RiftWatch 1-Click Updater Script
.DESCRIPTION
    Checks GitHub Releases for the latest RiftWatch binary, verifies SHA-256 hash,
    and updates the local installation.
#>

[CmdletBinding()]
param (
    [string]$Repo = "drmonocle/rift-scout",
    [string]$InstallDir = "$env:LOCALAPPDATA\Programs\RiftWatch"
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "             RiftWatch Automated Updater                  " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$ReleaseApi = "https://api.github.com/repos/$Repo/releases/latest"
Write-Host "[*] Checking for updates from $ReleaseApi..." -ForegroundColor DarkGray

try {
    $Release = Invoke-RestMethod -Uri $ReleaseApi -Headers @{ "User-Agent" = "RiftWatch-Updater" }
} catch {
    Write-Warning "Could not connect to GitHub API or repo not published yet: $_"
    return
}

$LatestTag = $Release.tag_name
Write-Host "[+] Latest Release Available: $LatestTag" -ForegroundColor Green

$ExeAsset = $Release.assets | Where-Object { $_.name -like "*.exe" } | Select-Object -First 1
if (-not $ExeAsset) {
    Write-Warning "No .exe asset found in release $LatestTag."
    return
}
$SumAsset = $Release.assets | Where-Object { $_.name -like "*SHA256*" } | Select-Object -First 1
if (-not $SumAsset) {
    Write-Warning "Release $LatestTag has no SHA256SUMS file, so it can't be verified. Not installing."
    return
}

$DownloadUrl = $ExeAsset.browser_download_url
$TempExe = "$env:TEMP\RiftWatch_$LatestTag.exe"

Write-Host "[*] Downloading $($ExeAsset.name) from $DownloadUrl..." -ForegroundColor Yellow
Invoke-WebRequest -Uri $DownloadUrl -OutFile $TempExe -UserAgent "RiftWatch-Updater"

if (-not (Test-Path $TempExe)) {
    Write-Error "Download failed. File not found at $TempExe"
    return
}

$Sums = (Invoke-WebRequest -Uri $SumAsset.browser_download_url -UserAgent "RiftWatch-Updater" -UseBasicParsing).Content
if ($Sums -is [byte[]]) { $Sums = [System.Text.Encoding]::UTF8.GetString($Sums) }
$Expected = $null
foreach ($line in ($Sums -split "`n")) {
    $parts = $line.Trim() -split '\s+'
    if ($parts.Count -ge 2 -and $parts[-1].TrimStart('*') -ieq $ExeAsset.name) { $Expected = $parts[0].ToUpper() }
}
$Actual = (Get-FileHash -Path $TempExe -Algorithm SHA256).Hash.ToUpper()
if (-not $Expected -or $Actual -ne $Expected) {
    Remove-Item -Path $TempExe -Force -ErrorAction SilentlyContinue
    Write-Error "Checksum verification failed (expected $Expected, got $Actual). The download was deleted."
    return
}
Write-Host "[+] SHA-256 verified: $Actual" -ForegroundColor Green

# Stop running RiftWatch processes if any
$RunningProc = Get-Process -Name "RiftWatch" -ErrorAction SilentlyContinue
if ($RunningProc) {
    Write-Host "[*] Stopping running RiftWatch process..." -ForegroundColor Yellow
    $RunningProc | Stop-Process -Force
    Start-Sleep -Milliseconds 500
}

# Determine target path
$TargetPath = "$InstallDir\RiftWatch.exe"
if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
}

Copy-Item -Path $TempExe -Destination $TargetPath -Force
Remove-Item -Path $TempExe -Force -ErrorAction SilentlyContinue

Write-Host "[✓] Successfully updated RiftWatch to $LatestTag at $TargetPath" -ForegroundColor Green
Write-Host "[*] Launching updated RiftWatch..." -ForegroundColor Cyan
Start-Process -FilePath $TargetPath -WindowStyle Normal
