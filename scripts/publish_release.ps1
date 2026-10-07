<#
.SYNOPSIS
    RiftWatch GitHub Release Publisher
.DESCRIPTION
    Builds (or verifies) the RiftWatch standalone executable and publishes a new
    GitHub Release with binary and SHA256SUMS assets attached.
.PARAMETER Tag
    The git release tag, e.g. "v0.2.0" (defaults to the version in riftscout/__init__.py).
#>

[CmdletBinding()]
param (
    [string]$Tag = ""
)

$ErrorActionPreference = "Stop"
$env:PATH = "C:\Program Files\Git\cmd;C:\Program Files\GitHub CLI;$env:PATH"

if (-not $Tag) {
    $ver = (py -3.12 -c "import riftscout; print(riftscout.__version__)").Trim()
    $Tag = "v$ver"
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "       Publishing RiftWatch Release $Tag to GitHub        " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Verify gh is available and authenticated
Write-Host "[*] Checking GitHub CLI authentication..." -ForegroundColor DarkGray
$ghStatus = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "GitHub CLI is not authenticated. Run 'gh auth login' first."
    exit 1
}

# 2. Check if assets exist; build if missing
$exe = "dist\RiftWatch.exe"
$sums = "dist\SHA256SUMS.txt"
if (-not (Test-Path $exe) -or -not (Test-Path $sums)) {
    Write-Host "[*] Assets missing in dist\. Triggering build..." -ForegroundColor Yellow
    powershell -ExecutionPolicy Bypass -File scripts\build_exe.ps1
}

$hash = (Get-Content $sums | Select-Object -First 1).Split()[0]

# 3. Release Notes Body
$notes = @"
## RiftWatch $Tag - Windows Desktop Esports Sentinel

A dedicated, lightweight Windows desktop tracker and sentinel for League of Legends pro esports and the 24/7 Twitch rebroadcast channel.

### ✨ What's New
* **First-Run Onboarding Setup Wizard:** 1-click setup dialog to follow your favorite regions, pro teams, and star players on first launch.
* **Regions & Tournaments:** Dedicated Regions tab to follow entire competitive ecosystems (International, Korea, China, Europe, North America, APAC, Brazil).
* **System Tray Sentinel:** Runs quietly in the notification area with close-to-tray minimization, spoiler mode toggle, and schedule refresh.
* **Team Crest Logos:** Crisp logos across player cards, starting lineups, and 24/7 Twitch rebroadcast cards.
* **Live In-Game Stats:** Gold lead tracking, kill scoreboards, towers, dragons, barons, inhibitors, and starting champions.
* **Twitch 24/7 Rebroadcast Sync:** Integrated live playout schedule and S-Tier Banger highlights.
* **1-Click Verified Self-Updater:** Automatically checks GitHub Releases and verifies SHA-256 checksums before swapping binaries.

### 📦 Checksums & Integrity
* **Executable:** \`RiftWatch.exe\`
* **SHA-256 Hash:** \`$hash\`
"@

# 4. Create GitHub Release
Write-Host "[*] Creating GitHub Release $Tag..." -ForegroundColor Cyan
gh release create $Tag $exe $sums --title "RiftWatch $Tag" --notes $notes

Write-Host "==========================================================" -ForegroundColor Green
Write-Host "Release published successfully!" -ForegroundColor Green
Write-Host "URL: https://github.com/drmonocle/rift-scout/releases/tag/$Tag" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
