"""
RiftScout Settings & Watchlist Persistence
Stores user preferences and followed teams, leagues and players in
%APPDATA%\\RiftScout\\settings.json (atomic writes, thread-safe).
"""

import copy
import json
import logging
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import config as C

log = logging.getLogger(__name__)

SETTINGS_VERSION = 2

DEFAULT_SETTINGS: Dict[str, Any] = {
    "version": SETTINGS_VERSION,
    # Followed teams are {"code", "name"} pairs: codes alone are not unique.
    "followed_teams": [],
    "followed_leagues": list(C.DEFAULT_FOLLOWED_LEAGUES),
    "followed_regions": list(C.DEFAULT_FOLLOWED_REGIONS),
    "followed_players": [],
    "onboarding_completed": False,
    "spoiler_mode": False,
    "minimize_to_tray_on_close": True,
    "auto_update_check": True,
    "start_with_windows": False,
    "schedule_filter_followed": False,
    "schedule_filter_league": "",
    "schedule_filter_range": "upcoming",
    "window_geometry": "",
    "last_tab": "live",
    "default_tab": "live",
    # Used by Phase 4 (tray / toasts / ticker); stored now so they persist.
    "notify_pregame": True,
    "notify_pregame_mins": 30,
    "notify_kickoff": True,
    "notify_final": True,
    "notify_stream": True,
}

_LEGACY_REGION_MAP = {"lta": ["lcs", "cblol-brazil"]}


def migrate(data: Dict[str, Any]) -> Dict[str, Any]:
    """Upgrade settings written by older versions."""
    out = dict(data)
    ver = out.get("version", 1)
    try:
        ver = int(ver)
    except (ValueError, TypeError):
        ver = 1

    teams = out.get("followed_teams") or []
    out["followed_teams"] = [
        t if isinstance(t, dict) else {"code": str(t), "name": ""}
        for t in teams if t
    ]

    # Legacy v1 migration: followed_regions previously held league slugs ("lck", "lta", etc.)
    if "followed_regions" in out and "followed_leagues" not in out:
        leagues: List[str] = []
        for r in out.pop("followed_regions") or []:
            for slug in _LEGACY_REGION_MAP.get(str(r).lower(), [str(r).lower()]):
                if slug not in leagues:
                    leagues.append(slug)
        out["followed_leagues"] = leagues

    # Modern followed_regions (e.g. "KOREA", "INTERNATIONAL", "NORTH AMERICA")
    if "followed_regions" not in out or not isinstance(out["followed_regions"], list):
        out["followed_regions"] = list(C.DEFAULT_FOLLOWED_REGIONS)
    else:
        out["followed_regions"] = [str(r).upper() for r in out["followed_regions"]]

    if "followed_leagues" not in out:
        out["followed_leagues"] = list(C.DEFAULT_FOLLOWED_LEAGUES)

    if "onboarding_completed" not in out:
        out["onboarding_completed"] = False

    if "minimize_to_tray_on_close" not in out:
        out["minimize_to_tray_on_close"] = True

    if "default_tab" not in out:
        out["default_tab"] = "live"

    for stale in ("ticker_bar_enabled", "ticker_bar_coords", "sound_enabled", "minimize_to_tray",
                  "notify_stream_banger"):
        out.pop(stale, None)
    out["version"] = SETTINGS_VERSION
    return out


