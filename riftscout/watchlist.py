"""
RiftScout Watchlist Engine (Phase 2)
Decides why a match matters to the user: a followed team, a followed league,
or a followed player. Player matches are "confirmed" when the player is in the
live starting lineup, otherwise "roster" (registered on the team).
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .catalog import Catalog, role_label
from .settings import SettingsManager


@dataclass(frozen=True)
class FollowReason:
    kind: str          # "team" | "player" | "league"
    label: str         # short text for badges
    confirmed: bool = True

    @property
    def strong(self) -> bool:
        """Team/player follows are explicit; league follows are broad."""
        return self.kind in ("team", "player")


class Watchlist:
    def __init__(self, settings: SettingsManager, catalog: Optional[Catalog] = None):
        self.settings = settings
        self.catalog = catalog or Catalog()

    def set_catalog(self, catalog: Catalog) -> None:
        self.catalog = catalog

    # ---------------------------------------------------------------- pro matches
    def reasons(self, match: Dict[str, Any], livestats: Optional[Dict[str, Any]] = None) -> List[FollowReason]:
        out: List[FollowReason] = []
        s = self.settings
        for i in (1, 2):
            code, name = match.get(f"team{i}_code", ""), match.get(f"team{i}_name", "")
            if s.is_team_followed(code, name):
                out.append(FollowReason("team", code))

        followed_players = {p.lower(): p for p in s.get("followed_players", [])}
        if followed_players:
            seen = set()
            # 1) Confirmed starters from live stats.
            if livestats:
                for side in ("blue", "red"):
                    for p in (livestats.get(side) or {}).get("players", []):
                        key = (p.get("name") or "").lower()
                        if key in followed_players and key not in seen:
                            seen.add(key)
                            out.append(FollowReason(
                                "player", f"{followed_players[key]} starting ({role_label(p.get('role'))})", True))
            # 2) Registered roster from the catalog.
            for i in (1, 2):
                for p in self.catalog.roster_for(match.get(f"team{i}_code", ""), match.get(f"team{i}_name", "")):
                    key = p.name.lower()
                    if key in followed_players and key not in seen:
                        seen.add(key)
                        out.append(FollowReason("player", f"{p.name} ({p.team_code} {role_label(p.role)})", False))

        # 3) Region follows (e.g. KOREA, EUROPE, NORTH AMERICA, INTERNATIONAL)
        league_info = self.catalog.league_by_slug.get(match.get("league_slug", ""))
        region = (match.get("region") or (league_info.get("region") if league_info else "") or "").upper()
        if region and s.is_region_followed(region):
            out.append(FollowReason("region", region.title(), True))

        if s.is_league_followed(match.get("league_slug", "")):
            out.append(FollowReason("league", match.get("league_name") or match.get("league_slug", ""), True))
        return out

    def is_followed(self, match: Dict[str, Any], livestats: Optional[Dict[str, Any]] = None) -> bool:
        return bool(self.reasons(match, livestats))

    def is_strong(self, match: Dict[str, Any], livestats: Optional[Dict[str, Any]] = None) -> bool:
        return any(r.strong for r in self.reasons(match, livestats))

    # ---------------------------------------------------------------- stream rebroadcasts
    def stream_reasons(self, event: Dict[str, Any]) -> List[FollowReason]:
        """Rebroadcast entries only carry historical team codes (e.g. SKT)."""
        out = []
        for key in ("team1", "team2"):
            code = event.get(key) or ""
            if code and self.settings.is_team_followed(code):
                out.append(FollowReason("team", code))
        return out
