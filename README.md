# ⚡ RiftWatch

A fast, lightweight Windows desktop app for League of Legends esports. Check live scores, view schedules, follow your favorite teams, and watch matches without opening a heavy browser.

[![Download](https://img.shields.io/github/v/release/drmonocle/riftwatch?color=0ac8b9&label=Download)](https://github.com/drmonocle/riftwatch/releases)
[![Platform](https://img.shields.io/badge/platform-Windows-blue)](#)
[![Size](https://img.shields.io/badge/size-4.5%20MB-brightgreen)](#)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## 📥 Download for Windows

Download the latest version from [**GitHub Releases**](https://github.com/drmonocle/riftwatch/releases):

* 🚀 [**Download RiftWatch.exe**](https://github.com/drmonocle/riftwatch/releases/latest/download/RiftWatch.exe) (Portable, ~3.7 MB)
* 📦 [**Download RiftWatch.zip**](https://github.com/drmonocle/riftwatch/releases/latest/download/RiftWatch-v0.3.5-windows-x64.zip) (~1.8 MB)

> **No installer needed.** Just download and run. It runs on Windows 10 and 11 and uses almost no RAM (~35 MB).

---

## What does it do?

### 📌 Floating Ticker Bar & Desktop HUD
* Pop out a mini bar that floats on your screen while you play games or work.
* Click and drag it anywhere on your desktop; double-click anytime to restore the main window.
* Pin it on top of other windows so you never miss a game.
* Shows live scores, upcoming start times, and stream info.
* Click any match on the bar to jump straight to it.

### 🔴 Live Matches & Countdown
* See games that are live right now with real-time scores.
* When no games are playing, shows a live countdown to the next game you care about.
* Click the star icon (`☆`/`★`) beside any team to instantly follow or unfollow them.
* One click to open official Twitch or YouTube streams.

### 🙈 Spoiler Mode & Per-Match Reveal
* Hate spoilers? Turn on Spoiler Mode in one click to hide scores and winners until you want to see them.
* Want to check just one result without unmasking the rest? Simply click any masked "VS" score to reveal that specific match!

### ⌨️ Desktop Keyboard Shortcuts
* `F5` or `Ctrl+R` — Refresh live scores immediately
* `Ctrl+1..6` — Fast-switch between Live, Schedule, 24/7 Stream, Watchlist, News, and Settings
* `Ctrl+S` — Toggle Spoiler Mode instantly
* `Ctrl+D` — Toggle Detached Floating HUD mode

### ⭐ Watchlist & 1-Click Following
* Follow your favorite **Teams** (T1, Gen.G, G2, FlyQuest, etc.) from the Watchlist or directly from match cards.
* Follow your favorite **Players** (Faker, Chovy, Caps, etc.).
* Pick which **Regions** and **Leagues** you care about (LCK, LPL, LEC, LCS, Worlds, MSI, etc.). All major regions are turned on by default.
* Filter schedules so you only see matches for the teams you follow.

### 📅 Full Schedule & Results
* See what's coming up today, this week, or check past results.
* Smart fallback: automatically opens to upcoming matches on tournament off-days so you never see a blank screen.
* Quick search by team name or league.

### 📺 24/7 Tournament Stream
* Built-in guide for the 24/7 League of Legends tournament replay channel running on Twitch and YouTube.
* See what classic tournament or series is playing right now.

### 🔔 System Tray & Native Single Instance
* Native single-instance enforcement: launching a second copy seamlessly brings your existing RiftWatch window to the front.
* Minimizes to the system tray near your Windows clock when you close it so it stays out of your way.
* Native Windows autostart option on sign-in and desktop kickoff notifications.
* Right-click the tray icon to quickly show, hide, or quit.

---

## How to Build from Code

If you want to compile it yourself:

1. Install [Node.js](https://nodejs.org/) and [Rust](https://rustup.rs/).
2. Clone this repo:
   ```powershell
   git clone https://github.com/drmonocle/riftwatch.git
   cd riftwatch
   ```
3. Install and run:
   ```powershell
   npm install
   npm run dev
   ```
4. To build the `.exe`:
   ```powershell
   npm run build
   cargo build --manifest-path src-tauri/Cargo.toml --release
   ```

---

## Support

RiftWatch is 100% free and open source. If you like it and want to support the project:

☕ [**Support on Ko-fi**](https://ko-fi.com/monocle)

---

## Disclaimer

RiftWatch is an unofficial fan project by Monocle Productions LLC. It is not endorsed by or affiliated with Riot Games. League of Legends and Riot Games are trademarks of Riot Games, Inc.
