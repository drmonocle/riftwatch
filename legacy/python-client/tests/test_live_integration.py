"""Live checks against the real APIs. Skipped automatically when offline.
Run with:  py -3.12 -m pytest tests/test_live_integration.py -m live"""

import pytest

from riftscout import catalog, net
from riftscout import config as C
from riftscout.data import DataCoordinator
from riftscout.stream import StreamScheduleReader

pytestmark = pytest.mark.live


def _online():
    return net.fetch_bytes(C.RIOT_LEAGUES_URL, headers={"x-api-key": C.RIOT_API_KEY}, max_retries=1) is not None


@pytest.fixture(scope="module", autouse=True)
def require_network():
    if not _online():
        pytest.skip("Riot API unreachable")


def test_schedule(tmp_path):
    matches = DataCoordinator(db_path=tmp_path / "c.db").fetch_schedule()
    assert matches, "schedule returned no matches"
    assert all(m["team1_code"] and m["team2_code"] for m in matches)


def test_catalog(tmp_path):
    cat = catalog.refresh(tmp_path / "c.db")
    assert cat and len(cat.teams) > 100
    assert any(p.name.lower() == "faker" for p in cat.roster_for("T1", "T1"))


def test_stream_schedule(tmp_path):
    events = StreamScheduleReader(db_path=tmp_path / "c.db").fetch()
    assert events, "lolworlds schedule-json returned nothing"
    assert all(e["start_utc"] for e in events)
