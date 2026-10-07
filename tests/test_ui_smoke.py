"""Renders every tab with fixture data (no network) and enforces the spoiler gate:
with spoiler mode on, no score, kill count, gold or game number may appear anywhere."""

import datetime
import tkinter as tk

import pytest

from riftscout import catalog
from riftscout.settings import SettingsManager
from riftscout.stream import normalize_stream_events

UTC = datetime.timezone.utc


def iso(delta_h):
    return (datetime.datetime.now(UTC) + datetime.timedelta(hours=delta_h)).strftime("%Y-%m-%dT%H:%M:%SZ")


LIVE = {
    "match_id": "live1", "league_name": "Worlds", "league_slug": "worlds", "block_name": "Finals",
    "start_time_utc": iso(-2), "state": "inProgress", "best_of": 5, "winner": "", "stream_url": "",
    "team1_id": "10", "team1_name": "T1", "team1_code": "T1", "team1_image": "", "team1_score": 7,
    "team2_id": "20", "team2_name": "Gen.G", "team2_code": "GEN", "team2_image": "", "team2_score": 8,
    "games": [{"number": 4, "id": "g4", "state": "inProgress", "blue_team_id": "20", "red_team_id": "10"}],
}
DONE = dict(LIVE, match_id="done1", state="completed", start_time_utc=iso(-26), winner="GEN", games=[])
SOON = dict(LIVE, match_id="soon1", state="unstarted", start_time_utc=iso(3), team1_score=0, team2_score=0,
            games=[], team1_name="Hanwha Life Esports", team1_code="HLE")
STATS = {"live1": {
    "blue_team_id": "20",
    "blue": {"team_id": "20", "kills": 41, "gold": 61234, "towers": 9, "dragons": ["a"], "barons": 1,
             "inhibitors": 0, "players": [{"name": "Chovy", "champion": "Azir", "role": "mid"}]},
    "red": {"team_id": "10", "kills": 39, "gold": 58000, "towers": 3, "dragons": [], "barons": 0,
            "inhibitors": 0, "players": [{"name": "Faker", "champion": "Orianna", "role": "mid"}]},
}}
STREAM = normalize_stream_events([
    {"id": 1, "utcIso": iso(-0.5), "type": "match", "team1": "SKT", "team2": "SSG", "event": "Worlds",
     "season": "S7", "stage": "Finals"},
    {"id": 2, "utcIso": iso(1), "type": "match", "team1": "FNC", "team2": "G2", "tag": "Banger"},
])
LEAKS = ("7  :  8", "41", "39", "61.2k", "58.0k", "+3.2k", "Game 4")


def texts(w):
    out = []
    try:
        t = w.cget("text")
        if t:
            out.append(str(t))
    except tk.TclError:
        pass
    for c in w.winfo_children():
        out.extend(texts(c))
    return out


@pytest.fixture
def app(tmp_path):
    from riftscout.ui.app import RiftScoutApp
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("no display")
    root.withdraw()
    s = SettingsManager(tmp_path / "s.json")
    s.toggle_team("T1", "T1")
    s.toggle_player("Faker")
    a = RiftScoutApp(root, settings=s, start_worker=False, offline_images=True, db_path=tmp_path / "c.db")
    teams, rosters = catalog.parse_teams({"data": {"teams": [
        {"slug": "t1", "code": "T1", "name": "T1", "status": "active", "homeLeague": {"name": "LCK"},
         "players": [{"summonerName": "Faker", "role": "mid"}]}]}})
    for kind, payload in (("catalog", catalog._build([{"slug": "worlds", "name": "Worlds",
                                                       "region": "INTERNATIONAL", "priority": 0}], teams, rosters)),
                          ("schedule", [DONE, SOON]), ("live", [LIVE]), ("livestats", STATS), ("stream", STREAM),
                          ("status", {"source": "schedule", "ok": True, "detail": "", "at": 0})):
        a._apply(kind, payload)
    yield a
    a.close()


def render_all(app):
    seen = []
    for key, view in app.views.items():
        if key == "schedule":
            for rng in ("upcoming", "today", "results"):
                app.settings.set("schedule_filter_range", rng)
                view.render()
                seen += texts(view)
        elif key == "watchlist":
            for mode in ("teams", "players", "regions", "leagues"):
                view.mode = mode
                view.render()
                seen += texts(view)
        else:
            view.render()
            seen += texts(view)
    app._refresh_header()
    return seen + texts(app.root)


def test_all_tabs_render_with_scores(app):
    all_text = "\n".join(render_all(app))
    assert "7  :  8" in all_text            # sanity: the leak detector can see scores
    assert "Game 4" in all_text and "61.2k" in all_text
    assert "SKT vs SSG" in all_text        # stream now-airing
    assert "★ Faker starting (Mid)" in all_text
    assert "Hanwha Life Esports" in all_text
    assert "RIFTWATCH" in all_text
    assert "Hide to Tray" in all_text


def test_spoiler_mode_leaks_nothing(app):
    app.toggle_spoiler()
    found = [t for t in render_all(app) if any(leak in t for leak in LEAKS)]
    assert found == [], f"spoiler leak: {found}"
    # Revealing a single match shows only that match.
    app.reveal("live1")
    app.views["live"].render()
    assert any("7  :  8" in t for t in texts(app.views["live"]))


def test_onboarding_wizard_and_regions(app):
    from riftscout.ui.wizard import OnboardingWizard
    wiz = OnboardingWizard(app.root, app)
    assert wiz.winfo_exists()
    # Check that presets work
    wiz._preset_recommended()
    assert "KOREA" in wiz.selected_regions
    assert "T1" in wiz.selected_teams
    assert "Faker" in wiz.selected_players
    # Save & close
    wiz._save_and_close()
    assert app.settings.get("onboarding_completed") is True
    assert app.settings.is_region_followed("Korea")
    assert not wiz.winfo_exists()


def test_hide_to_tray_and_restore(app):
    app.hide_to_tray()
    assert app.root.state() == "withdrawn"
    app.show_from_tray()
    assert app.root.state() == "normal"
