"""
RiftScout Configuration & Global Constants
Defines endpoints, visual Hextech tokens, file paths, and runtime settings.
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

# Ensure runtime directories exist
APPDATA_DIR.mkdir(parents=True, exist_ok=True)
UPDATES_DIR.mkdir(parents=True, exist_ok=True)

# ==============================================================================
# 2. DATA SOURCES & UPSTREAM APIS
# ==============================================================================
# Riot Games Unofficial/Persisted LoL Esports API
RIOT_API_KEY = "0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z"
RIOT_SCHEDULE_URL = "https://esports-api.lolesports.com/persisted/gw/getSchedule?hl=en-US"
RIOT_LIVE_URL = "https://esports-api.lolesports.com/persisted/gw/getLive?hl=en-US"

# Leaguepedia / MediaWiki Cargo API
LEAGUEPEDIA_API_URL = "https://lol.fandom.com/api.php"

# Local & Remote 24/7 Twitch Stream Sources
LOCAL_TWITCH_DB_PATH = Path("lol_broadcast_schedule.db")
LOCAL_TWITCH_JSON_PATH = Path("schedule_master.json")
REMOTE_TWITCH_SCHEDULE_URL = "https://lolworlds.com/api.ashx?type=schedule-master"
TWITCH_CHANNEL_URL = "https://twitch.tv/LoLWorldChampionship"

# GitHub Releases & Automated Update Configuration
GITHUB_REPO = "drmonocle/rift-scout"
GITHUB_LATEST_RELEASE_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
GITHUB_PROJECT_URL = f"https://github.com/{GITHUB_REPO}"

# Honest User-Agent header
USER_AGENT = f"RiftScout/{APP_VERSION} (Esports Desktop Companion; +{GITHUB_PROJECT_URL})"

# Security Allowlist for Network Requests
ALLOWED_HOSTS = {
    "esports-api.lolesports.com",
    "static.lolesports.com",
    "lol.fandom.com",
    "lolworlds.com",
    "api.github.com",
    "github.com",
    "objects.githubusercontent.com",
}

# ==============================================================================
# 3. POLLING & TIMING INTERVALS (SECONDS)
# ==============================================================================
INTERVAL_IDLE_POLL_SEC = 300       # 5 minutes when no followed game is live
INTERVAL_LIVE_POLL_SEC = 45        # 45 seconds during active live matches
INTERVAL_STREAM_POLL_SEC = 120     # 2 minutes for Twitch stream schedule sync
INTERVAL_UPDATE_CHECK_SEC = 21600  # Check for software updates every 6 hours

HTTP_TIMEOUT_DEFAULT = 12.0
HTTP_TIMEOUT_DOWNLOAD = 60.0
HTTP_MAX_RETRIES = 3
HTTP_BACKOFF_FACTOR = 1.5

# ==============================================================================
# 4. HEXTECH VISUAL PALETTE (OFFICIAL LEAGUE DARK THEME)
# ==============================================================================
COLOR_BG = "#091428"            # Deep Hextech Navy window background
COLOR_BG_DARK = "#050b14"       # Darker sub-canvas & footer background
COLOR_SURFACE = "#0f1923"       # Card surface tiles
COLOR_SURFACE_HOVER = "#17263c" # Card hover state
COLOR_BORDER = "#1e2a38"        # Crisp card border
COLOR_BORDER_FOCUS = "#c8aa6e"  # Selected card border

COLOR_GOLD = "#c8aa6e"          # Hextech Metallic Gold (Primary accents & active tabs)
COLOR_GOLD_HOVER = "#f0e6d2"    # Bright Gold / Champagne hover
COLOR_CYAN = "#0ac8b9"          # Summoner Magic Teal (Badges, links, highlights)
COLOR_CYAN_DIM = "#0397ab"      # Muted teal
COLOR_LIVE = "#e84057"          # Hot Crimson Red for live badges
COLOR_BANGER = "#ff4655"        # Bright coral for S-Tier Bangers

COLOR_TEXT_PRIMARY = "#f0f4f8"  # High-contrast white/silver headings
COLOR_TEXT_MUTED = "#8a9ba8"    # Soft slate for metadata, tags, dates
COLOR_TEXT_DIM = "#536675"      # Faint labels & footnotes

# ==============================================================================
# 5. MAJOR LEAGUES & REGIONS
# ==============================================================================
MAJOR_REGIONS = {
    "lck": {"name": "LCK (Korea)", "code": "LCK", "icon": "🇰🇷"},
    "lpl": {"name": "LPL (China)", "code": "LPL", "icon": "🇨🇳"},
    "lec": {"name": "LEC (EMEA)", "code": "LEC", "icon": "🇪🇺"},
    "lta": {"name": "LTA (Americas)", "code": "LTA", "icon": "🌎"},
    "lcs": {"name": "LCS (Legacy)", "code": "LCS", "icon": "🇺🇸"},
    "worlds": {"name": "World Championship", "code": "WORLDS", "icon": "🏆"},
    "msi": {"name": "Mid-Season Invitational", "code": "MSI", "icon": "⚡"},
    "first_stand": {"name": "First Stand", "code": "FS", "icon": "⚔️"},
}
