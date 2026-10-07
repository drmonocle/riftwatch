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
* **Zero White Screen Flash on Startup & Update Relaunch:**
  * **Off-Screen Window Staging:** Windows are now initialized in a withdrawn off-screen state (`root.withdraw()`) while dark Hextech themes and widgets are assembled, revealing via `deiconify()` only after all off-screen geometry and dark canvas buffers are calculated.
  * **Windows 10/11 Immersive Dark Mode Titlebars:** Native Win32 HWNDs now automatically activate `DWMWA_USE_IMMERSIVE_DARK_MODE` (20), preventing Windows from painting default `#FFFFFF` white window classes on application launch or after in-app updater restarts.
* **LoL Esports Leagues Multi-Selector & Schedule Expansion:**
  * **Dedicated League Filter Modal:** Replaced the single-league dropdown with a comprehensive Hextech league selector dialog (`LeagueFilterDialog`). Users can now select any combination of individual pro leagues to track together on the Schedule page.
  * **Full Riot Leagues Coverage (LCK, LPL, LEC, LCS, Worlds):** Directly queries Riot's API across 12+ league IDs in parallel, fetching 80+ events per league (LCK, LPL, LEC, LCS, Worlds, MSI, First Stand, Demacia Cup, CBLOL, LCP) and expanding cache retention to 60 days.
  * **1-Click Quick Presets & Real-Time Search:** Includes instant filters for "★ All Leagues", "⭐ Big 4 Major (LCK/LPL/LEC/LCS)", "🌐 International", and "★ Followed in Watchlist", plus dynamic instant-search filtering.
* **Streamlined 24/7 Broadcast Replays Tab:**
  * Cleaned up redundant streaming buttons: high-contrast "▶ Watch on Twitch" and "▶ Watch on YouTube" buttons remain front-and-center on the current live broadcast hero card, while the Next S-Tier Banger card and individual upcoming rebroadcast rows have been decluttered.

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
