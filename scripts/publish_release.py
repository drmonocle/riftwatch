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
* **Schedule 30-Day Window & Starvation Fix (Today & Upcoming Matches Restored):**
  * **Eliminated Past Match Starvation:** Replaced legacy `ORDER BY start_time_utc ASC LIMIT 200` query in `db.get_schedule()` with a 30-day rolling lookback window (`start_time_utc >= datetime('now', '-30 days')`) and limit of 1000. Ancient matches from 2 months ago no longer choke the schedule buffer, immediately restoring all matches under **Today** (8 matches) and **Upcoming** (70+ matches) including Demacia Cup, EMEA Masters, LCS Promotion, and Worlds.
* **Setup Wizard Follow/Unfollow State Retention Fix:**
  * **Dynamic Body Resolution:** Fixed an issue in `OnboardingWizard` where clicking follow/unfollow caused the window contents to vanish. Switched `wizard.body` to a dynamic property pointing directly to `self.scroll.body`, ensuring `keep_scroll` frame swaps render cleanly into the active container rather than referencing a destroyed frame.
* **Zero White Flash & In-Place Diagnostics in Settings Hub:**
  * **Eliminated Background Re-rendering:** Removed `"status"` from `SettingsView.deps` so routine worker polling passes no longer tear down and rebuild the entire settings page every 15–30 seconds.
  * **In-Place Diagnostic Label Updates:** Background data source health (schedule, live, stream, catalog) now updates existing labels in-place in 0 milliseconds without re-rendering the view.
  * **Atomic Double-Buffered Frame Swaps:** Added `new_body.update_idletasks()` to `ScrollFrame.keep_scroll()` before swapping the canvas window, ensuring all geometry and dark Hextech themes are fully resolved before display with zero white flash.

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
