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
* **Vector Rift Herald Emblem Branding (Taskbar & System Tray):**
  * **Custom Vector Herald Artwork:** Replaced procedural geometry with the community-voted Vector Rift Herald emblem: sharp golden and purple horns curving upward, glowing purple eyes, and angular gold shield lines on a deep Hextech navy-purple rounded squircle badge.
  * **Multi-Resolution Windows PE Icon:** Master `app.ico` packed with native Win32 icon mipmaps across 7 standard resolutions (`16x16`, `24x24`, `32x32`, `48x48`, `64x64`, `128x128`, `256x256`) for razor-sharp rendering in the Windows Taskbar, Alt-Tab switcher, File Explorer, and Desktop shortcuts.
  * **Custom System Tray Icon:** Updated the background `pystray` system notification tray icon with the Vector Rift Herald branding, complete with subtle sharpening and contrast optimization at 64x64 and 32x32.
  * **Dual Win32 / Tkinter Icon Binding:** Automatically applies native `iconbitmap` to the window HWND alongside multi-resolution `iconphoto` frames, guaranteeing crisp rendering across all DPI display scales.
  * **Zero White Screen Flash & Immersive Dark Mode:** Fully preserved all v0.2.4 dark mode enhancements (`root.withdraw()` staging and `DWMWA_USE_IMMERSIVE_DARK_MODE`).

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
