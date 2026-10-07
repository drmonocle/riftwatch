"""
RiftScout Team / Player / League Catalog (Phase 2)
Builds a searchable directory of active pro teams, their registered rosters,
and all Riot leagues. Refreshed from Riot at most once a day and cached locally.

Note: Riot's team rosters list every registered player, academy players
included, so "on the roster" is not the same as "starting". Confirmed starting
lineups come from live stats while a game is in progress (see watchlist.py).
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from . import config as C
from . import db
from . import net

log = logging.getLogger(__name__)

ROLE_LABELS = {"top": "Top", "jungle": "Jungle", "mid": "Mid", "bottom": "Bot", "support": "Support"}
ROLE_ORDER = {"top": 0, "jungle": 1, "mid": 2, "bottom": 3, "support": 4}


def role_label(role: str) -> str:
    return ROLE_LABELS.get((role or "").lower(), "Sub")


# ------------------------------------------------------------------ parsing
def parse_leagues(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    leagues = ((payload or {}).get("data") or {}).get("leagues") or []
    out = []
    for i, l in enumerate(leagues):
        if not l.get("slug") or not l.get("name"):
            continue
        out.append({
            "slug": l["slug"],
            "league_id": str(l.get("id") or ""),
            "name": l["name"],
            "region": l.get("region") or "",
            "image": net.https(l.get("image") or ""),
            "priority": i,
        })
    return out


def parse_teams(payload: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Keep active teams that belong to a league and have players."""
    teams_raw = ((payload or {}).get("data") or {}).get("teams") or []
    teams, rosters = [], []
    for t in teams_raw:
        home = t.get("homeLeague") or {}
        players = [p for p in t.get("players") or [] if (p.get("summonerName") or "").strip()]
        if t.get("status") != "active" or not home.get("name") or not players or not t.get("slug"):
            continue
        teams.append({
            "slug": t["slug"],
            "team_id": str(t.get("id") or ""),
            "code": (t.get("code") or "").strip() or t["slug"].upper(),
            "name": (t.get("name") or t["slug"]).strip(),
            "image": net.https(t.get("image") or ""),
            "league_name": home.get("name", ""),
            "region": home.get("region", ""),
        })
        seen = set()
        for p in players:
            name = p["summonerName"].strip()
            if name.lower() in seen:
                continue
            seen.add(name.lower())
            rosters.append({
                "team_slug": t["slug"],
                "player_name": name,
                "role": (p.get("role") or "").lower(),
                "first_name": p.get("firstName") or "",
                "last_name": p.get("lastName") or "",
                "image": net.https(p.get("image") or ""),
            })
    return teams, rosters


# ------------------------------------------------------------------ catalog
@dataclass
class PlayerEntry:
    name: str
    role: str
    team_slug: str
    team_code: str
    team_name: str
    real_name: str = ""


