"""
RiftScout Local Database & Cache Engine
WAL-mode SQLite storage for API responses, matches, the team/roster/league
catalog, and the 24/7 stream schedule. Everything here is a cache: deleting
cache.db is always safe.
"""

import hashlib
import json
import logging
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from . import config as C

log = logging.getLogger(__name__)

_init_lock = threading.Lock()
_initialized: set = set()

SCHEMA_VERSION = 2  # bump to rebuild cache tables on upgrade

SCHEMA = """
CREATE TABLE IF NOT EXISTS api_cache (
    endpoint TEXT NOT NULL,
    query_hash TEXT PRIMARY KEY,
    response_json TEXT NOT NULL,
    created_at REAL NOT NULL,
    expires_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_api_cache_exp ON api_cache(expires_at);

CREATE TABLE IF NOT EXISTS matches (
    match_id TEXT PRIMARY KEY,
    league_name TEXT NOT NULL,
    league_slug TEXT NOT NULL,
    block_name TEXT,
    start_time_utc TEXT NOT NULL,
    state TEXT NOT NULL,
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
CREATE INDEX IF NOT EXISTS idx_matches_time ON matches(start_time_utc);
CREATE INDEX IF NOT EXISTS idx_matches_state ON matches(state);
CREATE INDEX IF NOT EXISTS idx_matches_league ON matches(league_slug);

CREATE TABLE IF NOT EXISTS leagues (
    slug TEXT PRIMARY KEY,
    league_id TEXT,
    name TEXT NOT NULL,
    region TEXT,
    image TEXT,
    priority INTEGER DEFAULT 999,
    updated_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS teams (
    slug TEXT PRIMARY KEY,
    team_id TEXT,
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    image TEXT,
    league_name TEXT,
    region TEXT,
    updated_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_teams_code ON teams(code);

CREATE TABLE IF NOT EXISTS team_rosters (
    team_slug TEXT NOT NULL,
    player_name TEXT NOT NULL,
    role TEXT,
    first_name TEXT,
    last_name TEXT,
    image TEXT,
    updated_at REAL NOT NULL,
    PRIMARY KEY (team_slug, player_name)
);
CREATE INDEX IF NOT EXISTS idx_rosters_player ON team_rosters(player_name COLLATE NOCASE);

CREATE TABLE IF NOT EXISTS stream_events (
    event_id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    name TEXT,
    event TEXT,
    season TEXT,
    stage TEXT,
    team1 TEXT,
    team2 TEXT,
    start_utc TEXT NOT NULL,
    is_banger INTEGER DEFAULT 0,
    updated_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_stream_time ON stream_events(start_utc);

CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""


def _path(db_path: Optional[Path]) -> Path:
    return Path(db_path) if db_path else C.CACHE_DB_PATH


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Open a connection (one per call, so it is safe from any thread)."""
    target = _path(db_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target), timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    key = str(target.resolve())
    if key not in _initialized:
        with _init_lock:
            if key not in _initialized:
                version = conn.execute("PRAGMA user_version").fetchone()[0]
                if version < SCHEMA_VERSION:
                    # Pre-0.2.0 caches used incompatible tables. It's all cache: rebuild.
                    for table in ("stream_schedule", "team_rosters", "teams", "leagues", "matches"):
                        conn.execute(f"DROP TABLE IF EXISTS {table}")
                conn.executescript(SCHEMA)
                conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
                conn.commit()
                _initialized.add(key)
    return conn


def init_db(db_path: Optional[Path] = None) -> None:
    get_connection(db_path).close()


def _rows(conn: sqlite3.Connection, sql: str, args: Iterable = ()) -> List[Dict[str, Any]]:
    return [dict(r) for r in conn.execute(sql, tuple(args)).fetchall()]


# ------------------------------------------------------------------ meta / cache
def get_meta(key: str, db_path: Optional[Path] = None) -> Optional[str]:
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else None
    finally:
        conn.close()


def set_meta(key: str, value: str, db_path: Optional[Path] = None) -> None:
    conn = get_connection(db_path)
    try:
        with conn:
            conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)", (key, value))
    finally:
        conn.close()


def _hash(endpoint: str, query_key: str) -> str:
    return hashlib.sha256(f"{endpoint}:{query_key}".encode("utf-8")).hexdigest()


def get_cached_api(endpoint: str, query_key: str, db_path: Optional[Path] = None) -> Optional[Any]:
    """Retrieve non-expired cached JSON data."""
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT response_json FROM api_cache WHERE query_hash = ? AND expires_at > ?",
            (_hash(endpoint, query_key), time.time()),
        ).fetchone()
        return json.loads(row["response_json"]) if row else None
    finally:
        conn.close()


def set_cached_api(endpoint: str, query_key: str, data: Any, ttl_sec: float = 300,
                   db_path: Optional[Path] = None) -> None:
    now = time.time()
    conn = get_connection(db_path)
    try:
        with conn:
            conn.execute(
                "INSERT OR REPLACE INTO api_cache VALUES (?, ?, ?, ?, ?)",
                (endpoint, _hash(endpoint, query_key), json.dumps(data), now, now + ttl_sec),
            )
            conn.execute("DELETE FROM api_cache WHERE expires_at < ?", (now - 86400,))
    finally:
        conn.close()


