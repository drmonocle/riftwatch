import datetime

from riftscout.stream import (StreamScheduleReader, event_subtitle, event_title, next_banger,
                              normalize_stream_events, now_airing, upcoming)

UTC = datetime.timezone.utc
RAW = [
    {"id": 3, "utcIso": "2026-10-07T09:00:00Z", "type": "match", "team1": "T1", "team2": "WBG",
     "event": "Worlds", "season": "S13", "stage": "Finals", "tag": "Banger"},
    {"id": 1, "utcIso": "2026-10-07T07:00:00Z", "type": "match", "team1": "BLG", "team2": "WBG",
     "event": "Worlds", "season": "S13", "stage": "Semifinals"},
    {"id": 2, "utcIso": "2026-10-07T08:00:00Z", "type": "special", "name": "Opening Ceremony"},
    {"id": 4, "utcIso": "2026-10-07T11:00:00Z", "type": "special", "name": "End"},
    {"id": 5, "utcIso": "not a date"},
    "junk",
]


def at(h, m=0):
    return datetime.datetime(2026, 10, 7, h, m, tzinfo=UTC)


def test_normalize_sorts_and_filters():
    ev = normalize_stream_events(RAW)
    assert [e["event_id"] for e in ev] == ["1", "2", "3", "4"]
    assert ev[2]["is_banger"] and not ev[0]["is_banger"]
    assert event_title(ev[0]) == "BLG vs WBG" and event_title(ev[1]) == "Opening Ceremony"
    assert event_subtitle(ev[0]) == "Worlds · S13 · Semifinals"


def test_now_airing():
    ev = normalize_stream_events(RAW)
    assert now_airing(ev, at(6)) is None
    assert now_airing(ev, at(7, 30))["event_id"] == "1"
    assert now_airing(ev, at(8, 15))["event_id"] == "2"
    assert now_airing(ev, at(12)) is None             # after "End"


def test_stale_schedule_not_claimed_as_airing():
    ev = normalize_stream_events(RAW[:1])
    assert now_airing(ev, at(9) + datetime.timedelta(hours=11)) is None


def test_upcoming_and_banger():
    ev = normalize_stream_events(RAW)
    assert [e["event_id"] for e in upcoming(ev, at(7, 30))] == ["3"]
    assert [e["event_id"] for e in upcoming(ev, at(7, 30), matches_only=False)] == ["2", "3", "4"]
    assert next_banger(ev, at(7, 30))["event_id"] == "3"
    assert next_banger(ev, at(10)) is None


def test_reader_caches(tmp_path, monkeypatch):
    from riftscout import net
    monkeypatch.setattr(net, "fetch_json", lambda *a, **k: RAW)
    r = StreamScheduleReader("https://lolworlds.com/x", tmp_path / "c.db")
    assert len(r.fetch()) == 4
    monkeypatch.setattr(net, "fetch_json", lambda *a, **k: None)
    assert r.fetch() is None                          # offline -> None, cache untouched
    assert len(r.cached()) == 4
