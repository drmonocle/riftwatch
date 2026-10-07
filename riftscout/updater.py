"""
RiftScout Self-Updater
Checks GitHub Releases for a newer version, downloads the .exe asset,
verifies it against the release's SHA256SUMS file, and swaps it in.

The swap/restart only applies to the packaged .exe. When running from source,
update with `git pull` instead.
"""

import hashlib
import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

from . import __version__
from . import config as C
from . import net

log = logging.getLogger(__name__)


class UpdateError(Exception):
    pass


def is_frozen() -> bool:
    """True when running as the PyInstaller-built executable."""
    return bool(getattr(sys, "frozen", False))


def parse_version(v: str) -> Tuple[int, ...]:
    nums = re.findall(r"\d+", v or "")
    parts = [int(n) for n in nums[:3]]
    return tuple(parts + [0] * (3 - len(parts))) if parts else (0, 0, 0)


def check_for_updates(current: str = __version__) -> Optional[Dict[str, Any]]:
    """Return metadata for a newer GitHub release, or None."""
    if not C.GITHUB_REPO:
        return None
    release = net.fetch_json(C.GITHUB_LATEST_RELEASE_URL, timeout=8.0, max_retries=1)
    if not isinstance(release, dict):
        return None
    tag = str(release.get("tag_name") or "").strip()
    if parse_version(tag) <= parse_version(current):
        return None
    exe_asset = sha_asset = None
    for asset in release.get("assets") or []:
        name = (asset.get("name") or "").lower()
        if name.endswith(".exe"):
            exe_asset = asset
        elif "sha256" in name:
            sha_asset = asset
    return {
        "tag": tag,
        "html_url": release.get("html_url") or C.GITHUB_PROJECT_URL,
        "asset_url": (exe_asset or {}).get("browser_download_url"),
        "asset_name": (exe_asset or {}).get("name") or "RiftWatch.exe",
        "sha_url": (sha_asset or {}).get("browser_download_url"),
        "body": release.get("body") or "",
        "published_at": release.get("published_at") or "",
    }


def calculate_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(128 * 1024):
            h.update(chunk)
    return h.hexdigest().upper()


def parse_sha256sums(text: str, filename: str) -> Optional[str]:
    """Find the hash for `filename` in a `HASH  name` checksum file."""
    for line in (text or "").splitlines():
        parts = line.strip().split()
        if len(parts) >= 2 and parts[-1].lstrip("*").lower() == filename.lower():
            if re.fullmatch(r"[0-9a-fA-F]{64}", parts[0]):
                return parts[0].upper()
    return None


def download_update(update_info: Dict[str, Any],
                    progress_callback: Optional[Callable[[int, int], None]] = None) -> Path:
    """Download and verify the release exe. Raises UpdateError on any problem."""
    url, sha_url = update_info.get("asset_url"), update_info.get("sha_url")
    name = update_info.get("asset_name") or "RiftWatch.exe"
    if not url:
        raise UpdateError("This release has no Windows executable attached.")
    if not sha_url:
        raise UpdateError("This release has no SHA256SUMS file, so it can't be verified.")

    sums = net.fetch_bytes(sha_url, timeout=15.0)
    expected = parse_sha256sums(sums.decode("utf-8", "replace") if sums else "", name)
    if not expected:
        raise UpdateError(f"No checksum for {name} in the release's SHA256SUMS file.")

    dest = C.UPDATES_DIR / f"RiftWatch_{re.sub(r'[^0-9A-Za-z._-]', '', update_info.get('tag', 'new'))}.exe"
    if not net.download_file(url, str(dest), progress_callback=progress_callback):
        raise UpdateError("Download failed. Check your connection and try again.")
    actual = calculate_sha256(dest)
    if actual != expected:
        try:
            dest.unlink()
        except OSError:
            pass
        raise UpdateError("Downloaded file failed checksum verification and was deleted.")
    return dest