# ------------------------------------------------------------------ matches
MATCH_COLS = (
    "match_id", "league_name", "league_slug", "block_name", "start_time_utc", "state",
    "team1_name", "team1_code", "team1_image", "team1_score",
    "team2_name", "team2_code", "team2_image", "team2_score",
    "best_of", "winner", "stream_url",
)
_MATCH_DEFAULTS = {
    "league_name": "Unknown League", "league_slug": "unknown", "block_name": "",
    "start_time_utc": "", "state": "unstarted", "team1_name": "TBD", "team1_code": "TBD",
    "team1_image": "", "team1_score": 0, "team2_name": "TBD", "team2_code": "TBD",
    "team2_image": "", "team2_score": 0, "best_of": 1, "winner": "", "stream_url": "",
}


def upsert_matches(matches: List[Dict[str, Any]], db_path: Optional[Path] = None) -> int:
    now = time.time()
    placeholders = ", ".join("?" for _ in MATCH_COLS)
    sql = f"INSERT OR REPLACE INTO matches ({', '.join(MATCH_COLS)}, updated_at) VALUES ({placeholders}, ?)"
    conn = get_connection(db_path)
    try:
        with conn:
            for m in matches:
                vals = [str(m.get("match_id"))]
                vals += [m.get(c) if m.get(c) is not None else _MATCH_DEFAULTS[c] for c in MATCH_COLS[1:]]
                conn.execute(sql, (*vals, now))
            # Keep the cache bounded: drop matches older than 21 days.
            conn.execute(
                "DELETE FROM matches WHERE start_time_utc < strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-21 days')"
            )
        return len(matches)
    finally:
        conn.close()


def get_live_matches(db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    conn = get_connection(db_path)
    try:
        return _rows(conn, "SELECT * FROM matches WHERE state = 'inProgress' ORDER BY start_time_utc")
    finally:
        conn.close()


def get_schedule(limit: int = 200, league_slug: Optional[str] = None,
                 db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Cached matches in chronological order (recent results + upcoming)."""
    conn = get_connection(db_path)
    try:
        if league_slug:
            return _rows(conn, "SELECT * FROM matches WHERE league_slug = ? ORDER BY start_time_utc LIMIT ?",
                         (league_slug, limit))
        return _rows(conn, "SELECT * FROM matches ORDER BY start_time_utc LIMIT ?", (limit,))
    finally:
        conn.close()


# ------------------------------------------------------------------ catalog
def replace_catalog(leagues: List[Dict[str, Any]], teams: List[Dict[str, Any]],
                    rosters: List[Dict[str, Any]], db_path: Optional[Path] = None) -> None:
    """Atomically replace the league/team/roster catalog."""
    now = time.time()
    conn = get_connection(db_path)
    try:
        with conn:
            if leagues:
                conn.execute("DELETE FROM leagues")
                conn.executemany(
                    "INSERT OR REPLACE INTO leagues VALUES (?, ?, ?, ?, ?, ?, ?)",
                    [(l["slug"], l.get("league_id", ""), l["name"], l.get("region", ""),
                      l.get("image", ""), l.get("priority", 999), now) for l in leagues],
                )
            if teams:
                conn.execute("DELETE FROM teams")
                conn.execute("DELETE FROM team_rosters")
                conn.executemany(
                    "INSERT OR REPLACE INTO teams VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    [(t["slug"], t.get("team_id", ""), t["code"], t["name"], t.get("image", ""),
                      t.get("league_name", ""), t.get("region", ""), now) for t in teams],
                )
                conn.executemany(
                    "INSERT OR REPLACE INTO team_rosters VALUES (?, ?, ?, ?, ?, ?, ?)",
                    [(r["team_slug"], r["player_name"], r.get("role", ""), r.get("first_name", ""),
                      r.get("last_name", ""), r.get("image", ""), now) for r in rosters],
                )
    finally:
        conn.close()


def get_leagues(db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    conn = get_connection(db_path)
    try:
        return _rows(conn, "SELECT * FROM leagues ORDER BY priority, name")
    finally:
        conn.close()


def get_teams(db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    conn = get_connection(db_path)
    try:
        return _rows(conn, "SELECT * FROM teams ORDER BY name COLLATE NOCASE")
    finally:
        conn.close()


def get_rosters(db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    conn = get_connection(db_path)
    try:
        return _rows(conn, "SELECT * FROM team_rosters")
    finally:
        conn.close()


# ------------------------------------------------------------------ stream schedule
def replace_stream_events(events: List[Dict[str, Any]], db_path: Optional[Path] = None) -> int:
    now = time.time()
    conn = get_connection(db_path)
    try:
        with conn:
            conn.execute("DELETE FROM stream_events")
            conn.executemany(
                "INSERT OR REPLACE INTO stream_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [(e["event_id"], e["kind"], e.get("name", ""), e.get("event", ""), e.get("season", ""),
                  e.get("stage", ""), e.get("team1", ""), e.get("team2", ""), e["start_utc"],
                  1 if e.get("is_banger") else 0, now) for e in events],
            )
        return len(events)
    finally:
        conn.close()


def get_stream_events(db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    conn = get_connection(db_path)
    try:
        rows = _rows(conn, "SELECT * FROM stream_events ORDER BY start_utc")
        for r in rows:
            r["is_banger"] = bool(r["is_banger"])
        return rows
    finally:
        conn.close()
