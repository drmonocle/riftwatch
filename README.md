# ⚡ RiftWatch

[![Release](https://img.shields.io/github/v/release/drmonocle/riftwatch?color=0ac8b9&label=RiftWatch)](https://github.com/drmonocle/riftwatch/releases)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%20%7C%2011%20(x64)-blue)](#)
[![Stack](https://img.shields.io/badge/stack-Tauri%20v2%20%7C%20Rust%20%7C%20React%2019-c8aa6e)](#)
[![Size](https://img.shields.io/badge/binary%20size-4.4%20MB-brightgreen)](#)
[![Memory](https://img.shields.io/badge/idle%20RAM-~36%20MB-purple)](#)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Support](https://img.shields.io/badge/ko--fi-support-ff5e5b)](https://ko-fi.com/monocle)

**RiftWatch** is an ultra-lightweight, hardware-accelerated Windows desktop sentinel and 24/7 continuous stream companion for League of Legends esports. Track live pro match scores, inspect global tournament schedules, follow your favorite teams, and monitor the continuous 24/7 tournament rebroadcast channel on [Twitch](https://www.twitch.tv/LoLWorldChampionship) and [YouTube](https://www.youtube.com/@LoLWorldChampionships) with zero bloat.

RiftWatch is an unofficial fan project by **Monocle Productions LLC**. It is not endorsed by Riot Games.

---

## 📥 Quick Download (Windows 64-bit)

Get the latest standalone release from [**GitHub Releases**](https://github.com/drmonocle/riftwatch/releases):

* 🚀 [**Download RiftWatch.exe (v0.3.0 Standalone)**](https://github.com/drmonocle/riftwatch/releases/latest/download/RiftWatch.exe) `~4.4 MB`
* 📦 [**Download RiftWatch-v0.3.0-windows-x64.zip**](https://github.com/drmonocle/riftwatch/releases/latest/download/RiftWatch-v0.3.0-windows-x64.zip) `~1.8 MB`

> **Note:** Completely portable — no installation or administrator rights required. Requires Windows 10/11 with the standard Microsoft Edge WebView2 runtime (pre-installed by default on all modern Windows machines).

---

## ⚡ Architecture Comparison (Rebuild Highlights)

In version `v0.3.0`, RiftWatch was completely re-architected from legacy Python/Tkinter into **Tauri v2 + Rust + React 19 + Tailwind CSS v4**.

| Metric | Legacy Python (`v0.2.13`) | Typical Electron Client | **RiftWatch v0.3.0 (Tauri v2 + Rust)** |
| :--- | :---: | :---: | :---: |
| **Executable Size** | 45.2 MB | ~160 – 240 MB | **4.44 MB** *(90% smaller)* |
| **Idle Memory (RAM)** | ~55 – 65 MB | ~140 – 200 MB | **~36 MB** *(hardware-accelerated)* |
| **Launch Speed** | ~2.0s | ~2.5s – 4.0s | **< 0.35s (instantaneous)** |
| **Rendering Engine** | Tkinter CPU Software Canvas | Bundled Chromium | **Evergreen WebView2 (DirectX 12 GPU)** |
| **Detached HUD** | Hand-rolled Tk Toplevel | Heavy Web Browser Window | **Native Transparent Multi-Window** |
| **Settings Navigation**| Full widget tree re-draw | Varies | **100% In-Place Reactive (Zero Scroll Resets)** |

---

## ✨ Features

### 📌 1. Detached Desktop HUD Ribbon (`720x36px`)
* **Borderless Floating Ribbon**: Floats cleanly over fullscreen games, streams, or browser windows.
* **Native OS Dragging**: Uses `data-tauri-drag-region` for silky-smooth 144Hz / 240Hz Windows hardware dragging without CPU hitching.
* **Always-on-Top Toggle (📌)**: Pin over your active games or let it rest quietly on secondary monitors.
* **Instant Switching**: 1-click **Detach** from main window, or **Dock** back to the menu header.
* **Click-Through Routing**: Clicking any active match or stream card in the HUD instantly jumps straight to that event.

### 🔴 2. Live Pro Match Hub
* **Real-time Live Scores**: Live games across all Tier-1 and regional circuits (LCK, LPL, LEC, LCS, Worlds, MSI, First Stand).
* **Spoiler Mode**: Instantly hides scores and match outcomes until you choose to reveal them.
* **Direct Broadcast Links**: Jump directly to official Twitch and YouTube live broadcasts with one click.

### 📅 3. Complete Global Schedule
* **Smart Filter Tabs**: Switch between **Today**, **Upcoming**, and **Results** with zero lag.
* **Real-Time Fuzzy Search**: Filter hundreds of upcoming and completed matches instantly by team name or tournament.
* **Followed-Only Mode**: Focus exclusively on the teams and leagues in your custom Watchlist.

### 📺 4. 24/7 Continuous Stream Marathon
* **Live Broadcast Telemetry**: Real-time broadcast cards showing the currently airing tournament, season, and stage on the 24/7 channel.
* **S-Tier Banger Detection**: Automatically tags legendary historical games and Grand Finals sets.
* **Direct Playout Links**: One-click routing to the 24/7 Twitch and YouTube broadcasts.

### ⭐ 5. Watchlist & Follow Directory
* **Instant In-Place Following**: Click `☆ Follow` / `★ Following` on any pro team or regional league for immediate in-place visual updates.
* **Zero Page Teardowns**: Browsing and toggling never triggers full-page rebuilds or scroll jumping.

### 📰 6. LoL Esports Dispatch
* **Zero-Bloat Curated News**: Clean, distilled intelligence cards covering tournament formats, meta breakdowns, and power rankings without ads or clickbait.

### ⚙️ 7. In-Place Reactive Settings
* **Instant Setting Mutation**: Toggle spoiler mode, notifications, default launch tab, and HUD ribbon modes with zero page reloads.

---

## 🛠️ Building from Source

### Prerequisites
* [Node.js](https://nodejs.org/) (v20+ recommended)
* [Rust & Cargo](https://rustup.rs/) (v1.80+)
* Standard Windows C/C++ build tools (or LLVM-MinGW / MSVC)

### Development Mode
```powershell
# 1. Clone repository
git clone https://github.com/drmonocle/riftwatch.git
cd riftwatch

# 2. Install dependencies
npm install

# 3. Launch live hot-reloading development environment
npm run dev
# Or with Tauri native shell:
npx tauri dev
```

### Production Release Build
```powershell
# Compile frontend and link optimized release binary
npm run build
cargo build --manifest-path src-tauri/Cargo.toml --release
```
The optimized standalone binary outputs to:
`src-tauri/target/release/RiftWatch.exe` (~4.4 MB).

---

## 🗄️ Legacy Python Implementation

The original Python/Tkinter client (`v0.2.13`) has been preserved for historical and reference purposes in [`legacy/python-client/`](legacy/python-client/).

To run the legacy client:
```powershell
cd legacy/python-client
py -3.12 -m pip install -r requirements.txt
py -3.12 -m riftscout
```

---

## ☕ Support & Community

If you enjoy RiftWatch and the 24/7 tournament rebroadcast stream, you can support development and server hosting on Ko-fi:

👉 [**https://ko-fi.com/monocle**](https://ko-fi.com/monocle)

---

## 📜 License & Disclaimers

* **License**: Released under the [MIT License](LICENSE).
* **Disclaimer**: RiftWatch isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. League of Legends and Riot Games are trademarks or registered trademarks of Riot Games, Inc.
