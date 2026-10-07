import pytest

from riftscout import db


@pytest.fixture
def dbp(tmp_path):
    p = tmp_path / "cache.db"
    db.init_db(p)
    return p


def _match(mid, start, state="unstarted", **kw):
    m = {"match_id": mid, "league_name": "LCK", "league_slug": "lck", "start_time_utc": start,
         "state": state, "team1_name": "T1", "team1_code": "T1", "team2_name": "Gen.G", "team2_code": "GEN"}
    m.update(kw)
    return m


def test_upsert_and_query_matches(dbp):
    db.upsert_matches([_match("1", "2099-01-01T10:00:00Z"),
                       _match("2", "2099-01-01T08:00:00Z", state="inProgress", team1_score=1)], dbp)
    sched = db.get_schedule(db_path=dbp)
    assert [m["match_id"] for m in sched] == ["2", "1"]
    live = db.get_live_matches(dbp)
    assert len(live) == 1 and live[0]["team1_score"] == 1


def test_old_matches_pruned(dbp):
    db.upsert_matches([_match("old", "2000-01-01T00:00:00Z"), _match("new", "2099-01-01T00:00:00Z")], dbp)
    assert [m["match_id"] for m in db.get_schedule(db_path=dbp)] == ["new"]


def test_none_values_get_defaults(dbp):
    db.upsert_matches([_match("1", "2099-01-01T00:00:00Z", winner=None, stream_url=None)], dbp)
    m = db.get_schedule(db_path=dbp)[0]
    assert m["winner"] == "" and m["stream_url"] == ""


def test_schedule_window_returns_recent_and_future_matches(dbp):
    import datetime
    now = datetime.datetime.now(datetime.timezone.utc)
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    m_ancient = _match("ancient", (now - datetime.timedelta(days=45)).strftime(fmt))
    m_recent = _match("recent", (now - datetime.timedelta(days=5)).strftime(fmt), state="completed")
    m_today = _match("today", now.strftime(fmt), state="inProgress")
    m_future = _match("future", (now + datetime.timedelta(days=10)).strftime(fmt), state="unstarted")

    db.upsert_matches([m_ancient, m_recent, m_today, m_future], dbp)
    sched = db.get_schedule(since_days=30, db_path=dbp)
    ids = [m["match_id"] for m in sched]
    assert "ancient" not in ids, "Ancient matches older than 30 days should be excluded from active schedule"
    assert "recent" in ids, "Recent results within 30 days should be included"
    assert "today" in ids, "Today's matches must be included"
    assert "future" in ids, "Future matches must be included"


def test_catalog_roundtrip_and_replace(dbp):
    leagues = [{"slug": "lck", "name": "LCK", "priority": 1}]
    teams = [{"slug": "t1", "code": "T1", "name": "T1", "league_name": "LCK"}]
    rosters = [{"team_slug": "t1", "player_name": "Faker", "role": "mid"}]
    db.replace_catalog(leagues, teams, rosters, dbp)
    assert db.get_leagues(dbp)[0]["slug"] == "lck"
    assert db.get_rosters(dbp)[0]["player_name"] == "Faker"
    # Replacing with an empty team list keeps the old teams (failed fetch must not wipe cache).
    db.replace_catalog([], [], [], dbp)
    assert len(db.get_teams(dbp)) == 1


def test_stream_events_roundtrip(dbp):
    ev = [{"event_id": "a", "kind": "match", "team1": "SKT", "team2": "SSG",
           "start_utc": "2026-10-07T07:00:00Z", "is_banger": True}]
    db.replace_stream_events(ev, dbp)
    got = db.get_stream_events(dbp)
    assert got[0]["is_banger"] is True and got[0]["team1"] == "SKT"


def test_meta_and_api_cache(dbp):
    assert db.get_meta("x", dbp) is None
    db.set_meta("x", "1", dbp)
    assert db.get_meta("x", dbp) == "1"
    db.set_cached_api("ep", "q", {"a": 1}, ttl_sec=60, db_path=dbp)
    assert db.get_cached_api("ep", "q", dbp) == {"a": 1}
    db.set_cached_api("ep", "gone", {"a": 1}, ttl_sec=-1, db_path=dbp)
    assert db.get_cached_api("ep", "gone", dbp) is None


def test_legacy_v010_cache_is_rebuilt(tmp_path):
    import sqlite3
    p = tmp_path / "legacy.db"
    c = sqlite3.connect(p)
    c.execute("CREATE TABLE team_rosters (team_code TEXT, player_name TEXT, role TEXT, is_starter BOOLEAN,"
              " updated_at REAL, PRIMARY KEY (team_code, player_name))")
    c.execute("CREATE TABLE stream_schedule (series_num INTEGER PRIMARY KEY, title TEXT)")
    c.commit()
    c.close()
    db.replace_catalog([], [{"slug": "t1", "code": "T1", "name": "T1"}],
                       [{"team_slug": "t1", "player_name": "Faker"}], p)
    assert db.get_rosters(p)[0]["team_slug"] == "t1"
    names = {r[0] for r in sqlite3.connect(p).execute("select name from sqlite_master where type='table'")}
    assert "stream_schedule" not in names
