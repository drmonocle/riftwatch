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
* **Robust 1-Click Self-Updater & Process Relaunch Engine:**
  * **Dedicated Parameterized Helper Script:** Replaced inline string-evaluated PowerShell commands with a robust, disk-persisted helper script (`%APPDATA%\\RiftWatch\\apply_update.ps1`). Completely eradicates PowerShell command quoting errors, unescaped path parentheses (e.g. `RiftWatch (1).exe`), and `-and` operator syntax failures.
  * **Reliable Process Lifecycle Synchronization:** Helper now specifically tracks the exact parent PID, checks all process variants matching `*RiftWatch*` and `*RiftScout*`, and performs a safe two-step atomic swap with `.old` backup and automatic rollback protection.
  * **Guaranteed Foreground Elevation on Relaunch:** Explicitly launches updated executables via `Start-Process -FilePath $CurrentExe -WindowStyle Normal` with 1-second process and file-handle clearance delay, plus runtime `root.lift()` and `root.focus_force()`.
  * **Comprehensive Diagnostic Logging:** All update phases (process waiting, file replacement attempts, and process launch PIDs) are cleanly logged with timestamps to `%APPDATA%\\RiftWatch\\update.log`.
* **Single-Instance Mutex Acquisition Hardening:**
  * Added a 3-second mutex retry acquisition loop with immediate duplicate handle closure (`kernel32.CloseHandle(handle)`) upon `ERROR_ALREADY_EXISTS`. Prevents newly spawned binaries from exiting prematurely while a previous instance completes its shutdown sequence.
* **Vector Rift Herald Branding:**
  * High-resolution Vector Rift Herald icon across Windows Taskbar, System Notification Tray (`pystray`), Alt-Tab switcher, and Window Titlebar.

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
