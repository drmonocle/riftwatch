"""
RiftScout Configuration & Global Constants
Defines endpoints, visual Hextech tokens, file paths, and runtime settings.

No machine-specific paths live here: this file ships in the public repo.
Optional overrides come from environment variables (see README).
"""

import os
from pathlib import Path
from . import __version__, __app_name__

# ==============================================================================
# 1. APPLICATION & SYSTEM PATHS
# ==============================================================================
APP_ID = "com.monocle.riftscout"
APP_NAME = __app_name__
APP_VERSION = __version__

# User Data Directory: %APPDATA%\RiftScout
APPDATA_DIR = Path(os.environ.get("APPDATA", Path.home() / ".config")) / "RiftScout"
CACHE_DB_PATH = APPDATA_DIR / "cache.db"
SETTINGS_PATH = APPDATA_DIR / "settings.json"
LOG_PATH = APPDATA_DIR / "riftscout.log"
UPDATES_DIR = APPDATA_DIR / "updates"
LOGO_CACHE_DIR = APPDATA_DIR / "logos"

for _d in (APPDATA_DIR, UPDATES_DIR, LOGO_CACHE_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# ==============================================================================
# 2. DATA SOURCES & UPSTREAM APIS
# ==============================================================================
# Riot's LoL Esports API. This is the public key embedded in the lolesports.com
# web client. It is undocumented and Riot may rotate or revoke it at any time;
# the app must degrade gracefully to cached data when that happens.
RIOT_API_KEY = os.environ.get("RIFTSCOUT_RIOT_KEY", "0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z")
RIOT_API_BASE = "https://esports-api.lolesports.com/persisted/gw"
RIOT_SCHEDULE_URL = f"{RIOT_API_BASE}/getSchedule?hl=en-US"
RIOT_LIVE_URL = f"{RIOT_API_BASE}/getLive?hl=en-US"
RIOT_TEAMS_URL = f"{RIOT_API_BASE}/getTeams?hl=en-US"
RIOT_LEAGUES_URL = f"{RIOT_API_BASE}/getLeagues?hl=en-US"
RIOT_LIVESTATS_WINDOW_URL = "https://feed.lolesports.com/livestats/v1/window/{game_id}"

# 24/7 Twitch rebroadcast schedule (wall-clock air times for every series).
STREAM_SCHEDULE_URL = os.environ.get(
    "RIFTSCOUT_STREAM_URL", "https://lolworlds.com/api.ashx?type=schedule-json"
)
TWITCH_CHANNEL = "LoLWorldChampionship"
TWITCH_CHANNEL_URL = f"https://www.twitch.tv/{TWITCH_CHANNEL}"
STREAM_SITE_URL = "https://lolworlds.com"

# GitHub Releases & Automated Update Configuration
GITHUB_REPO = "drmonocle/rift-scout"
GITHUB_LATEST_RELEASE_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
GITHUB_PROJECT_URL = f"https://github.com/{GITHUB_REPO}"

# Honest User-Agent header
USER_AGENT = f"RiftScout/{APP_VERSION} (Esports Desktop Companion; +{GITHUB_PROJECT_URL})"

# Hosts the app may fetch data from.
ALLOWED_HOSTS = {
    "esports-api.lolesports.com",
    "feed.lolesports.com",
    "static.lolesports.com",
    "lolstatic-a.akamaihd.net",  # older team logos still live on Riot's legacy CDN
    "lolworlds.com",
    "api.github.com",
    "github.com",
    "objects.githubusercontent.com",
    "release-assets.githubusercontent.com",
}

# Hosts the app may open in the user's browser.
BROWSER_HOSTS = {
    "twitch.tv", "www.twitch.tv",
    "youtube.com", "www.youtube.com", "youtu.be",
    "lolesports.com", "www.lolesports.com",
    "lolworlds.com", "www.lolworlds.com",
    "github.com",
}

# ==============================================================================
# 3. POLLING & TIMING INTERVALS (SECONDS)
# ==============================================================================
INTERVAL_IDLE_POLL_SEC = 300       # schedule refresh when nothing is live
INTERVAL_LIVE_POLL_SEC = 45        # schedule/live refresh while a match is live
INTERVAL_LIVESTATS_SEC = 20        # in-game gold/kills refresh while live
INTERVAL_STREAM_POLL_SEC = 600     # 24/7 stream schedule refresh
INTERVAL_CATALOG_SEC = 86400       # team/roster/league catalog refresh
INTERVAL_UPDATE_CHECK_SEC = 21600  # software update check

HTTP_TIMEOUT_DEFAULT = 12.0
HTTP_TIMEOUT_DOWNLOAD = 60.0
HTTP_MAX_RETRIES = 3
HTTP_BACKOFF_FACTOR = 1.5
HTTP_MAX_JSON_BYTES = 8 * 1024 * 1024  # getTeams is ~1.5 MB

# ==============================================================================
# 4. HEXTECH VISUAL PALETTE (OFFICIAL LEAGUE DARK THEME)
# ==============================================================================
COLOR_BG = "#091428"            # Deep Hextech Navy window background
COLOR_BG_DARK = "#050b14"       # Darker header/footer background
COLOR_SURFACE = "#0f1923"       # Card surface tiles
COLOR_SURFACE_HOVER = "#17263c" # Card hover state
COLOR_BORDER = "#1e2a38"        # Crisp card border
COLOR_BORDER_FOCUS = "#c8aa6e"  # Selected/followed card border

COLOR_GOLD = "#c8aa6e"          # Hextech Metallic Gold
COLOR_GOLD_HOVER = "#f0e6d2"    # Champagne hover
COLOR_CYAN = "#0ac8b9"          # Summoner Magic Teal
COLOR_CYAN_DIM = "#0397ab"      # Muted teal
COLOR_LIVE = "#e84057"          # Live badge red
COLOR_BANGER = "#ff4655"        # S-Tier Banger coral
COLOR_BLUE_SIDE = "#4a90e2"
COLOR_RED_SIDE = "#e84057"

COLOR_TEXT_PRIMARY = "#f0f4f8"
COLOR_TEXT_MUTED = "#8a9ba8"
COLOR_TEXT_DIM = "#536675"

FONT_FAMILY = "Segoe UI"

# ==============================================================================
# 5. LEAGUES
# ==============================================================================
# Default followed leagues (Riot league slugs). The full list is loaded live
# from getLeagues and shown in the Watchlist tab.
DEFAULT_FOLLOWED_LEAGUES = [
    "worlds", "msi", "first_stand", "lck", "lpl", "lec", "lcs", "lcp", "cblol-brazil",
]
