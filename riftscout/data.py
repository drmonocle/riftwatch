"""
RiftScout Hybrid Data Coordinator
Fetches, normalizes, and reconciles pro match data from Riot's LoL Esports API
and community roster sources with local caching.
"""

import datetime
import logging
from typing import Any, Dict, List, Optional

from . import config as C
from . import db
from . import net

log = logging.getLogger(__name__)


def parse_iso_datetime(dt_str: str) -> Optional[datetime.datetime]:
    """Parse ISO-8601 UTC timestamp string to datetime."""
    if not dt_str:
        return None
    try:
        clean = dt_str.replace("Z", "+00:00")
        return datetime.datetime.fromisoformat(clean)
    except Exception:
        return None


def format_relative_time(dt_str: str) -> str:
    """Format an ISO UTC time into a human-readable relative string."""
    dt = parse_iso_datetime(dt_str)
    if not dt:
        return "TBD"

    now = datetime.datetime.now(datetime.timezone.utc)
    delta = dt - now
    total_seconds = int(delta.total_seconds())

    # Live or past
    if total_seconds <= 0:
        past_secs = abs(total_seconds)
        if past_secs < 3600:
            return f"{past_secs // 60}m ago"
        elif past_secs < 86400:
            return f"{past_secs // 3600}h ago"
        else:
            return f"{past_secs // 86400}d ago"

    # Future / Upcoming
    if total_seconds < 3600:
        return f"in {total_seconds // 60}m"
    elif total_seconds < 86400:
        hours = total_seconds // 3600
        mins = (total_seconds % 3600) // 60
        return f"in {hours}h {mins}m"
    else:
        days = total_seconds // 86400
        return f"in {days}d"


def format_local_match_time(dt_str: str) -> str:
    """Format ISO UTC timestamp to local system time format (e.g. 'Oct 07, 7:00 AM')."""
    dt = parse_iso_datetime(dt_str)
    if not dt:
        return "Time TBD"
    local_dt = dt.astimezone()  # converts to system local timezone
    return local_dt.strftime("%b %d, %I:%M %p")


class DataCoordinator:
    """High-level esports data orchestrator with automatic caching."""

    def __init__(self, api_key: str = C.RIOT_API_KEY):
        self.api_key = api_key
        self.headers = {
            "x-api-key": self.api_key,
            "Accept": "application/json",
        }

    def fetch_schedule(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Fetch pro match schedule from Riot API with caching and normalization.
        """
        cache_key = "global_schedule_v1"
        if not force_refresh:
            cached = db.get_cached_api(C.RIOT_SCHEDULE_URL, cache_key)
            if cached and isinstance(cached, list):
                return cached

        payload = net.fetch_json(
            C.RIOT_SCHEDULE_URL,
            headers=self.headers,
            timeout=C.HTTP_TIMEOUT_DEFAULT
        )

        if not payload or not isinstance(payload, dict):
            log.warning("Could not fetch schedule from Riot API. Falling back to local DB.")
            return db.get_schedule(limit=60)

        events = payload.get("data", {}).get("schedule", {}).get("events", [])
        normalized = []

        for event in events:
            match = event.get("match") or {}
            teams = match.get("teams") or []
            if len(teams) < 2:
                continue

            t1 = teams[0] or {}
            t2 = teams[1] or {}

            t1_res = t1.get("result") or {}
            t2_res = t2.get("result") or {}

            league = event.get("league") or {}
            strategy = match.get("strategy") or {}

            # Determine winner
            winner = ""
            if t1_res.get("outcome") == "win":
                winner = t1.get("code") or t1.get("name") or "Team 1"
            elif t2_res.get("outcome") == "win":
                winner = t2.get("code") or t2.get("name") or "Team 2"

            match_data = {
                "match_id": match.get("id") or event.get("id"),
                "league_name": league.get("name", "Unknown League"),
                "league_slug": league.get("slug", "unknown"),
                "block_name": event.get("blockName", ""),
                "start_time_utc": event.get("startTime", ""),
                "state": event.get("state", "unstarted"),
                "team1_name": t1.get("name", "TBD"),
                "team1_code": t1.get("code", "T1"),
                "team1_image": t1.get("image", ""),
                "team1_score": t1_res.get("gameWins", 0),
                "team2_name": t2.get("name", "TBD"),
                "team2_code": t2.get("code", "T2"),
                "team2_image": t2.get("image", ""),
                "team2_score": t2_res.get("gameWins", 0),
                "best_of": strategy.get("count", 1),
                "winner": winner,
                "stream_url": "",
            }
            normalized.append(match_data)

        if normalized:
            db.upsert_matches(normalized)
            db.set_cached_api(C.RIOT_SCHEDULE_URL, cache_key, normalized, ttl_sec=300)
            log.info("Successfully ingested %d pro matches into local database.", len(normalized))

        return normalized

    def fetch_live_matches(self) -> List[Dict[str, Any]]:
        """
        Fetch currently active live pro matches from Riot getLive endpoint.
        """
        payload = net.fetch_json(
            C.RIOT_LIVE_URL,
            headers=self.headers,
            timeout=C.HTTP_TIMEOUT_DEFAULT
        )

        if not payload or not isinstance(payload, dict):
            # Fall back to local database
            return db.get_live_matches()

        events = payload.get("data", {}).get("schedule", {}).get("events", [])
        live_list = []

        for event in events:
            if event.get("state") != "inProgress":
                continue

            match = event.get("match") or {}
            teams = match.get("teams") or []
            if len(teams) < 2:
                continue

            t1 = teams[0] or {}
            t2 = teams[1] or {}
            league = event.get("league") or {}
            strategy = match.get("strategy") or {}
            streams = event.get("streams") or []
            stream_url = ""
            if streams:
                first_stream = streams[0]
                param = first_stream.get("parameter", "")
                provider = first_stream.get("provider", "")
                if provider == "twitch":
                    stream_url = f"https://twitch.tv/{param}"
                elif provider == "youtube":
                    stream_url = f"https://youtube.com/watch?v={param}"

            live_match = {
                "match_id": match.get("id") or event.get("id"),
                "league_name": league.get("name", "Pro League"),
                "league_slug": league.get("slug", "unknown"),
                "block_name": event.get("blockName", ""),
                "start_time_utc": event.get("startTime", ""),
                "state": "inProgress",
                "team1_name": t1.get("name", "TBD"),
                "team1_code": t1.get("code", "T1"),
                "team1_image": t1.get("image", ""),
                "team1_score": (t1.get("result") or {}).get("gameWins", 0),
                "team2_name": t2.get("name", "TBD"),
                "team2_code": t2.get("code", "T2"),
                "team2_image": t2.get("image", ""),
                "team2_score": (t2.get("result") or {}).get("gameWins", 0),
                "best_of": strategy.get("count", 1),
                "winner": "",
                "stream_url": stream_url,
            }
            live_list.append(live_match)

        if live_list:
            db.upsert_matches(live_list)

        return live_list
