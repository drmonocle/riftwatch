"""
Unit and integration tests for the Live Ticker Bar and Watchlist search debounce.
Verifies flicker-free typing, spoiler gating, item rotation, and tab routing.
"""

import datetime
import os
import sys
import tkinter as tk

_sys_tcl = os.path.join(sys.base_prefix, 'tcl')
if os.path.isdir(_sys_tcl):
    os.environ['TCL_LIBRARY'] = os.path.join(_sys_tcl, 'tcl8.6')
    os.environ['TK_LIBRARY'] = os.path.join(_sys_tcl, 'tk8.6')

import pytest

from riftscout import catalog
from riftscout import config as C
from riftscout.settings import SettingsManager
from riftscout.stream import normalize_stream_events
from riftscout.ui.app import RiftScoutApp
from riftscout.ui.ticker import TickerBar, gather_ticker_items

UTC = datetime.timezone.utc


def iso(delta_h: float) -> str:
    return (datetime.datetime.now(UTC) + datetime.timedelta(hours=delta_h)).strftime("%Y-%m-%dT%H:%M:%SZ")


LIVE_MATCH = {
    "match_id": "m_live_1", "league_name": "LCK", "league_slug": "lck", "block_name": "Spring Split",
    "start_time_utc": iso(-1), "state": "inProgress", "best_of": 3, "winner": "", "stream_url": "",
    "team1_id": "100", "team1_name": "T1", "team1_code": "T1", "team1_image": "", "team1_score": 1,
    "team2_id": "200", "team2_name": "Gen.G", "team2_code": "GEN", "team2_image": "", "team2_score": 0,
    "games": [{"number": 2, "id": "g2", "state": "inProgress", "blue_team_id": "100", "red_team_id": "200"}],
}

LIVE_STATS = {"m_live_1": {
    "blue_team_id": "100",
    "blue": {"team_id": "100", "gold": 45000, "kills": 12},
    "red": {"team_id": "200", "gold": 38000, "kills": 5},
}}

UPCOMING_MATCH = {
    "match_id": "m_up_1", "league_name": "LPL", "league_slug": "lpl",
    "start_time_utc": iso(3), "state": "unstarted", "best_of": 3,
    "team1_id": "300", "team1_name": "Bilibili Gaming", "team1_code": "BLG",
    "team2_id": "400", "team2_name": "Top Esports", "team2_code": "TES",
    "team1_score": 0, "team2_score": 0, "games": [],
}

STREAM_EVENTS = normalize_stream_events([
    {"id": 101, "utcIso": iso(-0.5), "type": "match", "team1": "T1", "team2": "WBG", "event": "Worlds",
     "season": "S13", "stage": "Grand Finals"},
])


@pytest.fixture
def ticker_app(tmp_path):
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("no display")
    root.withdraw()

    s = SettingsManager(tmp_path / "settings.json")
    s.toggle_team("T1", "T1")

    app = RiftScoutApp(root, settings=s, start_worker=False, offline_images=True, db_path=tmp_path / "test.db")
    teams, rosters = catalog.parse_teams({"data": {"teams": [
        {"slug": "t1", "code": "T1", "name": "T1", "status": "active", "homeLeague": {"name": "LCK"},
         "players": [{"summonerName": "Faker", "role": "mid"}]},
        {"slug": "geng", "code": "GEN", "name": "Gen.G", "status": "active", "homeLeague": {"name": "LCK"},
         "players": [{"summonerName": "Chovy", "role": "mid"}]},
    ]}})
    app._apply("catalog", catalog._build([{"slug": "lck", "name": "LCK", "region": "KOREA", "priority": 1}], teams, rosters))
    app._apply("schedule", [UPCOMING_MATCH])
    app._apply("live", [LIVE_MATCH])
    app._apply("livestats", LIVE_STATS)
    app._apply("stream", STREAM_EVENTS)
    yield app
    app.close()


def test_watchlist_search_debounce_eliminates_keystroke_flicker(ticker_app):
    """Typing into search entry must NOT alter signature until debounce timer fires or Return is pressed."""
    wv = ticker_app.views["watchlist"]
    sig_initial = wv.signature()
    assert wv.applied_query == ""

    # User types a query into the entry StringVar
    wv.query.set("fak")
    # Immediate signature must be UNCHANGED (prevents _poll from triggering a frame swap)
    assert wv.signature() == sig_initial
    assert wv.applied_query == ""

    # Simulate hitting Enter or debounce timeout
    wv._apply_search()
    assert wv.applied_query == "fak"
    assert wv.signature() != sig_initial

    # Clearing search
    wv._clear_search()
    assert wv.applied_query == ""
    assert wv.query.get() == ""


