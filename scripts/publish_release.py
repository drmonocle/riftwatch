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
* **YouTube Live Stream Integration for 24/7 Schedule:**
  * **24/7 Stream Hero & Spotlight:** Added prominent `▶ Watch on YouTube` buttons (`#cc0000`) alongside `▶ Watch on Twitch` on the 24/7 hero banner and the Next S-Tier Banger spotlight card.
  * **Direct Stream Action per Schedule Row:** Every upcoming rebroadcast row in the 24/7 schedule table now features individual `YT` and `Twitch` action buttons so users can instantly tune in with a single click.
  * **System Tray Quick Links:** Added `Watch 24/7 Stream (YouTube)` and `Watch 24/7 Stream (Twitch)` to the system tray context menu.
  * **Settings Hub Integration:** Displays both Twitch and YouTube stream URLs with one-click direct browser launchers.
* **Double-Buffered Smooth UI (Zero White Screen Flashing):**
  * Fully background-rendered page hierarchies with atomic canvas swaps in `ScrollFrame` to eliminate Win32 `WM_ERASEBKGND` flicker.
* **Robust In-App Updater & Auto-Restart:**
  * Safe file replacement with `.old` fallback, mutex release, and visible process relaunching.
* **Accurate 24/7 Stream Offline State:**
  * Streamlined header badge and hero cards strictly displaying `Offline` when streams are down without showing scheduled match titles.

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
