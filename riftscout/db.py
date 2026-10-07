"""
RiftScout Local Database & Cache Engine
Provides WAL-mode SQLite storage for API responses, matches, rosters, and Twitch stream schedules.
"""

import hashlib
import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import config as C

log = logging.getLogger(__name__)


def get_connection(db_path: Optional[Path] = None, auto_init: bool = True) -> sqlite3.Connection:
    """Establish a thread-safe connection to the SQLite cache."""
    target_path = db_path or C.CACHE_DB_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target_path), timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    if auto_init:
        init_db(target_path, conn=conn)
    return conn


def init_db(db_path: Optional[Path] = None, conn: Optional[sqlite3.Connection] = None) -> None:
    """Initialize database tables and performance indices."""
    close_when_done = False
    if conn is None:
        conn = get_connection(db_path, auto_init=False)
        close_when_done = True

    with conn:
        # 1. Raw API Response Cache (with TTL expiration)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS api_cache (
                endpoint TEXT NOT NULL,
                query_hash TEXT PRIMARY KEY,
                response_json TEXT NOT NULL,
                created_at REAL NOT NULL,
                expires_at REAL NOT NULL
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_api_cache_exp ON api_cache(expires_at);")

        # 2. Normalized Pro Matches
        conn.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                match_id TEXT PRIMARY KEY,
                league_name TEXT NOT NULL,
                league_slug TEXT NOT NULL,
                block_name TEXT,
                start_time_utc TEXT NOT NULL,
                state TEXT NOT NULL,          -- unstarted, inProgress, completed
                team1_name TEXT NOT NULL,
                team1_code TEXT NOT NULL,
                team1_image TEXT,
                team1_score INTEGER DEFAULT 0,
                team2_name TEXT NOT NULL,
                team2_code TEXT NOT NULL,
                team2_image TEXT,
                team2_score INTEGER DEFAULT 0,
                best_of INTEGER DEFAULT 1,
                winner TEXT,
                stream_url TEXT,
                updated_at REAL NOT NULL
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_matches_time ON matches(start_time_utc);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_matches_state ON matches(state);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_matches_league ON matches(league_slug);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_matches_teams ON matches(team1_code, team2_code);")

        # 3. Team Rosters & Players
        conn.execute("""
            CREATE TABLE IF NOT EXISTS team_rosters (
                team_code TEXT NOT NULL,
                player_name TEXT NOT NULL,
                role TEXT,                    -- Top, Jungle, Mid, Bot, Support
                is_starter BOOLEAN DEFAULT 1,
                updated_at REAL NOT NULL,
                PRIMARY KEY (team_code, player_name)
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_rosters_player ON team_rosters(player_name);")

        # 4. 24/7 Twitch Broadcast Stream Schedule
        conn.execute("""
            CREATE TABLE IF NOT EXISTS stream_schedule (
                series_num INTEGER PRIMARY KEY,
                tournament_slug TEXT,
                tournament_name TEXT,
                title TEXT NOT NULL,
                stage TEXT,
                team_1 TEXT,
                team_2 TEXT,
                score TEXT,
                winner TEXT,
                is_banger BOOLEAN DEFAULT 0,
                banger_tier TEXT,
                updated_at REAL NOT NULL
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_stream_banger ON stream_schedule(is_banger);")
    if close_when_done:
        conn.close()


def get_cached_api(endpoint: str, query_key: str, db_path: Optional[Path] = None) -> Optional[Any]:
    """Retrieve non-expired cached JSON data."""
    query_hash = hashlib.sha256(f"{endpoint}:{query_key}".encode("utf-8")).hexdigest()
    now = time.time()
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT response_json FROM api_cache WHERE query_hash = ? AND expires_at > ?",
            (query_hash, now)
        )
        row = cur.fetchone()
        if row:
            return json.loads(row["response_json"])
        return None
    finally:
        conn.close()


def set_cached_api(
    endpoint: str,
    query_key: str,
    data: Any,
    ttl_sec: float = 300,
    db_path: Optional[Path] = None
) -> None:
    """Save response data to cache with TTL."""
    query_hash = hashlib.sha256(f"{endpoint}:{query_key}".encode("utf-8")).hexdigest()
    now = time.time()
    expires_at = now + ttl_sec
    json_str = json.dumps(data)
    conn = get_connection(db_path)
    try:
        with conn:
            conn.execute("""
                INSERT OR REPLACE INTO api_cache (endpoint, query_hash, response_json, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?)
            """, (endpoint, query_hash, json_str, now, expires_at))
    finally:
        conn.close()


def upsert_matches(matches: List[Dict[str, Any]], db_path: Optional[Path] = None) -> int:
    """Batch upsert normalized pro matches into the database."""
    now = time.time()
    conn = get_connection(db_path)
    count = 0
    try:
        with conn:
            for m in matches:
                conn.execute("""
                    INSERT OR REPLACE INTO matches (
                        match_id, league_name, league_slug, block_name,
                        start_time_utc, state, team1_name, team1_code, team1_image, team1_score,
                        team2_name, team2_code, team2_image, team2_score,
                        best_of, winner, stream_url, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(m.get("match_id")),
                    m.get("league_name", "Unknown League"),
                    m.get("league_slug", "unknown"),
                    m.get("block_name", ""),
                    m.get("start_time_utc", ""),
                    m.get("state", "unstarted"),
                    m.get("team1_name", "TBD"),
                    m.get("team1_code", "TBD"),
                    m.get("team1_image", ""),
                    m.get("team1_score", 0),
                    m.get("team2_name", "TBD"),
                    m.get("team2_code", "TBD"),
                    m.get("team2_image", ""),
                    m.get("team2_score", 0),
                    m.get("best_of", 1),
                    m.get("winner", ""),
                    m.get("stream_url", ""),
                    now
                ))
                count += 1
    finally:
        conn.close()
    return count


def get_live_matches(db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Fetch currently active live pro matches."""
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM matches WHERE state = 'inProgress' ORDER BY start_time_utc ASC")
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def get_schedule(
    limit: int = 50,
    league_slug: Optional[str] = None,
    db_path: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """Fetch upcoming and recent matches, sorted chronologically."""
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        if league_slug:
            cur.execute("""
                SELECT * FROM matches
                WHERE league_slug = ?
                ORDER BY start_time_utc ASC LIMIT ?
            """, (league_slug, limit))
        else:
            cur.execute("""
                SELECT * FROM matches
                ORDER BY start_time_utc ASC LIMIT ?
            """, (limit,))
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def upsert_stream_schedule(series_list: List[Dict[str, Any]], db_path: Optional[Path] = None) -> int:
    """Store 24/7 Twitch broadcast schedule items."""
    now = time.time()
    conn = get_connection(db_path)
    count = 0
    try:
        with conn:
            for s in series_list:
                conn.execute("""
                    INSERT OR REPLACE INTO stream_schedule (
                        series_num, tournament_slug, tournament_name, title, stage,
                        team_1, team_2, score, winner, is_banger, banger_tier, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    s.get("series_num", 0),
                    s.get("tournament_slug", ""),
                    s.get("tournament_name", ""),
                    s.get("title", ""),
                    s.get("stage", ""),
                    s.get("team_1", ""),
                    s.get("team_2", ""),
                    s.get("score", ""),
                    s.get("winner", ""),
                    1 if s.get("is_banger") else 0,
                    s.get("banger_tier", ""),
                    now
                ))
                count += 1
    finally:
        conn.close()
    return count


def get_stream_bangers(db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Retrieve all identified S-Tier Bangers from the stream schedule."""
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM stream_schedule WHERE is_banger = 1 ORDER BY series_num ASC")
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()