class SettingsManager:
    """Thread-safe settings and watchlist state."""

    def __init__(self, file_path: Optional[Path] = None):
        self.file_path = Path(file_path) if file_path else C.SETTINGS_PATH
        self._lock = threading.RLock()
        self.data: Dict[str, Any] = copy.deepcopy(DEFAULT_SETTINGS)
        self.load()

    # ---------------------------------------------------------------- io
    def load(self) -> None:
        with self._lock:
            if not self.file_path.exists():
                self.save()
                return
            try:
                saved = json.loads(self.file_path.read_text(encoding="utf-8"))
                if isinstance(saved, dict):
                    self.data = {**copy.deepcopy(DEFAULT_SETTINGS), **migrate(saved)}
                    self.save()
            except Exception as exc:
                log.warning("Could not read settings %s (%s); using defaults.", self.file_path, exc)
                self.data = copy.deepcopy(DEFAULT_SETTINGS)

    def save(self) -> bool:
        with self._lock:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.file_path.with_suffix(".tmp")
            try:
                tmp.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8")
                tmp.replace(self.file_path)
                return True
            except Exception as exc:
                log.error("Failed saving settings to %s: %s", self.file_path, exc)
                try:
                    tmp.unlink()
                except Exception:
                    pass
                return False

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return copy.deepcopy(self.data.get(key, default))

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self.data[key] = value
            self.save()

    # ---------------------------------------------------------------- teams
    def followed_teams(self) -> List[Dict[str, str]]:
        return self.get("followed_teams", [])

    def is_team_followed(self, code: str, name: str = "") -> bool:
        code_l, name_l = (code or "").strip().lower(), (name or "").strip().lower()
        if not code_l or code_l == "tbd":
            return False
        for t in self.followed_teams():
            if t.get("code", "").lower() != code_l:
                continue
            stored = (t.get("name") or "").lower()
            # Entries without a stored name (legacy) match on code alone.
            if not stored or not name_l or stored == name_l:
                return True
        return False

    def toggle_team(self, code: str, name: str = "") -> bool:
        """Follow/unfollow a team. Returns True if it is now followed."""
        with self._lock:
            teams = self.followed_teams()
            code_l, name_l = code.strip().lower(), (name or "").strip().lower()
            keep = [t for t in teams if not (
                t.get("code", "").lower() == code_l
                and (not t.get("name") or not name_l or t["name"].lower() == name_l))]
            now_followed = len(keep) == len(teams)
            if now_followed:
                keep.append({"code": code.strip(), "name": (name or "").strip()})
            self.data["followed_teams"] = keep
            self.save()
            return now_followed

    def attach_team_names(self, lookup) -> int:
        """Fill in names for code-only (legacy) follows. `lookup(code)` returns a
        team name or None. Returns how many entries were updated."""
        with self._lock:
            teams = self.followed_teams()
            changed = 0
            for t in teams:
                if not t.get("name"):
                    name = lookup(t.get("code", ""))
                    if name:
                        t["name"] = name
                        changed += 1
            if changed:
                self.data["followed_teams"] = teams
                self.save()
            return changed

    # ---------------------------------------------------------------- leagues
    def is_league_followed(self, slug: str) -> bool:
        return (slug or "").strip().lower() in [s.lower() for s in self.get("followed_leagues", [])]

    def toggle_league(self, slug: str) -> bool:
        with self._lock:
            leagues = self.get("followed_leagues", [])
            s = slug.strip().lower()
            if s in leagues:
                leagues.remove(s)
                now_followed = False
            else:
                leagues.append(s)
                now_followed = True
            self.data["followed_leagues"] = leagues
            self.save()
            return now_followed

    # ---------------------------------------------------------------- regions
    def followed_regions(self) -> List[str]:
        return [str(r).upper() for r in self.get("followed_regions", [])]

    def is_region_followed(self, region: str) -> bool:
        return (region or "").strip().upper() in self.followed_regions()

    def toggle_region(self, region: str) -> bool:
        with self._lock:
            regions = self.followed_regions()
            r = region.strip().upper()
            if r in regions:
                regions.remove(r)
                now_followed = False
            else:
                regions.append(r)
                now_followed = True
            self.data["followed_regions"] = regions
            self.save()
            return now_followed

    # ---------------------------------------------------------------- players
    def is_player_followed(self, player_name: str) -> bool:
        target = (player_name or "").strip().lower()
        return bool(target) and target in [p.lower() for p in self.get("followed_players", [])]

    def toggle_player(self, player_name: str) -> bool:
        with self._lock:
            players = self.get("followed_players", [])
            name = player_name.strip()
            matched = [p for p in players if p.lower() == name.lower()]
            if matched:
                players = [p for p in players if p.lower() != name.lower()]
                now_followed = False
            else:
                players.append(name)
                now_followed = True
            self.data["followed_players"] = players
            self.save()
            return now_followed

    def reset_all_follows(self) -> None:
        """Clear all followed teams, players, leagues, and regions."""
        with self._lock:
            self.data["followed_teams"] = []
            self.data["followed_players"] = []
            self.data["followed_leagues"] = []
            self.data["followed_regions"] = []
            self.save()
