"""
RiftScout 24/7 Twitch Rebroadcast Schedule
Reads the channel's published playout schedule (one entry per series, with a
wall-clock air time) and works out what is on now and what is coming up.
"""

import datetime
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import config as C
from . import db
from . import net
from .data import parse_iso_datetime, utcnow

log = logging.getLogger(__name__)

# If the last entry started longer ago than this, we no longer claim to know
# what is airing (the published schedule has probably run out).
MAX_AIRING_GAP = datetime.timedelta(hours=10)


def normalize_stream_events(raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for e in raw or []:
        if not isinstance(e, dict) or not e.get("utcIso") or not parse_iso_datetime(e["utcIso"]):
            continue
        out.append({
            "event_id": str(e.get("id") or e["utcIso"]),
            "kind": "match" if e.get("type") == "match" else "special",
            "name": e.get("name") or "",
            "event": e.get("event") or "",
            "season": e.get("season") or "",
            "stage": e.get("stage") or "",
            "team1": e.get("team1") or "",
            "team2": e.get("team2") or "",
            "start_utc": e["utcIso"],
            "is_banger": str(e.get("tag") or "").strip().lower() == "banger",
        })
    out.sort(key=lambda x: x["start_utc"])
    return out


def event_title(e: Dict[str, Any]) -> str:
    if e.get("kind") == "match":
        return f"{e.get('team1') or 'TBD'} vs {e.get('team2') or 'TBD'}"
    return e.get("name") or "Broadcast segment"


def event_subtitle(e: Dict[str, Any]) -> str:
    parts = [p for p in (e.get("event"), e.get("season"), e.get("stage")) if p]
    return " · ".join(parts)


def now_airing(events: List[Dict[str, Any]], now: Optional[datetime.datetime] = None) -> Optional[Dict[str, Any]]:
    """The most recent entry that has started, or None if off-air/unknown."""
    now = now or utcnow()
    current = None
    for e in events:
        start = parse_iso_datetime(e["start_utc"])
        if start and start <= now:
            current = e
        elif start and start > now:
            break
    if not current:
        return None
    if current["kind"] == "special" and current.get("name", "").lower() == "end":
        return None
    if now - parse_iso_datetime(current["start_utc"]) > MAX_AIRING_GAP:
        return None
    return current


def upcoming(events: List[Dict[str, Any]], now: Optional[datetime.datetime] = None,
             limit: int = 40, matches_only: bool = True) -> List[Dict[str, Any]]:
    now = now or utcnow()
    out = []
    for e in events:
        start = parse_iso_datetime(e["start_utc"])
        if start and start > now and (e["kind"] == "match" or not matches_only):
            out.append(e)
            if len(out) >= limit:
                break
    return out


def next_banger(events: List[Dict[str, Any]], now: Optional[datetime.datetime] = None) -> Optional[Dict[str, Any]]:
    for e in upcoming(events, now, limit=10_000):
        if e["is_banger"]:
            return e
    return None


class StreamScheduleReader:
    def __init__(self, url: str = C.STREAM_SCHEDULE_URL, db_path: Optional[Path] = None):
        self.url = url
        self.db_path = db_path

    def fetch(self) -> Optional[List[Dict[str, Any]]]:
        """Download the published schedule. Returns None when unreachable."""
        raw = net.fetch_json(self.url, timeout=20.0)
        if not isinstance(raw, list):
            return None
        events = normalize_stream_events(raw)
        if events:
            db.replace_stream_events(events, self.db_path)
        return events

    def cached(self) -> List[Dict[str, Any]]:
        return db.get_stream_events(self.db_path)


def is_stream_online(channel: str = C.TWITCH_CHANNEL) -> Optional[bool]:
    """Check if the 24/7 Twitch channel is currently broadcasting live.
    Returns True if live, False if offline, or None if the check could not be completed."""
    try:
        url = f"https://decapi.me/twitch/uptime/{channel}"
        txt = net.fetch_text(url, timeout=5.0)
        if not txt:
            return None
        t = txt.strip().lower()
        if "is offline" in t:
            return False
        if "error" in t or "not found" in t:
            return None
        return True
    except Exception:
        return None