@dataclass
class Catalog:
    leagues: List[Dict[str, Any]] = field(default_factory=list)
    teams: List[Dict[str, Any]] = field(default_factory=list)
    players: List[PlayerEntry] = field(default_factory=list)

    # indexes
    def __post_init__(self):
        self.reindex()

    def reindex(self) -> None:
        self.team_by_slug = {t["slug"]: t for t in self.teams}
        self.league_by_slug = {l["slug"]: l for l in self.leagues}
        self.players_by_team: Dict[str, List[PlayerEntry]] = {}
        self.teams_by_player: Dict[str, List[PlayerEntry]] = {}
        for p in self.players:
            self.players_by_team.setdefault(p.team_slug, []).append(p)
            self.teams_by_player.setdefault(p.name.lower(), []).append(p)
        for plist in self.players_by_team.values():
            plist.sort(key=lambda p: (ROLE_ORDER.get(p.role, 9), p.name.lower()))

    @property
    def empty(self) -> bool:
        return not self.teams

    # ---- lookup
    def find_team(self, code: str, name: str = "") -> Optional[Dict[str, Any]]:
        """Match a schedule team (code + display name) to a catalog team.
        Codes are not unique (HLE, HLE Challengers, HLE Academy), so prefer an
        exact name match, then a code match in a top league."""
        code_l, name_l = (code or "").lower(), (name or "").strip().lower()
        candidates = [t for t in self.teams if t["code"].lower() == code_l]
        if name_l:
            for t in candidates:
                if t["name"].lower() == name_l:
                    return t
            for t in self.teams:
                if t["name"].lower() == name_l:
                    return t
        if len(candidates) == 1:
            return candidates[0]
        if candidates:
            top = {s.upper() for s in C.DEFAULT_FOLLOWED_LEAGUES} | {"LCK", "LPL", "LEC", "LCS", "LCP", "CBLOL"}
            candidates.sort(key=lambda t: 0 if t["league_name"].upper() in top else 1)
            return candidates[0]
        return None

    def roster_for(self, code: str, name: str = "") -> List[PlayerEntry]:
        t = self.find_team(code, name)
        return list(self.players_by_team.get(t["slug"], [])) if t else []

    # ---- search
    def search_teams(self, query: str, limit: int = 40) -> List[Dict[str, Any]]:
        q = (query or "").strip().lower()
        if not q:
            return []
        def score(t):
            code, name = t["code"].lower(), t["name"].lower()
            if code == q or name == q:
                return 0
            if code.startswith(q) or name.startswith(q):
                return 1
            return 2
        hits = [t for t in self.teams if q in t["code"].lower() or q in t["name"].lower()
                or q in (t.get("league_name") or "").lower()]
        hits.sort(key=lambda t: (score(t), t["name"].lower()))
        return hits[:limit]

    def search_players(self, query: str, limit: int = 40) -> List[PlayerEntry]:
        q = (query or "").strip().lower()
        if not q:
            return []
        hits = [p for p in self.players if q in p.name.lower() or q in p.real_name.lower()]
        hits.sort(key=lambda p: (0 if p.name.lower() == q else 1 if p.name.lower().startswith(q) else 2,
                                 p.name.lower()))
        return hits[:limit]


def _build(leagues, teams, rosters) -> Catalog:
    tby = {t["slug"]: t for t in teams}
    players = []
    for r in rosters:
        t = tby.get(r["team_slug"])
        if not t:
            continue
        real = f"{r.get('first_name', '')} {r.get('last_name', '')}".strip()
        players.append(PlayerEntry(r["player_name"], r.get("role", ""), t["slug"], t["code"], t["name"], real))
    return Catalog(leagues=leagues, teams=teams, players=players)


def load_cached(db_path=None) -> Catalog:
    return _build(db.get_leagues(db_path), db.get_teams(db_path), db.get_rosters(db_path))


def catalog_age_sec(db_path=None) -> float:
    try:
        return time.time() - float(db.get_meta("catalog_synced_at", db_path) or 0)
    except ValueError:
        return float("inf")


def refresh(db_path=None, api_key: str = C.RIOT_API_KEY) -> Optional[Catalog]:
    """Download leagues + teams from Riot and replace the cached catalog."""
    headers = {"x-api-key": api_key}
    lp = net.fetch_json(C.RIOT_LEAGUES_URL, headers=headers)
    tp = net.fetch_json(C.RIOT_TEAMS_URL, headers=headers, timeout=30.0)
    leagues = parse_leagues(lp) if isinstance(lp, dict) else []
    teams, rosters = parse_teams(tp) if isinstance(tp, dict) else ([], [])
    if not leagues and not teams:
        return None
    db.replace_catalog(leagues, teams, rosters, db_path)
    db.set_meta("catalog_synced_at", str(time.time()), db_path)
    log.info("Catalog refreshed: %d leagues, %d teams, %d roster entries", len(leagues), len(teams), len(rosters))
    return load_cached(db_path)
