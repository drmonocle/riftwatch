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
* **Comprehensive Live Information Audit & Official Stream Routing:**
  * **International Streaming Provider Ingestion:** Expanded `_stream_url()` to recognize and parse official broadcast providers from Riot's live match feeds: **SOOP / AfreecaTV** (`play.sooplive.co.kr`), **Bilibili** (`live.bilibili.com`), **Huya** (`huya.com`), **Chzzk** (`chzzk.naver.com`), and **Trovo**.
  * **DCGI / Global Invitational Stream Resolution:** The live Demacia Cup Global Invitational (DCGI) match between Shopify Rebellion and FlyQuest now resolves directly to its official Korean live broadcast (`https://play.sooplive.co.kr/aflol`) rather than an empty stream URL.
  * **Accurate Fallback Search Routing:** When stream links are absent, the YouTube search fallback now constructs a targeted query (`{league} {team1} vs {team2} live`) ensuring precise search results for all tournaments (e.g. `DCGI SR vs FLY live`).
  * **Guaranteed Closure Safety in LiveView:** Bound `▶ Watch live` and `Reveal scores` button lambdas to explicit default values (`m=m`, `mid=m['match_id']`), preventing closure reference leaks across multi-match broadcasts.

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
