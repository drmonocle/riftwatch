"""
Integration tests verifying live data fetching and local Twitch broadcast ingestion.
"""

from pathlib import Path
from riftscout import config as C
from riftscout.data import DataCoordinator
from riftscout.stream import StreamScheduleReader


def test_riot_schedule_live_fetch():
    """Verify live connection to Riot LoL Esports persisted API."""
    coordinator = DataCoordinator()
    matches = coordinator.fetch_schedule(force_refresh=True)

    # Should fetch active or upcoming pro events
    assert isinstance(matches, list)
    assert len(matches) > 0

    first = matches[0]
    assert "match_id" in first
    assert "team1_name" in first
    assert "team2_name" in first
    assert "start_time_utc" in first


def test_local_broadcast_db_ingestion():
    """Verify ingestion of the actual 24/7 Twitch broadcast database."""
    if not C.LOCAL_TWITCH_DB_PATH.exists():
        return

    reader = StreamScheduleReader(local_db_path=C.LOCAL_TWITCH_DB_PATH)
    items = reader.fetch_stream_schedule()

    assert len(items) > 100
    bangers = [i for i in items if i.get("is_banger")]
    assert len(bangers) > 0
