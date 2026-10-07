import pytest

from riftscout import catalog
from riftscout.catalog import Catalog, parse_leagues, parse_teams
from riftscout.settings import SettingsManager
from riftscout.watchlist import Watchlist

TEAMS_PAYLOAD = {"data": {"teams": [
    {"slug": "t1", "id": "1", "code": "T1", "name": "T1", "status": "active",
     "image": "http://static.lolesports.com/t1.png", "homeLeague": {"name": "LCK", "region": "KOREA"},
     "players": [{"summonerName": "Faker", "role": "mid", "firstName": "Sanghyeok", "lastName": "Lee"},
                 {"summonerName": "Oner", "role": "jungle"},
                 {"summonerName": "faker", "role": "mid"}]},
    {"slug": "hanwha-life-esports", "code": "HLE", "name": "Hanwha Life Esports", "status": "active",
     "homeLeague": {"name": "LCK"}, "players": [{"summonerName": "Zeka", "role": "mid"}]},
    {"slug": "hle-challengers", "code": "HLE", "name": "HLE Challengers", "status": "active",
     "homeLeague": {"name": "LCK Challengers"}, "players": [{"summonerName": "Rookie2", "role": "mid"}]},
    {"slug": "retired", "code": "OLD", "name": "Old Team", "status": "archived",
     "homeLeague": {"name": "LCK"}, "players": [{"summonerName": "Ghost"}]},
    {"slug": "no-players", "code": "NP", "name": "Empty", "status": "active", "homeLeague": {"name": "LCK"},
     "players": []},
]}}


@pytest.fixture
def cat():
    teams, rosters = parse_teams(TEAMS_PAYLOAD)
    return catalog._build([{"slug": "lck", "name": "LCK"}], teams, rosters)


def test_parse_teams_filters_and_dedupes():
    teams, rosters = parse_teams(TEAMS_PAYLOAD)
    assert [t["slug"] for t in teams] == ["t1", "hanwha-life-esports", "hle-challengers"]
    assert teams[0]["image"].startswith("https://")
    assert [r["player_name"] for r in rosters if r["team_slug"] == "t1"] == ["Faker", "Oner"]


def test_parse_leagues():
    out = parse_leagues({"data": {"leagues": [{"slug": "lck", "name": "LCK", "id": 9}, {"slug": "x"}]}})
    assert out == [{"slug": "lck", "league_id": "9", "name": "LCK", "region": "", "image": "", "priority": 0}]


def test_find_team_disambiguates_duplicate_codes(cat):
    assert cat.find_team("HLE", "HLE Challengers")["slug"] == "hle-challengers"
    assert cat.find_team("HLE", "Hanwha Life Esports")["slug"] == "hanwha-life-esports"
    assert cat.find_team("HLE")["slug"] == "hanwha-life-esports"   # top league preferred
    assert cat.find_team("ZZZ") is None


def test_roster_sorted_by_role(cat):
    assert [p.name for p in cat.roster_for("T1", "T1")] == ["Oner", "Faker"]


def test_search(cat):
    assert cat.search_teams("hle")[0]["code"] == "HLE"
    assert cat.search_teams("") == []
    assert cat.search_players("fak")[0].name == "Faker"
    assert cat.search_players("Sanghyeok")[0].name == "Faker"   # real-name search


def test_db_roundtrip(tmp_path, cat):
    from riftscout import db
    teams, rosters = parse_teams(TEAMS_PAYLOAD)
    db.replace_catalog([{"slug": "lck", "name": "LCK"}], teams, rosters, tmp_path / "c.db")
    loaded = catalog.load_cached(tmp_path / "c.db")
    assert len(loaded.teams) == 3 and loaded.roster_for("T1", "T1")[1].name == "Faker"


# ------------------------------------------------------------------ watchlist
def _m(**kw):
    m = {"team1_code": "T1", "team1_name": "T1", "team2_code": "HLE", "team2_name": "HLE Challengers",
         "league_slug": "lck", "league_name": "LCK"}
    m.update(kw)
    return m


@pytest.fixture
def settings(tmp_path):
    s = SettingsManager(tmp_path / "s.json")
    s.set("followed_leagues", [])
    return s


def test_team_reason(settings, cat):
    settings.toggle_team("T1", "T1")
    r = Watchlist(settings, cat).reasons(_m())
    assert [(x.kind, x.label) for x in r] == [("team", "T1")]


def test_same_code_other_team_not_matched(settings, cat):
    settings.toggle_team("HLE", "Hanwha Life Esports")
    assert not Watchlist(settings, cat).is_followed(_m())


def test_roster_player_is_unconfirmed_until_live(settings, cat):
    settings.toggle_player("Faker")
    wl = Watchlist(settings, cat)
    r = wl.reasons(_m())
    assert len(r) == 1 and r[0].kind == "player" and r[0].confirmed is False and r[0].strong
    live = {"blue": {"players": [{"name": "Faker", "role": "mid"}]}, "red": {"players": []}}
    r = wl.reasons(_m(), live)
    assert len(r) == 1 and r[0].confirmed is True and "starting" in r[0].label


def test_league_reason_is_weak(settings, cat):
    settings.toggle_league("lck")
    wl = Watchlist(settings, cat)
    assert wl.is_followed(_m()) and not wl.is_strong(_m())


def test_tbd_never_matches(settings, cat):
    settings.toggle_team("TBD", "TBD")
    assert not Watchlist(settings, cat).is_followed(_m(team1_code="TBD", team1_name="TBD"))


def test_stream_reasons(settings, cat):
    settings.toggle_team("SKT", "SK Telecom T1")
    wl = Watchlist(settings, cat)
    assert [r.label for r in wl.stream_reasons({"team1": "SKT", "team2": "SSG"})] == ["SKT"]
