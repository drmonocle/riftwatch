# RiftScout

A Windows desktop tracker for League of Legends esports. Follow the teams, players and
leagues you care about, see what is live right now, and see what is airing on the
24/7 rebroadcast channel [twitch.tv/LoLWorldChampionship](https://www.twitch.tv/LoLWorldChampionship).

RiftScout is an unofficial fan project by Monocle Productions LLC. It is not endorsed by Riot Games.

## Status

| Phase | What | State |
|---|---|---|
| 1 | Data engine (Riot schedule/live/livestats, SQLite cache, lolworlds.com stream schedule) | done |
| 2 | Watchlist engine (team / player / league follows, team directory, roster matching) | done |
| 3 | Desktop UI (Live, Schedule, 24/7 Stream, Watchlist, Settings tabs) | done |
| 4 | Tray icon, desktop notifications, floating ticker | not started |
| 5 | Packaged `RiftScout.exe` + GitHub release with checksums | not started |
| 6 | Web version at lolworlds.com/scout | not started |

## Features (v0.2.0)

- **Live tab**: every pro match in progress, with series score, and when Riot's live-stats feed
  covers the game: kills, gold, towers, dragons, barons, inhibitors, gold lead, and the
  starting lineups with champions. When nothing is live it counts down to your next match.
- **Schedule tab**: upcoming, today, and results (last 7 days), filterable by league and
  "followed only". Times are shown in your local time zone.
- **24/7 Stream tab**: what is on the Twitch channel now, what's next, the next S-tier "banger",
  and the upcoming rebroadcast list. Read from the public schedule at lolworlds.com.
- **Watchlist tab**: browse or search all ~450 active pro teams and ~2,900 registered players,
  and follow teams, players and leagues. You can also star a team on any match card.
- **Why a match is highlighted**: each card shows chips such as `★ T1` (followed team),
  `★ Faker starting (Mid)` (followed player confirmed in the live lineup) or
  `★ Faker (T1 Mid)` (on the registered roster; Riot rosters include academy and sub players,
  so this is only confirmed once the game is live), plus the league name for followed leagues.
- **Spoiler mode**: hides series scores, winners, game numbers and in-game stats everywhere,
  including the header and `--diag` output. Each match has its own "Reveal" button.
- **Works offline**: everything is cached in `%APPDATA%\RiftScout\cache.db`; if an API is down
  you see the last good data and a warning in the footer.
- **Start with Windows** option (per-user registry Run key, no admin needed).

## Running from source

Requires Python 3.12 on Windows.

```powershell
py -3.12 -m pip install -r requirements.txt
py -3.12 -m riftscout              # open the app
py -3.12 -m riftscout --diag       # text diagnostics: checks every data source
pyw -3.12 run_riftscout.pyw        # open the app without a console window
```

Only one copy of the app runs at a time. Logs go to `%APPDATA%\RiftScout\riftscout.log`.

## Updating

- **From source**: `git pull` in the project folder. The app notices newer GitHub releases
  and tells you, but it won't replace your source files.
- **Packaged exe (from Phase 5)**: the app checks GitHub Releases every 6 hours (or on
  "Check now"). "Update & restart" downloads the new exe, **verifies its SHA-256 against the
  release's `SHA256SUMS` file** and refuses to install if the checksum is missing or wrong,
  then swaps the exe and restarts. `scripts\update.ps1` does the same from PowerShell.

No release has been published yet, so today the update check always reports "up to date".

## Configuration

| Environment variable | Purpose |
|---|---|
| `RIFTSCOUT_RIOT_KEY` | Override the LoL Esports API key |
| `RIFTSCOUT_STREAM_URL` | Override the 24/7 schedule URL (default `https://lolworlds.com/api.ashx?type=schedule-json`) |

Settings (follows, filters, spoiler mode) are stored in `%APPDATA%\RiftScout\settings.json`.
Deleting `cache.db` is always safe; it is rebuilt automatically.

## Data sources

- Riot's LoL Esports API (`esports-api.lolesports.com`, `feed.lolesports.com`). This is the
  same public, but undocumented, API the lolesports.com website uses. Its key is not an
  official developer key and Riot could change or revoke it at any time.
- The 24/7 channel schedule published at lolworlds.com.

## Tests

```powershell
py -3.12 -m pytest tests            # 51 tests: unit, UI render + spoiler gate, live API checks
py -3.12 -m pytest tests -m "not live"   # skip the tests that call the real APIs
```

The UI test renders every tab with fixture data and fails if any score, kill count, gold
value or game number is visible while spoiler mode is on.

## Project layout

```
riftscout/
  config.py      endpoints, allowlists, poll intervals, colours
  net.py         HTTP with host allowlist, retries, size cap; safe browser opening
  db.py          SQLite cache (matches, team directory, stream schedule)
  data.py        Riot schedule/live/livestats parsing
  catalog.py     team / roster / league directory and search
  watchlist.py   "why does this match matter to me" rules
  stream.py      24/7 schedule: now airing, upcoming, next banger
  settings.py    settings.json with migration from v0.1
  worker.py      background thread: all network and disk I/O
  updater.py     GitHub release check + checksum-verified self-update
  diag.py        --diag text report
  ui/            Tkinter app: app.py, views.py, cards.py, widgets.py, images.py
tests/
scripts/update.ps1
run_riftscout.pyw
```

## License

MIT. Copyright (c) 2026 Monocle Productions LLC.
League of Legends and Riot Games are trademarks or registered trademarks of Riot Games, Inc.
