import json

from riftscout.settings import SettingsManager, migrate


def test_defaults_follow_no_teams(tmp_path):
    s = SettingsManager(tmp_path / "s.json")
    assert s.followed_teams() == []
    assert s.get("followed_players") == []
    assert "lck" in s.get("followed_leagues")


def test_migrate_v1(tmp_path):
    p = tmp_path / "s.json"
    p.write_text(json.dumps({"followed_teams": ["T1", "G2"], "followed_regions": ["lck", "lta"],
                             "followed_players": ["Faker"], "ticker_bar_enabled": True}))
    s = SettingsManager(p)
    assert s.followed_teams() == [{"code": "T1", "name": ""}, {"code": "G2", "name": ""}]
    assert s.get("followed_leagues") == ["lck", "lcs", "cblol-brazil"]
    assert "ticker_bar_enabled" not in s.data
    # Legacy "lck" in followed_regions was converted to league slug; followed_regions has default modern regions
    assert "lck" not in [r.lower() for r in s.followed_regions()]
    assert s.is_region_followed("KOREA")
    assert json.loads(p.read_text())["version"] == 2


def test_migrate_is_idempotent():
    once = migrate({"followed_teams": ["T1"], "followed_regions": ["KOREA"]})
    assert migrate(once) == once


def test_regions_and_tray_settings(tmp_path):
    s = SettingsManager(tmp_path / "s.json")
    assert s.is_region_followed("Korea")
    assert s.toggle_region("Korea") is False
    assert not s.is_region_followed("Korea")
    assert s.toggle_region("Korea") is True
    assert s.is_region_followed("KOREA")
    assert s.get("minimize_to_tray_on_close") is True
    assert isinstance(s.get("onboarding_completed"), bool)


def test_team_follow_code_and_name(tmp_path):
    s = SettingsManager(tmp_path / "s.json")
    assert s.toggle_team("HLE", "Hanwha Life Esports") is True
    assert s.is_team_followed("HLE", "Hanwha Life Esports")
    assert not s.is_team_followed("HLE", "HLE Challengers")      # same code, different team
    assert s.is_team_followed("hle")                              # code-only lookup (stream)
    assert not s.is_team_followed("TBD") and not s.is_team_followed("")
    assert s.toggle_team("HLE", "Hanwha Life Esports") is False
    assert s.followed_teams() == []


def test_legacy_code_only_team_matches_any_name(tmp_path):
    p = tmp_path / "s.json"
    p.write_text(json.dumps({"followed_teams": ["T1"]}))
    s = SettingsManager(p)
    assert s.is_team_followed("T1", "T1")


def test_league_and_player_toggles(tmp_path):
    s = SettingsManager(tmp_path / "s.json")
    s.set("followed_leagues", [])
    assert s.toggle_league("LEC") is True and s.is_league_followed("lec")
    assert s.toggle_league("lec") is False
    assert s.toggle_player("Faker") is True and s.is_player_followed("FAKER")
    assert s.toggle_player("faker") is False and not s.is_player_followed("Faker")


def test_corrupt_file_falls_back(tmp_path):
    p = tmp_path / "s.json"
    p.write_text("{not json")
    s = SettingsManager(p)
    assert s.followed_teams() == []


def test_attach_team_names_resolves_legacy_codes(tmp_path):
    p = tmp_path / "s.json"
    p.write_text(json.dumps({"followed_teams": ["HLE", "T1", "ZZZ"]}))
    s = SettingsManager(p)
    names = {"HLE": "Hanwha Life Esports", "T1": "T1"}
    assert s.attach_team_names(names.get) == 2
    assert s.is_team_followed("HLE", "Hanwha Life Esports")
    assert not s.is_team_followed("HLE", "HLE Challengers")    # no longer matches every HLE
    assert s.followed_teams()[2] == {"code": "ZZZ", "name": ""}  # unknown codes left alone
    assert s.attach_team_names(names.get) == 0
