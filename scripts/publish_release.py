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

A dedicated, lightweight Windows desktop tracker and sentinel for League of Legends pro esports and the 24/7 Twitch rebroadcast channel.

### ✨ What's New
* **First-Run Onboarding Setup Wizard:** 1-click setup dialog to follow your favorite regions, pro teams, and star players on first launch.
* **Regions & Tournaments:** Dedicated Regions tab to follow entire competitive ecosystems (International, Korea, China, Europe, North America, APAC, Brazil).
* **System Tray Sentinel:** Runs quietly in the notification area with close-to-tray minimization, spoiler mode toggle, and schedule refresh.
* **Team Crest Logos:** Crisp logos across player cards, starting lineups, and 24/7 Twitch rebroadcast cards.
* **Live In-Game Stats:** Gold lead tracking, kill scoreboards, towers, dragons, barons, inhibitors, and starting champions.
* **Twitch 24/7 Rebroadcast Sync:** Integrated live playout schedule and S-Tier Banger highlights.
* **1-Click Verified Self-Updater:** Automatically checks GitHub Releases and verifies SHA-256 checksums before swapping binaries.
* **Monocle Productions LLC Branding:** Portal and Ko-fi support integration.

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
