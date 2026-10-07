"""
Unit tests for Twitch stream reader and banger filtering.
"""

import json
from pathlib import Path
from riftscout.stream import StreamScheduleReader


def test_stream_reader_from_json(tmp_path: Path):
    fake_json = tmp_path / "schedule_master.json"
    payload = {
        "tournaments": [
            {"id": 1, "slug": "worlds_2022", "name": "2022 Worlds"}
        ],
        "series": [
            {
                "series_num": 10,
                "tournament_id": 1,
                "title": "T1 vs DRX",
                "stage": "Grand Finals",
                "team_1": "T1",
                "team_2": "DRX",
                "score": "2-3",
                "winner": "DRX",
                "is_banger": True,
                "banger_tier": "S-Tier Banger"
            }
        ]
    }
    with open(fake_json, "w", encoding="utf-8") as f:
        json.dump(payload, f)

    reader = StreamScheduleReader(
        local_db_path=tmp_path / "nonexistent.db",
        local_json_path=fake_json,
        remote_url="http://invalid.local",
        cache_db_path=tmp_path / "cache.db"
    )

    items = reader.fetch_stream_schedule()
    assert len(items) == 1
    assert items[0]["title"] == "T1 vs DRX"
    assert items[0]["is_banger"] == 1
    assert items[0]["banger_tier"] == "S-Tier Banger"
