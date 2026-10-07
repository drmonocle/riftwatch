"""
RiftScout Hybrid Data Coordinator
Fetches and normalizes pro match data from Riot's LoL Esports API (schedule,
live events, in-game live stats) with local caching. Parsing is done by pure
functions so it can be unit-tested against recorded payloads.
"""

import datetime
import logging
import time
from typing import Any, Dict, List, Optional

from . import config as C
from . import db
from . import net

log = logging.getLogger(__name__)


# ------------------------------------------------------------------ time helpers
def parse_iso_datetime(dt_str: str) -> Optional[datetime.datetime]:
    """Parse ISO-8601 UTC timestamp string to an aware datetime."""
    if not dt_str:
        return None
    try:
        dt = datetime.datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=datetime.timezone.utc)
    except Exception:
        return None


def utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def format_relative_time(dt_str: str, now: Optional[datetime.datetime] = None) -> str:
    """Human-readable relative time, e.g. 'in 2h 5m' or '15m ago'."""
    dt = parse_iso_datetime(dt_str)
    if not dt:
        return "TBD"
    total = int((dt - (now or utcnow())).total_seconds())
    if total <= 0:
        past = -total
        if past < 60:
            return "just now"
        if past < 3600:
            return f"{past // 60}m ago"
        if past < 86400:
            return f"{past // 3600}h ago"
        return f"{past // 86400}d ago"
    if total < 3600:
        return f"in {max(1, total // 60)}m"
    if total < 86400:
        return f"in {total // 3600}h {(total % 3600) // 60}m"
    return f"in {total // 86400}d {(total % 86400) // 3600}h"


def format_local_match_time(dt_str: str) -> str:
    """ISO UTC -> local time, e.g. 'Oct 07, 7:00 AM'."""
    dt = parse_iso_datetime(dt_str)
    if not dt:
        return "Time TBD"
    local = dt.astimezone()
    return local.strftime("%b %d, ") + local.strftime("%I:%M %p").lstrip("0")


def format_local_day(dt_str: str) -> str:
    """ISO UTC -> local day header, e.g. 'Wednesday, Oct 07'."""
    dt = parse_iso_datetime(dt_str)
    return dt.astimezone().strftime("%A, %b %d") if dt else "Date TBD"


# ------------------------------------------------------------------ parsing
def _team(t: Dict[str, Any]) -> Dict[str, Any]:
    res = t.get("result") or {}
    return {
        "id": str(t.get("id") or ""),
        "name": t.get("name") or "TBD",
        "code": t.get("code") or "TBD",
        "image": net.https(t.get("image") or ""),
        "score": res.get("gameWins") or 0,
        "outcome": res.get("outcome"),
    }


def _stream_url(streams: List[Dict[str, Any]]) -> str:
    """Prefer an English Twitch/YouTube stream, then any Twitch/YouTube stream, then any official provider stream."""
    def url(s):
        p = (s.get("provider") or "").lower().strip()
        param = (s.get("parameter") or "").strip()
        if not param:
            return ""
        if p == "twitch":
            return f"https://www.twitch.tv/{param}"
        if p == "youtube":
            return f"https://www.youtube.com/watch?v={param}"
        if p in ("afreecatv", "afreeca", "soop"):
            return f"https://play.sooplive.co.kr/{param}"
        if p == "bilibili":
            return f"https://live.bilibili.com/{param}"
        if p == "huya":
            return f"https://www.huya.com/{param}"
        if p == "chzzk":
            return f"https://chzzk.naver.com/live/{param}"
        if p == "trovo":
            return f"https://trovo.live/s/{param}"
        return ""
    english = [s for s in streams if (s.get("locale") or "").startswith("en")]
    for s in english + list(streams):
        u = url(s)
        if u:
            return u
    return ""


