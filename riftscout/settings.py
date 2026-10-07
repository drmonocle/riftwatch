"""
RiftScout Settings & Watchlist Persistence Manager
Stores user configuration, followed entities, and notification preferences.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from . import config as C

log = logging.getLogger(__name__)

DEFAULT_SETTINGS: Dict[str, Any] = {
    "version": "1.0",
    "followed_teams": ["T1", "GEN", "G2", "FLY", "BLG"],
    "followed_regions": ["lck", "lpl", "lec", "lta", "worlds", "msi"],
    "followed_players": ["Faker", "Chovy", "Ruler", "Caps", "Bwipo"],
    "spoiler_mode": False,
    "notify_pregame": True,
    "notify_pregame_mins": 30,
    "notify_kickoff": True,
    "notify_final": True,
    "notify_stream_banger": True,
    "sound_enabled": True,
    "start_with_windows": False,
    "minimize_to_tray": True,
    "ticker_bar_enabled": False,
    "ticker_bar_coords": {"x": 100, "y": 100, "opacity": 0.95},
    "auto_update_check": True,
}


class SettingsManager:
    """Thread-safe settings and watchlist state manager."""

    def __init__(self, file_path: Optional[Path] = None):
        self.file_path = file_path or C.SETTINGS_PATH
        self.data: Dict[str, Any] = dict(DEFAULT_SETTINGS)
        self.load()

    def load(self) -> None:
        """Load settings from JSON file with fallback to defaults."""
        if not self.file_path.exists():
            self.save()
            return

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                saved = json.load(f)
                if isinstance(saved, dict):
                    # Shallow merge with defaults to preserve new keys
                    self.data = {**DEFAULT_SETTINGS, **saved}
        except Exception as exc:
            log.warning("Could not read settings from %s (%s). Using defaults.", self.file_path, exc)
            self.data = dict(DEFAULT_SETTINGS)

    def save(self) -> bool:
        """Atomically persist settings to JSON file via temp file."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        temp_file = self.file_path.with_suffix(".tmp")
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            temp_file.replace(self.file_path)
            return True
        except Exception as exc:
            log.error("Failed saving settings to %s: %s", self.file_path, exc)
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass
            return False

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value
        self.save()

    # -------------------------------------------------------------------------
    # Watchlist & Following Helper Methods
    # -------------------------------------------------------------------------
    def is_team_followed(self, team_code_or_name: str) -> bool:
        target = (team_code_or_name or "").strip().lower()
        followed = [t.lower() for t in self.data.get("followed_teams", [])]
        return target in followed

    def toggle_team(self, team_code: str) -> bool:
        """Add or remove team from watchlist. Returns True if now followed."""
        teams = list(self.data.get("followed_teams", []))
        code_clean = team_code.strip()
        matched = [t for t in teams if t.lower() == code_clean.lower()]
        if matched:
            for m in matched:
                teams.remove(m)
            is_followed = False
        else:
            teams.append(code_clean)
            is_followed = True
        self.data["followed_teams"] = teams
        self.save()
        return is_followed

    def is_region_followed(self, league_slug: str) -> bool:
        target = (league_slug or "").strip().lower()
        followed = [r.lower() for r in self.data.get("followed_regions", [])]
        return target in followed

    def toggle_region(self, league_slug: str) -> bool:
        regions = list(self.data.get("followed_regions", []))
        slug_clean = league_slug.strip().lower()
        if slug_clean in regions:
            regions.remove(slug_clean)
            is_followed = False
        else:
            regions.append(slug_clean)
            is_followed = True
        self.data["followed_regions"] = regions
        self.save()
        return is_followed

    def is_player_followed(self, player_name: str) -> bool:
        target = (player_name or "").strip().lower()
        followed = [p.lower() for p in self.data.get("followed_players", [])]
        return target in followed

    def toggle_player(self, player_name: str) -> bool:
        players = list(self.data.get("followed_players", []))
        name_clean = player_name.strip()
        matched = [p for p in players if p.lower() == name_clean.lower()]
        if matched:
            for m in matched:
                players.remove(m)
            is_followed = False
        else:
            players.append(name_clean)
            is_followed = True
        self.data["followed_players"] = players
        self.save()
        return is_followed

    def is_match_followed(self, match: Dict[str, Any], roster_players: Optional[Set[str]] = None) -> bool:
        """
        Check if a match matches any followed team, region, or starting player.
        """
        # 1. Check Teams
        t1 = match.get("team1_code") or match.get("team1_name") or ""
        t2 = match.get("team2_code") or match.get("team2_name") or ""
        if self.is_team_followed(t1) or self.is_team_followed(t2):
            return True

        # 2. Check Region
        league = match.get("league_slug") or ""
        if self.is_region_followed(league):
            return True

        # 3. Check Players
        if roster_players:
            followed = {p.lower() for p in self.data.get("followed_players", [])}
            if any(rp.lower() in followed for rp in roster_players):
                return True

        return False
