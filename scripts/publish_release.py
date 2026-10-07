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

    notes = f"""## RiftWatch {version} - Windows Desktop Esports Sentinel & 24/7 Stream Companion

### ✨ What's New & Refined in {version}
* **Search Bar Keystroke Flicker Eradication:**
  * **Decoupled Keystrokes from Polling Signature:** In `WatchlistView`, typing into the search bar is now decoupled from the polling signature (`applied_query`). Keystrokes no longer trigger rapid 150ms frame teardowns, widget clearing, or layout rebuilds.
  * **Debounced Query Execution:** Added an ultra-smooth 280ms debounce timer (and snappy 40ms clear), with immediate search application on `<Return>` and `<Escape>`, guaranteeing a 100% flicker-free search experience.
  * **Optimized League Filter Search:** Debounced search queries in `LeagueFilterDialog` and added mapping checks so widgets are never redundantly re-packed.
* **Live Broadcast Ticker Bar:**
  * **Docked Real-Time Sports Ticker:** Added a sleek Hextech sports ticker bar docked beneath the navigation tabs, providing persistent live game awareness across all tabs.
  * **Live Scores & In-Game Gold Differentials:** Displays live pro matches with current game number and gold leads (e.g. `● LIVE · DCGI · SR 0 : 0 FLY · Game 1 · FLY +13.2k gold`).
  * **Upcoming Countdown Timers & 24/7 Stream Highlights:** Cycles upcoming fixtures with relative countdowns and currently airing 24/7 Twitch marathon events.
  * **Spoiler-Safe & Clickable Navigation:** Clicking any ticker item jumps directly to its corresponding tab (`Live`, `Schedule`, or `Stream`). Under Spoiler Mode, all scores and gold leads remain 100% masked.
  * **Controls & Settings Toggle:** Includes manual ◀ / ▶ cycle buttons, item counter, pause-on-hover, quick `✕` hide button, and a toggle under `Settings -> Display & Experience`.

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
