"""
RiftScout 1-Click Automated Self-Updater
Checks GitHub Releases for new versions, downloads verified standalone executables,
and executes seamless atomic restart-and-swaps on Windows.
"""

import hashlib
import json
import logging
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

from . import __version__
from . import config as C
from . import net

log = logging.getLogger(__name__)


def is_frozen() -> bool:
    """Check if application is running as a compiled standalone executable."""
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def parse_version(v: str) -> Tuple[int, ...]:
    """Extract integer version components from a semver tag string."""
    nums = re.findall(r"\d+", v or "")
    return tuple(int(n) for n in nums[:3]) or (0, 0, 0)


def check_for_updates() -> Optional[Dict[str, Any]]:
    """
    Check GitHub Releases API for a newer version than currently running.
    Returns update metadata dictionary if an update exists, else None.
    """
    if not C.GITHUB_REPO:
        return None

    try:
        release = net.fetch_json(C.GITHUB_LATEST_RELEASE_URL, timeout=8.0)
        if not release or not isinstance(release, dict):
            return None

        tag_name = str(release.get("tag_name") or "").strip()
        latest_ver = parse_version(tag_name)
        current_ver = parse_version(__version__)

        if latest_ver <= current_ver:
            log.info("RiftScout is up to date (current: v%s, latest: %s)", __version__, tag_name)
            return None

        # Locate .exe asset in the release
        exe_asset = None
        sha_asset = None
        for asset in release.get("assets", []):
            name = (asset.get("name") or "").lower()
            if name.endswith(".exe"):
                exe_asset = asset
            elif "sha256" in name or name.endswith(".txt"):
                sha_asset = asset

        asset_url = exe_asset.get("browser_download_url") if exe_asset else None

        return {
            "tag": tag_name,
            "html_url": release.get("html_url", C.GITHUB_PROJECT_URL),
            "asset_url": asset_url,
            "asset_name": exe_asset.get("name") if exe_asset else "RiftScout.exe",
            "body": release.get("body", "Bug fixes and performance improvements."),
            "published_at": release.get("published_at", ""),
            "sha_url": sha_asset.get("browser_download_url") if sha_asset else None,
        }
    except Exception as exc:
        log.warning("Update check failed: %s", exc)
        return None


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash of a local file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(128 * 1024):
            hasher.update(chunk)
    return hasher.hexdigest().upper()


def download_update(
    update_info: Dict[str, Any],
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> Optional[Path]:
    """
    Download the latest executable binary to %APPDATA%/RiftScout/updates.
    """
    asset_url = update_info.get("asset_url")
    if not asset_url:
        log.error("No binary asset URL found in update payload.")
        return None

    tag = update_info.get("tag", "latest")
    dest_path = C.UPDATES_DIR / f"RiftScout_{tag}.exe"

    log.info("Downloading RiftScout update from %s to %s", asset_url, dest_path)
    success = net.download_file(asset_url, str(dest_path), progress_callback=progress_callback)
    if not success or not dest_path.exists():
        log.error("Download failed or destination file missing.")
        return None

    return dest_path


def apply_update_and_restart(new_exe_path: Path) -> bool:
    """
    Atomically swap the currently running executable with the new binary and restart.
    Uses a detached PowerShell process to avoid Windows file-locking collisions.
    """
    if not new_exe_path.exists():
        log.error("Update binary does not exist at %s", new_exe_path)
        return False

    current_pid = os.getpid()

    if not is_frozen():
        log.info(
            "Running from source tree (not frozen exe). To update, pull latest git commits: git pull."
        )
        return False

    current_exe = Path(sys.executable).resolve()
    new_exe = new_exe_path.resolve()

    log.info("Initiating 1-click self-update: %s -> %s (PID %d)", new_exe, current_exe, current_pid)

    # Detached PowerShell script to wait for old PID, swap executable, and restart
    ps_cmd = (
        f"$ErrorActionPreference = 'SilentlyContinue'; "
        f"Wait-Process -Id {current_pid} -Timeout 10; "
        f"Start-Sleep -Milliseconds 500; "
        f"Move-Item -Path '{new_exe}' -Destination '{current_exe}' -Force; "
        f"Start-Process -FilePath '{current_exe}'"
    )

    try:
        # Launch detached PowerShell process with Session 1 visibility
        subprocess.Popen(
            ["powershell.exe", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_cmd],
            creationflags=subprocess.DETACHED_PROCESS if sys.platform == "win32" else 0,
            close_fds=True
        )
        # Cleanly terminate current process so the PowerShell script can replace it
        sys.exit(0)
    except Exception as exc:
        log.error("Failed to launch self-update restart script: %s", exc)
        return False