def test_gather_ticker_items_prioritizes_live_and_displays_gold(ticker_app):
    items = gather_ticker_items(ticker_app)
    assert len(items) >= 2

    # First item must be the live match
    live_item = items[0]
    assert live_item.kind == "live"
    assert live_item.badge == "● LIVE"
    assert "T1 1 : 0 GEN" in live_item.headline
    assert "Game 2" in live_item.details
    assert "T1 +7.0k gold" in live_item.details
    assert live_item.tab_target == "live"


def test_ticker_spoiler_mode_masks_scores_and_gold(ticker_app):
    ticker_app.toggle_spoiler()
    items = gather_ticker_items(ticker_app)

    live_item = next(it for it in items if it.kind == "live")
    assert "1 : 0" not in live_item.headline
    assert "T1 vs GEN" in live_item.headline
    assert "7.0k" not in live_item.details
    assert "Scores hidden" in live_item.details


def test_gather_ticker_items_includes_stream_and_upcoming(ticker_app):
    items = gather_ticker_items(ticker_app)
    kinds = {it.kind for it in items}
    assert "live" in kinds
    assert "stream" in kinds
    assert "upcoming" in kinds

    stream_item = next(it for it in items if it.kind == "stream")
    assert "24/7" in stream_item.badge
    assert "T1 vs WBG" in stream_item.headline
    assert stream_item.tab_target == "stream"

    up_item = next(it for it in items if it.kind == "upcoming")
    assert "UPCOMING" in up_item.badge
    assert "BLG vs TES" in up_item.headline
    assert up_item.tab_target == "schedule"


def test_ticker_bar_cycling_and_visibility(ticker_app):
    tb = ticker_app.ticker_bar
    tb.refresh_data()
    assert len(tb.items) >= 3

    init_idx = tb.index
    tb.next_item()
    assert tb.index == (init_idx + 1) % len(tb.items)
    tb.prev_item()
    assert tb.index == init_idx

    # Toggle visibility
    assert ticker_app.settings.get("show_ticker_bar") is True
    assert tb.winfo_manager() == "pack"
    ticker_app.set_ticker_visible(False)
    assert ticker_app.settings.get("show_ticker_bar") is False
    assert tb.winfo_manager() == ""

    ticker_app.set_ticker_visible(True)
    assert ticker_app.settings.get("show_ticker_bar") is True
    assert tb.winfo_manager() == "pack"


def test_watchlist_inplace_follow_toggle(ticker_app):
    """Clicking follow button must toggle button text, styling, and top chips in-place without triggering full render."""
    ticker_app.show_tab("watchlist")
    wv = ticker_app.views["watchlist"]
    wv.render()

    assert "team:GEN" in wv._row_bindings
    btn, row, _ = wv._row_bindings["team:GEN"]
    assert btn.cget("text") == "☆ Follow"
    assert not ticker_app.settings.is_team_followed("GEN", "Gen.G")

    # Capture signature before toggle
    sig_before = wv.signature()

    # Click the follow button on GEN
    wv._handle_toggle(
        "team", "GEN",
        lambda: ticker_app.toggle_team("GEN", "Gen.G"),
        lambda: ticker_app.settings.is_team_followed("GEN", "Gen.G")
    )

    # 1. State must update
    assert ticker_app.settings.is_team_followed("GEN", "Gen.G")
    # 2. Button text must toggle in-place
    assert btn.cget("text") == "★ Following"
    # 3. Row highlight border must be gold
    assert row.cget("highlightbackground") == C.COLOR_GOLD
    # 4. Rendered cache must match current signature to prevent app._poll from re-rendering
    assert ticker_app.rendered["watchlist"] == wv.signature()
    assert wv.signature() != sig_before

    # Now toggle again to unfollow
    wv._handle_toggle(
        "team", "GEN",
        lambda: ticker_app.toggle_team("GEN", "Gen.G"),
        lambda: ticker_app.settings.is_team_followed("GEN", "Gen.G")
    )
    assert not ticker_app.settings.is_team_followed("GEN", "Gen.G")
    assert btn.cget("text") == "☆ Follow"
    assert row.cget("highlightbackground") == C.COLOR_BORDER


def test_updater_relaunch_script_structure():
    """Verify updater helper uses Shell.Application, Unblock-File, and Copy-Item for reliable desktop relaunch."""
    from riftscout import updater
    ps_path = updater._find_powershell()
    assert ps_path and ("powershell" in ps_path.lower())

    import inspect
    src = inspect.getsource(updater.launch_swap_and_restart)
    assert "Shell.Application" in src
    assert "Unblock-File" in src
    assert "Copy-Item" in src
    assert "SW_SHOWNORMAL" in src

