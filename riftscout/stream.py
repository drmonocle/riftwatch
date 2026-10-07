"""
RiftScout Twitch Stream Schedule Synchronizer
Reads tournament schedules, S-Tier Bangers, and playout data from lol_broadcast_schedule.db.
"""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import config as C
from . import db
from . import net

log = logging.getLogger(__name__)


class StreamScheduleReader:
    """Reads 24/7 Twitch stream marathon schedule with multi-tiered fallback."""

    def __init__(
        self,
        local_db_path: Path = C.LOCAL_TWITCH_DB_PATH,
        local_json_path: Path = C.LOCAL_TWITCH_JSON_PATH,
        remote_url: str = C.REMOTE_TWITCH_SCHEDULE_URL,
        cache_db_path: Optional[Path] = None,
    ):
        self.local_db_path = local_db_path
        self.local_json_path = local_json_path
        self.remote_url = remote_url
        self.cache_db_path = cache_db_path

    def fetch_stream_schedule(self) -> List[Dict[str, Any]]:
        """
        Fetch stream series schedule trying local SQLite DB first, then local JSON,
        then lolworlds.com remote API.
        """
        # Tier 1: Local SQLite Broadcast Database (Fastest on Home Server / Node 1)
        if self.local_db_path.exists():
            try:
                items = self._fetch_from_sqlite(self.local_db_path)
                if items:
                    self._save_to_cache(items)
                    return items
            except Exception as exc:
                log.warning("Failed querying local broadcast DB %s: %s", self.local_db_path, exc)

        # Tier 2: Local Master JSON
        if self.local_json_path.exists():
            try:
                items = self._fetch_from_json_file(self.local_json_path)
                if items:
                    self._save_to_cache(items)
                    return items
            except Exception as exc:
                log.warning("Failed reading local master JSON %s: %s", self.local_json_path, exc)

        # Tier 3: Remote lolworlds.com endpoint
        try:
            items = self._fetch_from_remote_api(self.remote_url)
            if items:
                self._save_to_cache(items)
                return items
        except Exception as exc:
            log.warning("Failed fetching stream schedule from remote API: %s", exc)

        # Fallback to local SQLite cache
        try:
            return db.get_stream_bangers(db_path=self.cache_db_path)
        except Exception:
            return []

    def _save_to_cache(self, items: List[Dict[str, Any]]) -> None:
        try:
            db.init_db(self.cache_db_path)
            db.upsert_stream_schedule(items, db_path=self.cache_db_path)
        except Exception as exc:
            log.warning("Failed saving stream schedule to cache: %s", exc)

    def _fetch_from_sqlite(self, db_path: Path) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(str(db_path), timeout=5.0)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                s.series_num,
                t.slug AS tournament_slug,
                t.name AS tournament_name,
                s.title,
                s.stage,
                s.team_1,
                s.team_2,
                s.score,
                s.winner,
                s.is_banger,
                s.banger_tier
            FROM series s
            JOIN tournaments t ON s.tournament_id = t.id
            ORDER BY s.series_num ASC
        """)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    def _fetch_from_json_file(self, json_path: Path) -> List[Dict[str, Any]]:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        series_raw = data.get("series", [])
        tournaments = {t.get("id"): t for t in data.get("tournaments", [])}
        
        items = []
        for s in series_raw:
            tid = s.get("tournament_id")
            t_info = tournaments.get(tid, {})
            items.append({
                "series_num": s.get("series_num", 0),
                "tournament_slug": t_info.get("slug", ""),
                "tournament_name": t_info.get("name", ""),
                "title": s.get("title", ""),
                "stage": s.get("stage", ""),
                "team_1": s.get("team_1", ""),
                "team_2": s.get("team_2", ""),
                "score": s.get("score", ""),
                "winner": s.get("winner", ""),
                "is_banger": 1 if s.get("is_banger") else 0,
                "banger_tier": s.get("banger_tier", ""),
            })
        return items

    def _fetch_from_remote_api(self, url: str) -> List[Dict[str, Any]]:
        payload = net.fetch_json(url)
        if not payload or not isinstance(payload, dict):
            return []
        series_raw = payload.get("series", [])
        tournaments = {t.get("id"): t for t in payload.get("tournaments", [])}

        items = []
        for s in series_raw:
            tid = s.get("tournament_id")
            t_info = tournaments.get(tid, {})
            items.append({
                "series_num": s.get("series_num", 0),
                "tournament_slug": t_info.get("slug", ""),
                "tournament_name": t_info.get("name", ""),
                "title": s.get("title", ""),
                "stage": s.get("stage", ""),
                "team_1": s.get("team_1", ""),
                "team_2": s.get("team_2", ""),
                "score": s.get("score", ""),
                "winner": s.get("winner", ""),
                "is_banger": 1 if s.get("is_banger") else 0,
                "banger_tier": s.get("banger_tier", ""),
            })
        return items
