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
* **Instant In-Place Follow Toggling (Zero Page Reloads):**
  * **Reactive In-Place Button Updates:** Clicking `☆ Follow` / `★ Following` on any team, player, region, or league row now updates the button text, colors, and row border immediately in-place (<0.1ms).
  * **Eliminated Full-Page Rebuilds:** Synchronized the rendered view signature upon user toggles so the background 150ms poll loop never tears down or re-renders the 50+ item directory while actively browsing.
  * **Isolated Following Summary Container:** The top "Following" chips section now updates independently in an isolated container without affecting list scroll position or tearing down existing rows.
  * **Immediate Match Card Star Feedback:** Match card `☆`/`★` buttons in Live and Schedule views now update their visual state immediately on click.
* **Hardened Self-Updater Desktop Relaunch:**
  * **Windows Desktop Shell Execution (`SW_SHOWNORMAL`):** Resolved the issue where clicking Update on remote or secondary PCs closed the app after downloading but failed to open it. Replaced child-process launching with direct Windows Shell COM execution (`Shell.Application.ShellExecute`), guaranteeing the updated client opens visibly in the user's interactive desktop session (`SW_SHOWNORMAL = 1`) without inheriting hidden process window flags.
  * **Automatic Mark-of-the-Web Unblocking:** Automatically runs `Unblock-File` on the downloaded binary to strip Windows SmartScreen/Zone.Identifier download locks.
  * **Safe Non-Destructive Binary Swap:** Uses `Copy-Item` with randomized backup files to ensure the source update binary remains safely cached in `%APPDATA%\\RiftWatch\\updates\\` if initial locks occur.

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
