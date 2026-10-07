"""
Unit tests for RiftScout SQLite cache and relational match storage.
"""

import time
from pathlib import Path
from riftscout import db


def test_db_init_and_api_cache(tmp_path: Path):
    db_file = tmp_path / "test_cache.db"
    db.init_db(db_file)

    # Test cache insertion and retrieval
    endpoint = "https://esports-api.lolesports.com/test"
    data = {"events": [{"id": "1", "state": "completed"}]}
    db.set_cached_api(endpoint, "q1", data, ttl_sec=60, db_path=db_file)

    cached = db.get_cached_api(endpoint, "q1", db_path=db_file)
    assert cached == data

    # Test expired cache returns None
    db.set_cached_api(endpoint, "q_expired", data, ttl_sec=-10, db_path=db_file)
    assert db.get_cached_api(endpoint, "q_expired", db_path=db_file) is None


def test_match_upserts_and_queries(tmp_path: Path):
    db_file = tmp_path / "test_matches.db"
    db.init_db(db_file)

    matches = [
        {
            "match_id": "1001",
            "league_name": "LCK",
            "league_slug": "lck",
            "block_name": "Finals",
            "start_time_utc": "2026-10-07T08:00:00Z",
            "state": "inProgress",
            "team1_name": "T1",
            "team1_code": "T1",
            "team1_score": 1,
            "team2_name": "Gen.G",
            "team2_code": "GEN",
            "team2_score": 1,
            "best_of": 5,
        },
        {
            "match_id": "1002",
            "league_name": "LEC",
            "league_slug": "lec",
            "block_name": "Week 1",
            "start_time_utc": "2026-10-08T16:00:00Z",
            "state": "unstarted",
            "team1_name": "G2 Esports",
            "team1_code": "G2",
            "team1_score": 0,
            "team2_name": "Fnatic",
            "team2_code": "FNC",
            "team2_score": 0,
            "best_of": 3,
        }
    ]

    inserted = db.upsert_matches(matches, db_path=db_file)
    assert inserted == 2

    # Query live matches
    live = db.get_live_matches(db_path=db_file)
    assert len(live) == 1
    assert live[0]["match_id"] == "1001"
    assert live[0]["team1_code"] == "T1"

    # Query schedule
    sched = db.get_schedule(limit=10, db_path=db_file)
    assert len(sched) == 2


def test_stream_schedule_and_bangers(tmp_path: Path):
    db_file = tmp_path / "test_stream.db"
    db.init_db(db_file)

    series_data = [
        {
            "series_num": 1,
            "tournament_slug": "worlds_2022",
            "tournament_name": "2022 World Championship",
            "title": "T1 vs DRX (Grand Finals)",
            "stage": "Finals",
            "team_1": "T1",
            "team_2": "DRX",
            "score": "2-3",
            "winner": "DRX",
            "is_banger": 1,
            "banger_tier": "S-Tier Banger"
        },
        {
            "series_num": 2,
            "tournament_slug": "msi_2023",
            "tournament_name": "2023 MSI",
            "title": "JDG vs BLG",
            "stage": "Finals",
            "team_1": "JDG",
            "team_2": "BLG",
            "score": "3-1",
            "winner": "JDG",
            "is_banger": 0,
            "banger_tier": ""
        }
    ]

    db.upsert_stream_schedule(series_data, db_path=db_file)
    bangers = db.get_stream_bangers(db_path=db_file)
    assert len(bangers) == 1
    assert bangers[0]["title"] == "T1 vs DRX (Grand Finals)"
    assert bangers[0]["banger_tier"] == "S-Tier Banger"