def normalize_event(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Convert a Riot schedule/live event into RiftScout's flat match dict."""
    if event.get("type") not in (None, "match"):
        return None
    match = event.get("match") or {}
    teams = match.get("teams") or []
    if len(teams) < 2:
        return None
    t1, t2 = _team(teams[0] or {}), _team(teams[1] or {})
    league = event.get("league") or {}
    strategy = match.get("strategy") or {}
    winner = t1["code"] if t1["outcome"] == "win" else t2["code"] if t2["outcome"] == "win" else ""
    games = []
    for g in match.get("games") or []:
        sides = {s.get("side"): str(s.get("id")) for s in g.get("teams") or []}
        games.append({
            "number": g.get("number"),
            "id": str(g.get("id") or ""),
            "state": g.get("state", "unstarted"),
            "blue_team_id": sides.get("blue", ""),
            "red_team_id": sides.get("red", ""),
        })
    return {
        "match_id": str(match.get("id") or event.get("id") or ""),
        "league_name": league.get("name") or "Unknown League",
        "league_slug": league.get("slug") or "unknown",
        "league_image": net.https(league.get("image") or ""),
        "block_name": event.get("blockName") or "",
        "start_time_utc": event.get("startTime") or "",
        "state": event.get("state") or "unstarted",
        "team1_id": t1["id"], "team1_name": t1["name"], "team1_code": t1["code"],
        "team1_image": t1["image"], "team1_score": t1["score"],
        "team2_id": t2["id"], "team2_name": t2["name"], "team2_code": t2["code"],
        "team2_image": t2["image"], "team2_score": t2["score"],
        "best_of": strategy.get("count") or 1,
        "winner": winner,
        "stream_url": _stream_url(event.get("streams") or []),
        "games": games,
    }


def normalize_events(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for e in events or []:
        m = normalize_event(e)
        if m and m["match_id"]:
            out.append(m)
    return out


def current_game(match: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    games = match.get("games") or []
    for g in games:
        if g.get("state") == "inProgress":
            return g
    return None


def _strip_code(name: str, codes: List[str]) -> str:
    for code in codes:
        if code and name.upper().startswith(code.upper() + " "):
            return name[len(code) + 1:]
    return name


def parse_livestats(window: Dict[str, Any], team_codes: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
    """Reduce a livestats window payload to scoreboard numbers + lineups."""
    try:
        frames = window.get("frames") or []
        meta = window.get("gameMetadata") or {}
        if not frames:
            return None
        fr = frames[-1]
        codes = team_codes or []
        out = {"state": fr.get("gameState", ""), "timestamp": fr.get("rfc460Timestamp", "")}
        for side, mkey in (("blue", "blueTeamMetadata"), ("red", "redTeamMetadata")):
            t = fr.get(f"{side}Team") or {}
            m = meta.get(mkey) or {}
            out[side] = {
                "team_id": str(m.get("esportsTeamId") or ""),
                "gold": t.get("totalGold", 0),
                "kills": t.get("totalKills", 0),
                "towers": t.get("towers", 0),
                "inhibitors": t.get("inhibitors", 0),
                "barons": t.get("barons", 0),
                "dragons": list(t.get("dragons") or []),
                "players": [
                    {
                        "name": _strip_code(p.get("summonerName", ""), codes),
                        "champion": p.get("championId", ""),
                        "role": p.get("role", ""),
                    }
                    for p in m.get("participantMetadata") or []
                ],
            }
        return out
    except Exception as exc:
        log.warning("Could not parse livestats window: %s", exc)
        return None


# ------------------------------------------------------------------ coordinator
class DataCoordinator:
    """Fetches from Riot, normalizes, caches. Methods return None when offline."""

    def __init__(self, api_key: str = C.RIOT_API_KEY, db_path=None):
        self.headers = {"x-api-key": api_key}
        self.db_path = db_path

    def _get_priority_league_ids(self) -> List[str]:
        ids = set(C.KNOWN_LEAGUE_IDS.values())
        try:
            db_leagues = db.get_leagues(self.db_path)
            for l in db_leagues:
                slug, lid = l.get("slug"), l.get("league_id")
                if slug in C.DEFAULT_FOLLOWED_LEAGUES and lid:
                    ids.add(lid)
        except Exception:
            pass
        return list(ids)

    def fetch_schedule(self, league_ids: Optional[Any] = None) -> Optional[List[Dict[str, Any]]]:
        payload = net.fetch_json(C.RIOT_SCHEDULE_URL, headers=self.headers)
        all_matches: List[Dict[str, Any]] = []
        if isinstance(payload, dict):
            events = ((payload.get("data") or {}).get("schedule") or {}).get("events") or []
            all_matches.extend(normalize_events(events))

        target_ids = list(league_ids) if league_ids is not None else self._get_priority_league_ids()
        if target_ids:
            import concurrent.futures
            def _fetch_league(lid: str) -> List[Dict[str, Any]]:
                url = f"{C.RIOT_API_BASE}/getSchedule?hl=en-US&leagueId={lid}"
                lp = net.fetch_json(url, headers=self.headers, timeout=8.0, max_retries=1)
                if isinstance(lp, dict):
                    evs = ((lp.get("data") or {}).get("schedule") or {}).get("events") or []
                    return normalize_events(evs)
                return []

            with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
                for ms in ex.map(_fetch_league, target_ids):
                    all_matches.extend(ms)

        if all_matches:
            db.upsert_matches(all_matches, db_path=self.db_path)
            return all_matches
        return None if not isinstance(payload, dict) else []

    def cached_schedule(self) -> List[Dict[str, Any]]:
        return db.get_schedule(db_path=self.db_path)

    def fetch_live_matches(self) -> Optional[List[Dict[str, Any]]]:
        payload = net.fetch_json(C.RIOT_LIVE_URL, headers=self.headers)
        if not isinstance(payload, dict):
            return None
        events = ((payload.get("data") or {}).get("schedule") or {}).get("events") or []
        live = [m for m in normalize_events(events) if m["state"] == "inProgress"]
        if live:
            db.upsert_matches(live, db_path=self.db_path)
        return live

    def fetch_live_stats(self, game_id: str, team_codes: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """In-game scoreboard. The feed needs a startingTime ~2 minutes in the past,
        rounded down to 10 seconds; newer timestamps return HTTP 400."""
        for lag in (120, 180):
            t = int(time.time()) - lag
            t -= t % 10
            start = datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            url = C.RIOT_LIVESTATS_WINDOW_URL.format(game_id=game_id) + f"?startingTime={start}"
            window = net.fetch_json(url, max_retries=1)
            if isinstance(window, dict):
                return parse_livestats(window, team_codes)
        return None
