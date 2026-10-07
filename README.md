# RiftWatch

A Windows desktop tracker and sentinel for League of Legends esports. Follow the regions, teams, players and
tournaments you care about, see what is live right now with in-game gold/kill stats, and track upcoming matches airing on the
24/7 rebroadcast channel [twitch.tv/LoLWorldChampionship](https://www.twitch.tv/LoLWorldChampionship).

RiftWatch is an unofficial fan project by Monocle Productions LLC. It is not endorsed by Riot Games.

## Status

| Phase | What | State |
|---|---|---|
| 1 | Data engine (Riot schedule/live/livestats, SQLite cache, lolworlds.com stream schedule) | done |
| 2 | Watchlist engine (team / player / region / league follows, team directory, roster matching) | done |
| 3 | Desktop UI (Live, Schedule, 24/7 Stream, Watchlist [Teams/Players/Regions/Leagues], Settings tabs) | done |
| 4 | First-run Onboarding Setup Wizard, System Tray icon, close-to-tray & hide-to-tray, Ko-fi support | done |
| 5 | Packaged `RiftWatch.exe` + GitHub release with checksums | not started |
| 6 | Web version at lolworlds.com | not started |

## Features (v0.2.0)

- **Onboarding Setup Wizard**: On first install, launches a streamlined wizard allowing 1-click selection of major regions (International, Korea, China, Europe, North America, APAC, Brazil), popular pro teams, and star players. Can be re-launched anytime from the Settings tab.
- **Regions & Tournaments**: Follow entire competitive ecosystems (LCK, LPL, LEC, LCS, Worlds, MSI, First Stand) from the dedicated Regions sub-tab in Watchlist.
- **System Tray & Close-to-Tray**: Live notification area icon with quick actions (Open RiftWatch, Spoiler Mode toggle, Refresh, Support on Ko-fi, Exit). Includes a dedicated "Hide to Tray" button in the bottom right corner, and window close (X) minimizes to the system tray by default (configurable in Settings).
- **Team Logos Everywhere**: Displays crisp team logos next to player cards, live lineup headers, 24/7 stream cards, and match rows.
- **Ko-fi Support**: Integrated "♥ Support" button in the header and Settings tab linking directly to the creator's Ko-fi page (`https://ko-fi.com/monocle`).
- **Live tab**: Every pro match in progress, with series score, and when Riot's live-stats feed covers the game: kills, gold, towers, dragons, barons, inhibitors, gold lead, and the starting lineups with champions and team logos. When nothing is live it counts down to your next match.
- **Schedule tab**: Upcoming, today, and results (last 7 days), filterable by league and "followed only". Times are shown in your local time zone.
- **24/7 Stream tab**: What is on the Twitch channel now, what's next, the next S-tier "banger", and the upcoming rebroadcast list. Read from the public schedule at lolworlds.com.
- **Watchlist tab**: Browse or search all ~450 active pro teams and ~2,900 registered players, and follow regions, teams, players, and leagues.
- **Why a match is highlighted**: Each card shows chips such as `🌐 Korea` (followed region), `★ T1` (followed team), `★ Faker starting (Mid)` (followed player confirmed in the live lineup) or `★ Faker (T1 Mid)` (on the registered roster), plus league chips.
- **Spoiler mode**: Hides series scores, winners, game numbers and in-game stats everywhere, including the header and `--diag` output. Each match has its own "Reveal" button.
- **Works offline**: Everything is cached in `%APPDATA%\RiftWatch\cache.db`; if an API is down you see the last good data and a warning in the footer.
- **Start with Windows** option (per-user registry Run key, no admin needed).

## Running from source

Requires Python 3.12 on Windows.

```powershell
py -3.12 -m pip install -r requirements.txt
py -3.12 -m riftscout              # open RiftWatch
py -3.12 -m riftscout --diag       # text diagnostics: checks every data source
pyw -3.12 run_riftscout.pyw        # open RiftWatch without a console window
```

Only one copy of the app runs at a time (protected by a single-instance mutex). Logs go to `%APPDATA%\RiftWatch\riftwatch.log`.

## Updating

- **From source**: `git pull` in the project folder. The app notices newer GitHub releases and notifies you.
- **Packaged exe (from Phase 5)**: The app checks GitHub Releases every 6 hours (or on "Check now"). "Update & restart" downloads the new exe, **verifies its SHA-256 against the release's `SHA256SUMS` file** and refuses to install if the checksum is missing or wrong, then swaps the exe and restarts.

## Configuration

| Environment variable | Purpose |
|---|---|
| `RIFTSCOUT_RIOT_KEY` | Override the LoL Esports API key |
| `RIFTSCOUT_STREAM_URL` | Override the 24/7 schedule URL (default `https://lolworlds.com/api.ashx?type=schedule-json`) |

Settings (follows, regions, filters, spoiler mode, tray preferences) are stored in `%APPDATA%\RiftWatch\settings.json`. Deleting `cache.db` is always safe; it is rebuilt automatically.

## Support & Ko-fi

If you enjoy RiftWatch and the 24/7 Twitch broadcast, you can support development and hosting on Ko-fi:
[https://ko-fi.com/monocle](https://ko-fi.com/monocle)

## Data sources

- Riot's LoL Esports API (`esports-api.lolesports.com`, `feed.lolesports.com`).
- The 24/7 channel schedule published at lolworlds.com.

## Tests

```powershell
py -3.12 -m pytest tests            # 54 tests: unit, UI render + spoiler gate, tray, wizard, live API checks
py -3.12 -m pytest tests -m "not live"   # skip tests that call live APIs
```

## Project layout

```
riftscout/
  __init__.py    version & metadata (__app_name__ = "RiftWatch")
  config.py      endpoints, regions, popular teams/players, allowlists, poll intervals, colors
  net.py         HTTP with host allowlist, retries, size cap; safe browser opening
  db.py          SQLite cache (matches, team directory, stream schedule)
  data.py        Riot schedule/live/livestats parsing
  catalog.py     team / roster / league directory, search, and logo resolver
  watchlist.py   "why does this match matter to me" rules (teams, players, regions, leagues)
  stream.py      24/7 schedule: now airing, upcoming, next banger
  settings.py    settings.json with migration from v1/v2, region & tray persistence
  worker.py      background thread: all network and disk I/O
  updater.py     GitHub release check + checksum-verified self-update
  diag.py        --diag text report
  ui/            Tkinter & pystray app:
    app.py       main window, single-instance mutex, tray coordination, close/hide logic
    views.py     tab views (Live, Schedule, Stream, Watchlist, Settings)
    cards.py     card renderers (match cards, chips, logos)
    widgets.py   Hextech widgets (buttons, pills, scrollframe)
    wizard.py    first-launch onboarding modal dialog
    tray.py      system tray manager (pystray background thread)
    images.py    offline / async image caching
tests/
run_riftscout.pyw
run_riftwatch.pyw
```

## License

MIT. Copyright (c) 2026 Monocle Productions LLC.
League of Legends and Riot Games are trademarks or registered trademarks of Riot Games, Inc.
