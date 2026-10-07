"""
Unit tests for RiftScout settings and entity watchlist matching.
"""

from pathlib import Path
from riftscout.settings import SettingsManager


def test_settings_initialization_and_save(tmp_path: Path):
    settings_file = tmp_path / "settings.json"
    sm = SettingsManager(file_path=settings_file)

    assert sm.get("spoiler_mode") is False
    assert "T1" in sm.get("followed_teams")

    # Change a setting and verify persistence
    sm.set("spoiler_mode", True)
    assert settings_file.exists()

    # Reload from disk
    sm2 = SettingsManager(file_path=settings_file)
    assert sm2.get("spoiler_mode") is True


def test_watchlist_toggling(tmp_path: Path):
    settings_file = tmp_path / "settings_toggle.json"
    sm = SettingsManager(file_path=settings_file)

    # Team toggle
    assert sm.is_team_followed("C9") is False
    sm.toggle_team("C9")
    assert sm.is_team_followed("C9") is True
    assert sm.is_team_followed("c9") is True  # Case insensitive
    sm.toggle_team("C9")
    assert sm.is_team_followed("C9") is False

    # Region toggle
    assert sm.is_region_followed("lck") is True
    sm.toggle_region("lck")
    assert sm.is_region_followed("lck") is False
    sm.toggle_region("lck")
    assert sm.is_region_followed("lck") is True

    # Player toggle
    assert sm.is_player_followed("Faker") is True
    assert sm.is_player_followed("Gumayusi") is False
    sm.toggle_player("Gumayusi")
    assert sm.is_player_followed("gumayusi") is True


def test_match_follow_matching(tmp_path: Path):
    settings_file = tmp_path / "settings_match.json"
    sm = SettingsManager(file_path=settings_file)
    # Default followed: T1, GEN, G2, FLY, BLG | lck, lpl, lec, lta, worlds, msi | Faker, Chovy

    # Match featuring followed team
    match1 = {"team1_code": "T1", "team2_code": "KT", "league_slug": "other"}
    assert sm.is_match_followed(match1) is True

    # Match featuring followed region
    match2 = {"team1_code": "BRO", "team2_code": "DRX", "league_slug": "lck"}
    assert sm.is_match_followed(match2) is True

    # Match featuring unfollowed teams and region, but followed starting player
    match3 = {"team1_code": "ABC", "team2_code": "XYZ", "league_slug": "unknown"}
    assert sm.is_match_followed(match3, roster_players={"Zeus", "Oner", "Faker"}) is True

    # Completely unfollowed match
    match4 = {"team1_code": "ABC", "team2_code": "XYZ", "league_slug": "unknown"}
    assert sm.is_match_followed(match4, roster_players={"PlayerA", "PlayerB"}) is False
