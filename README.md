# 🎯 RiftScout

> **League of Legends Desktop Esports Watchdog & 24/7 Stream Companion**  
> *Track live pro matches, follow your favorite teams, players, and regions, and stay synced with the 24/7 Twitch marathon broadcast.*

---

## ⚡ What is RiftScout?

Modeled after the architecture of **CBJ Gameday Sentinel**, **RiftScout** is a high-performance Windows desktop application that solves the inaccuracies of the official LoL Esports portal and the rate-limits of community wikis.

### Key Capabilities
- **🔴 Real-Time Pro Match Ingestion:** Polls Riot Games' official persisted API (`esports-api.lolesports.com`) for live match statuses, live scores, and game clocks across all major leagues (LCK, LPL, LEC, LTA, Worlds, MSI).
- **⭐ Granular Watchlist System:** Follow specific **Teams** (T1, Gen.G, G2, FlyQuest), **Regions** (LCK, LPL, LEC, LTA, Worlds), and **Players** (Faker, Chovy, Ruler, Caps). When a followed entity is playing, RiftScout highlights the match and triggers desktop notifications.
- **📺 24/7 Twitch Broadcast Integration:** Directly syncs with your channel's master schedule database (`lol_broadcast_schedule.db` / `lolworlds.com`), tracking current marathon progress, series scores, and highlighting all **S-Tier Bangers** airing on stream.
- **🔄 1-Click Automated Self-Updater:** Automatically checks GitHub Releases for new updates in the background. Clicking "Update" downloads the verified release binary, swaps the executable, and seamlessly restarts with zero friction.
- **🛡️ Global Spoiler Mode:** One-click toggle hides all match scores, results, and winner indicators across notifications and the UI so you never get spoiled when watching on delay.

---

## 🚀 Quick Start (Phase 1 CLI Diagnostics)

Run the diagnostics suite to verify live pro feeds, watchlist filters, and Twitch broadcast synchronization:

```powershell
# Run RiftScout diagnostics CLI
py -3.12 -m riftscout

# Run full automated test suite (16 tests)
py -3.12 -m pytest tests -v
```

---

## 🔄 1-Click Update Architecture

Updating RiftScout is designed to be completely effortless for users:

1. **In-App 1-Click Update:**  
   RiftScout polls GitHub Releases in the background. When a new version is detected, an update button appears in the app. Clicking it streams the verified release executable to `%APPDATA%\RiftScout\updates`, launches a detached PowerShell process to swap the binary, and immediately restarts the app.
2. **PowerShell One-Liner:**  
   Power users can also update from the command line anytime by running:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\update.ps1
   ```

---

## 📁 Project Architecture

```
rift-scout/
├── riftscout/                     # Core application package
│   ├── __init__.py                # Package version & metadata (v0.1.0)
│   ├── __main__.py                # Diagnostics CLI entry point
│   ├── config.py                  # Endpoints, Hextech palette, timeouts
│   ├── net.py                     # Resilient HTTP client with security allowlist
│   ├── db.py                      # Local SQLite cache (%APPDATA%/RiftScout/cache.db)
│   ├── settings.py                # JSON persistence for watchlist and preferences
│   ├── data.py                    # Hybrid Riot API + Cargo data coordinator
│   ├── stream.py                  # Twitch marathon schedule reader & banger filter
│   └── updater.py                 # 1-click automated self-updater & binary swap
├── tests/                         # Pytest test suite (16 unit & live integration tests)
├── scripts/                       # Automation and packaging scripts
│   └── update.ps1                 # Standalone PowerShell update script
├── requirements.txt               # Dependencies (requests, pillow, pystray, pytest)
└── README.md
```

---

## 📄 License

Copyright (c) 2026 Monocle Productions LLC. Distributed under the MIT License.