def launch_swap_and_restart(new_exe: Path) -> None:
    """Start a hidden helper that waits for this process to exit, replaces the
    running exe with `new_exe`, and relaunches it. The caller must then quit."""
    if not is_frozen():
        raise UpdateError("Running from source: update with `git pull` instead.")
    current_exe = Path(sys.executable).resolve()
    new_exe = Path(new_exe).resolve()
    pid = os.getpid()

    log_file = C.APPDATA_DIR / "update.log"
    script_path = C.APPDATA_DIR / "apply_update.ps1"

    ps_script = """param(
    [Parameter(Mandatory=$true)][string]$CurrentExe,
    [Parameter(Mandatory=$true)][string]$NewExe,
    [Parameter(Mandatory=$true)][int]$OldPid,
    [Parameter(Mandatory=$true)][string]$LogFile
)

$ErrorActionPreference = 'Continue'

function Log($m) {
    $t = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    "$t $m" | Out-File -FilePath $LogFile -Append -Encoding utf8
}

Log "=== RiftWatch Update Helper Started ==="
Log "Target Current Exe: $CurrentExe"
Log "Source New Exe: $NewExe"
Log "Old PID: $OldPid"

# 1. Wait for old process to exit
Log "Waiting for old PID $OldPid to exit..."
try {
    Wait-Process -Id $OldPid -Timeout 15 -ErrorAction SilentlyContinue
} catch {
    Log "Wait-Process error: $($_.Exception.Message)"
}

# 2. Ensure any lingering instances exit cleanly
$waited = 0
while ($waited -lt 15) {
    $procs = Get-Process -ErrorAction SilentlyContinue | Where-Object {
        $_.Id -ne $PID -and ($_.Id -eq $OldPid -or $_.Name -like "*RiftWatch*" -or $_.Name -like "*RiftScout*")
    }
    if (-not $procs) { break }
    Start-Sleep -Milliseconds 500
    $waited += 0.5
}

$procs = Get-Process -ErrorAction SilentlyContinue | Where-Object {
    $_.Id -ne $PID -and ($_.Id -eq $OldPid -or $_.Name -like "*RiftWatch*" -or $_.Name -like "*RiftScout*")
}
if ($procs) {
    Log "Force-stopping lingering processes..."
    $procs | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

# 3. Two-step atomic file swap with retries
$oldBackup = "$CurrentExe.old"
if (Test-Path -LiteralPath $oldBackup) {
    Remove-Item -LiteralPath $oldBackup -Force -ErrorAction SilentlyContinue
}

$replaced = $false
for ($i = 1; $i -le 30; $i++) {
    try {
        if (Test-Path -LiteralPath $CurrentExe) {
            Move-Item -LiteralPath $CurrentExe -Destination $oldBackup -Force -ErrorAction Stop
        }
        Move-Item -LiteralPath $NewExe -Destination $CurrentExe -Force -ErrorAction Stop
        $replaced = $true
        Log "File swapped successfully on attempt $i"
        break
    } catch {
        Log "Attempt $i failed: $($_.Exception.Message)"
        Start-Sleep -Milliseconds 500
    }
}

if ($replaced) {
    if (Test-Path -LiteralPath $oldBackup) {
        Remove-Item -LiteralPath $oldBackup -Force -ErrorAction SilentlyContinue
    }
} else {
    Log "ERROR: Failed to swap executable after 30 attempts!"
    if ((Test-Path -LiteralPath $oldBackup) -and (-not (Test-Path -LiteralPath $CurrentExe))) {
        Move-Item -LiteralPath $oldBackup -Destination $CurrentExe -Force -ErrorAction SilentlyContinue
    }
}

# 4. Relaunch the updated executable in normal interactive desktop window state
if ($replaced -and (Test-Path -LiteralPath $CurrentExe)) {
    Log "Launching updated executable: $CurrentExe"
    Start-Sleep -Seconds 1
    $proc = Start-Process -FilePath $CurrentExe -WindowStyle Normal -PassThru
    Log "Successfully launched new process PID: $($proc.Id)"
}

Log "=== RiftWatch Update Helper Completed ==="
"""
    try:
        script_path.write_text(ps_script, encoding="utf-8")
    except Exception as exc:
        log.warning("Could not write apply_update.ps1 to disk: %s", exc)

    flags = 0
    if sys.platform == "win32":
        flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP

    cmd = [
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-WindowStyle", "Hidden",
        "-File", str(script_path),
        "-CurrentExe", str(current_exe),
        "-NewExe", str(new_exe),
        "-OldPid", str(pid),
        "-LogFile", str(log_file),
    ]

    subprocess.Popen(cmd, creationflags=flags, close_fds=True)
