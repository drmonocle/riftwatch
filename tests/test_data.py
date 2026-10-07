import datetime

from riftscout.data import (current_game, format_relative_time, normalize_event, normalize_events,
                            parse_iso_datetime, parse_livestats)

NOW = datetime.datetime(2026, 10, 7, 12, 0, tzinfo=datetime.timezone.utc)

EVENT = {
    "startTime": "2026-10-07T13:00:00Z", "state": "inProgress", "type": "match", "blockName": "Semifinals",
    "league": {"name": "Worlds", "slug": "worlds", "image": "http://static.lolesports.com/w.png"},
    "streams": [{"provider": "twitch", "parameter": "lck_kr", "locale": "ko-KR"},
                {"provider": "youtube", "parameter": "abc", "locale": "en-US"}],
    "match": {"id": "m1", "strategy": {"count": 5},
              "teams": [{"id": "10", "name": "T1", "code": "T1", "result": {"gameWins": 2, "outcome": None}},
                        {"id": "20", "name": "Gen.G", "code": "GEN", "result": {"gameWins": 1}}],
              "games": [{"number": 1, "id": "g1", "state": "completed",
                         "teams": [{"side": "blue", "id": "10"}, {"side": "red", "id": "20"}]},
                        {"number": 4, "id": "g4", "state": "inProgress",
                         "teams": [{"side": "blue", "id": "20"}, {"side": "red", "id": "10"}]}]},
}


def test_normalize_event():
    m = normalize_event(EVENT)
    assert m["match_id"] == "m1" and m["best_of"] == 5
    assert (m["team1_code"], m["team1_score"], m["team2_score"]) == ("T1", 2, 1)
    assert m["stream_url"] == "https://www.youtube.com/watch?v=abc"   # English preferred
    assert m["league_image"].startswith("https://")
    g = current_game(m)
    assert g["id"] == "g4" and g["blue_team_id"] == "20" and g["red_team_id"] == "10"


def test_missing_team_is_tbd_not_t1():
    ev = {"match": {"id": "x", "teams": [{}, {"name": "Gen.G", "code": "GEN"}]}}
    m = normalize_event(ev)
    assert m["team1_code"] == "TBD" and m["team1_name"] == "TBD"


def test_non_match_events_skipped():
    assert normalize_event({"type": "show", "match": {}}) is None
    assert normalize_events([{"type": "show"}, EVENT])[0]["match_id"] == "m1"


def test_relative_time():
    assert format_relative_time("2026-10-07T12:30:00Z", NOW) == "in 30m"
    assert format_relative_time("2026-10-07T14:05:00Z", NOW) == "in 2h 5m"
    assert format_relative_time("2026-10-09T13:00:00Z", NOW) == "in 2d 1h"
    assert format_relative_time("2026-10-07T11:59:30Z", NOW) == "just now"
    assert format_relative_time("2026-10-07T09:00:00Z", NOW) == "3h ago"
    assert format_relative_time("", NOW) == "TBD"
    assert parse_iso_datetime("garbage") is None


def test_parse_livestats_strips_team_prefix():
    window = {
        "gameMetadata": {
            "blueTeamMetadata": {"esportsTeamId": "10", "participantMetadata": [
                {"summonerName": "T1 Faker", "championId": "Azir", "role": "mid"}]},
            "redTeamMetadata": {"esportsTeamId": "20", "participantMetadata": [
                {"summonerName": "GEN Chovy", "championId": "Orianna", "role": "mid"}]}},
        "frames": [{"gameState": "in_game", "rfc460Timestamp": "t",
                    "blueTeam": {"totalGold": 50000, "totalKills": 12, "towers": 6, "dragons": ["ocean"]},
                    "redTeam": {"totalGold": 45000, "totalKills": 7}}],
    }
    st = parse_livestats(window, ["T1", "GEN"])
    assert st["blue"]["players"][0]["name"] == "Faker"
    assert st["red"]["players"][0]["name"] == "Chovy"
    assert st["blue"]["gold"] == 50000 and st["blue"]["dragons"] == ["ocean"]
    assert parse_livestats({"frames": []}) is None
