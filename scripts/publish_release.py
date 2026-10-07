"""
RiftWatch GitHub Release Publisher
Builds (or verifies) the RiftWatch standalone executable and publishes a new
GitHub Release with binary and SHA256SUMS assets attached.
"""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import riftscout

def main():
    version = f"v{riftscout.__version__}"
    print(f"==========================================================")
    print(f"       Publishing RiftWatch Release {version} to GitHub   ")
    print(f"==========================================================")

    exe = ROOT / "dist" / "RiftWatch.exe"
    sums = ROOT / "dist" / "SHA256SUMS.txt"

    if not exe.exists() or not sums.exists():
        print("[*] Assets missing in dist/. Triggering build...")
        subprocess.run(["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", "scripts/build_exe.ps1"],
                       cwd=str(ROOT), check=True)

    sha256 = sums.read_text(encoding="utf-8").strip().split()[0]
    print(f"[*] Verified SHA-256: {sha256}")

    notes = f"""## RiftWatch {version} - Windows Desktop Esports Sentinel

### ✨ What's New & Refined in {version}
* **Robust 1-Click In-App Updater & Auto-Restart:**
  * Fixed process locking and relaunch failures during executable updates. The updater now waits for all running bootloader processes to exit, safely renames in-use binaries to `.old`, atomically swaps the verified executable, and releases the single-instance mutex before relaunching with a visible window.
  * Added detailed logging to `%APPDATA%\\RiftWatch\\update.log`.
* **Double-Buffered Smooth UI (Zero White Screen Flashing):**
  * Implemented an off-screen double-buffering frame swap in `ScrollFrame`. Pages now build new card hierarchies completely in the background before atomically swapping the canvas window, eliminating Win32 `WM_ERASEBKGND` white flashes and widget flicker.
  * Themed native scrollbars with dark Hextech colors (`#091428` trough, `#1e2328` thumb) and enforced global dark widget background defaults.
* **Twitch 24/7 Clean Status & Offline Mode:**
  * When the Twitch broadcast is offline, the top header badge and 24/7 tab hero card strictly display `Offline` without showing any scheduled match titles (e.g. "BLG vs WBG").
  * Fixed `net.fetch_text` to correctly query Twitch channel uptime.
  * Streamlined active stream titles by removing redundant "ON AIR" badges.
* **Expanded Settings Hub:**
  * **Default Launch Tab:** Choose whether RiftWatch opens to Live, Schedule, 24/7 Stream, or Watchlist.
  * **Desktop Toast Notifications:** Configurable toggles for match kickoffs, 15m pre-match countdowns, and 24/7 stream broadcasts.
  * **Watchlist Summary & Reset:** Shows live counts of followed entities and provides a 1-click Reset All Follows action.
  * **Diagnostics & Maintenance:** Quick actions to clear downloaded logo caches, open log files, and inspect data feed health.

### 📦 Checksums & Integrity
* **Executable:** `RiftWatch.exe`
* **SHA-256 Hash:** `{sha256}`
"""

    notes_path = ROOT / "dist" / "release_notes.md"
    notes_path.write_text(notes, encoding="utf-8")

    env = dict(os.environ)
    env["PATH"] = f"C:\\Program Files\\Git\\cmd;C:\\Program Files\\GitHub CLI;{env.get('PATH', '')}"

    gh_bin = r"C:\Program Files\GitHub CLI\gh.exe" if Path(r"C:\Program Files\GitHub CLI\gh.exe").exists() else "gh"
    cmd = [
        gh_bin, "release", "create", version,
        str(exe), str(sums),
        "--title", f"RiftWatch {version}",
        "--notes-file", str(notes_path)
    ]
    print(f"[*] Creating GitHub Release {version}...")
    subprocess.run(cmd, cwd=str(ROOT), check=True, env=env)

    print("==========================================================")
    print("Release published successfully!")
    print(f"URL: https://github.com/drmonocle/rift-scout/releases/tag/{version}")
    print("==========================================================")

if __name__ == "__main__":
    main()
